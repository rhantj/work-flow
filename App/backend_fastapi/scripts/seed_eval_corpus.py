"""평가 코퍼스 스냅샷을 로컬 Postgres(pgvector)에 적재한다.

임베딩은 저장하지 않고 여기서 다시 만든다. 임베딩 모델이 리비전 고정된 로컬
SentenceTransformer 라 같은 본문에서 같은 벡터가 나오기 때문이다. 벡터를 굳혀두면
스냅샷이 3.4MB 가 되는데, 본문만 두면 119kB 다. 재현성은 recompute_grounding.py 가
검증한다.

사용법:
    docker run -d --name workflow-eval-db -p 55432:5432 \\
      -e POSTGRES_PASSWORD=eval -e POSTGRES_DB=eval pgvector/pgvector:pg17
    EVAL_DATABASE_URL=postgres://postgres:eval@localhost:55432/eval \\
      python scripts/seed_eval_corpus.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

CORPUS = REPO_ROOT / "tests" / "fixtures" / "assistant_eval" / "corpus"
PROJECT_ID = 1
EMBEDDING_DIM = 1024

# 값싼 1차 방어일 뿐이다. 이 팀은 운영 OCI Postgres 에 SSH 터널(-L <port>:localhost:5432)로
# 붙으므로 운영 DB 도 종단은 문자 그대로 localhost 다. 호스트명으로는 "버려도 되는 DB인가"를
# 판별할 수 없어서, 실질 방어선은 아래 _assert_disposable 의 마커 검사다.
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

# 이 스크립트가 만든 DB 라는 표식. 테이블을 DROP 하기 전에 이것부터 본다.
_MARKER_TABLE = "eval_corpus_marker"

_SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS document_chunks, meeting_action_items, meetings, tasks, users, projects,
    {_MARKER_TABLE} CASCADE;

CREATE TABLE projects (id BIGINT PRIMARY KEY, title TEXT);
CREATE TABLE users (id BIGINT PRIMARY KEY, name TEXT);
CREATE TABLE tasks (
    id BIGINT PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT, description TEXT, status TEXT, priority TEXT,
    assignee_id BIGINT REFERENCES users(id), due_date DATE
);
CREATE TABLE meetings (
    id BIGINT PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE
);
CREATE TABLE meeting_action_items (
    id BIGINT PRIMARY KEY,
    meeting_id BIGINT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    due_date DATE, priority TEXT,
    final_assignee_id BIGINT REFERENCES users(id)
);
CREATE TABLE {_MARKER_TABLE} (seeded_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE document_chunks (
    id BIGINT PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_type VARCHAR(32) NOT NULL,
    source_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR({EMBEDDING_DIM}) NOT NULL,
    assignee_id BIGINT REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


def _read_jsonl(name: str) -> list[dict]:
    path = CORPUS / name
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _as_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _require_local(url: str) -> None:
    host = urlparse(url).hostname
    if host not in _LOCAL_HOSTS:
        raise SystemExit(
            f"거부: EVAL_DATABASE_URL 호스트가 '{host}' 입니다. 이 스크립트는 테이블을 "
            f"DROP 후 재생성하므로 로컬 평가용 DB({', '.join(sorted(_LOCAL_HOSTS))})만 허용합니다."
        )


async def _assert_disposable(conn) -> None:
    """이 DB 를 통째로 비워도 되는지 확인한다.

    호스트명 검사는 SSH 터널을 구분하지 못한다. 그래서 대상 DB 자체에 물어본다 -
    비어 있거나(첫 시딩), 이전에 이 스크립트가 만든 마커가 있을 때만 허용한다.
    운영 DB 는 마커가 없고 테이블은 많으므로 여기서 걸린다.
    """
    marker = await conn.fetchval(f"SELECT to_regclass('public.{_MARKER_TABLE}')")
    if marker is not None:
        return
    tables = await conn.fetchval(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
    )
    if tables:
        raise SystemExit(
            f"거부: 이 DB 의 public 스키마에 테이블이 {tables}개 있는데 평가용 마커"
            f"('{_MARKER_TABLE}')가 없습니다. SSH 터널 너머의 운영 DB 일 수 있습니다. "
            f"빈 DB 를 쓰세요."
        )


async def main() -> int:
    url = os.getenv("EVAL_DATABASE_URL")
    if not url:
        raise SystemExit("EVAL_DATABASE_URL 이 필요합니다. 모듈 docstring 의 사용법을 보세요.")
    _require_local(url)

    # 임베딩 모델이 비공개 저장소라 HF_TOKEN 이 필요하다. 베이스라인 노트북·재계산
    # 스크립트와 같은 규약으로 .env 를 찾는다. DATABASE_URL 은 그 뒤에 평가 DB 로 덮어써야
    # get_settings() 가 동결 Supabase 를 가리킨 채로 뜨지 않는다.
    env_file = os.getenv("ASSISTANT_EVAL_ENV_FILE") or str(REPO_ROOT.parents[0] / ".env")
    if Path(env_file).is_file():
        from dotenv import load_dotenv

        load_dotenv(env_file)
    os.environ["DATABASE_URL"] = url

    import asyncpg

    from llm_rag_assistant.app.services.embedding_service import embed_text

    chunks = _read_jsonl("chunks.jsonl")
    tasks = _read_jsonl("tasks.jsonl")
    meetings = _read_jsonl("meetings.jsonl")
    items = _read_jsonl("action_items.jsonl")
    # transcript_only 는 계정이 없어 users 행이 없다. 본문 별칭으로만 존재한다.
    people = json.loads((CORPUS / "people.json").read_text(encoding="utf-8"))["users"]

    # 임베딩을 먼저 만든다. 비공개 HF 저장소라 토큰이 만료되면 모델 로딩이 401 로 죽는데,
    # DROP 뒤에 죽으면 DB 는 비워진 채로 남는다(트랜잭션이 아니라 되돌려지지도 않는다).
    # 느리고 실패할 수 있는 일을 먼저, 되돌릴 수 없는 일을 나중에.
    print(f"임베딩 재생성 {len(chunks)}건...", flush=True)
    rows = []
    for n, ch in enumerate(chunks, 1):
        vector = await embed_text(ch["content"])
        if len(vector) != EMBEDDING_DIM:
            raise SystemExit(
                f"임베딩 차원이 {len(vector)} 입니다. 스냅샷은 {EMBEDDING_DIM} 차원 기준이라 "
                f"모델이 바뀌면 스키마부터 맞춰야 합니다."
            )
        rows.append((ch["id"], PROJECT_ID, ch["source_type"], ch["source_id"],
                     ch["content"], "[" + ",".join(map(repr, vector)) + "]", ch["assignee_id"]))
        if n % 50 == 0:
            print(f"  {n}/{len(chunks)}", flush=True)

    conn = await asyncpg.connect(url)
    try:
        # 검사는 public 을 명시하는데 DROP 은 스키마를 안 적어 search_path 로 풀린다.
        # 둘이 다른 곳을 가리키면 텅 빈 public 을 보고 통과시킨 뒤 데이터가 있는 스키마를 친다.
        await conn.execute("SET search_path = public")
        await _assert_disposable(conn)
        await conn.execute(_SCHEMA)
        await conn.execute("INSERT INTO projects (id, title) VALUES ($1, $2)", PROJECT_ID, "평가 코퍼스")
        await conn.executemany(
            "INSERT INTO users (id, name) VALUES ($1, $2)",
            [(int(uid), name) for uid, name in people.items()],
        )
        await conn.executemany(
            """INSERT INTO tasks (id, project_id, title, description, status, priority, assignee_id, due_date)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            [
                (t["id"], PROJECT_ID, t["title"], t["description"], t["status"],
                 t["priority"], t["assignee_id"], _as_date(t["due_date"]))
                for t in tasks
            ],
        )
        await conn.executemany(
            "INSERT INTO meetings (id, project_id) VALUES ($1, $2)",
            [(m["id"], PROJECT_ID) for m in meetings],
        )
        await conn.executemany(
            """INSERT INTO meeting_action_items (id, meeting_id, due_date, priority, final_assignee_id)
               VALUES ($1, $2, $3, $4, $5)""",
            [
                (i["id"], i["meeting_id"], _as_date(i["due_date"]), i["priority"], i["final_assignee_id"])
                for i in items
            ],
        )

        await conn.executemany(
            """INSERT INTO document_chunks (id, project_id, source_type, source_id, content, embedding, assignee_id)
               VALUES ($1, $2, $3, $4, $5, $6::vector, $7)""",
            rows,
        )
    finally:
        await conn.close()

    print(
        f"완료 - 청크 {len(chunks)} / 업무 {len(tasks)} / 회의 {len(meetings)} / "
        f"액션 {len(items)} / 인원 {len(people)}"
    )
    print("검증: DATABASE_URL 을 같은 값으로 두고 scripts/recompute_grounding.py 를 돌리세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
