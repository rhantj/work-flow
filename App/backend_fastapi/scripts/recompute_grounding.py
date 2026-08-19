#!/usr/bin/env python3
"""검색을 다시 돌려 근거 점수를 재계산한다. 생성도 캐시 변경도 하지 않는다.

## 왜 이 스크립트가 있는가

`output/assistant_eval/RESULT.md` 의 채점기 정정은 **노트북을 다시 돌리지 않고** 표의
`grounding` 값을 고쳤다. 그 근거가 "검색은 결정적이라 재실행 없이 같은 결과가 나온다"
인데, 그 주장을 사람이 임시 스크립트로 한 번 확인하고 지워버리면 다음 사람은 확인할
길이 없다. 주장만 남고 확인 수단이 없는 상태가 된다.

그래서 그 재계산을 저장소에 남긴다. 두 가지를 한 번에 답한다.

1. **재현되는가** - id 전용 채점으로 다시 계산했을 때 RESULT.md 표의 값이 나오는가.
   나오지 않으면 검색이 결정적이라는 전제가 깨진 것이고, 정정 자체를 다시 봐야 한다.
2. **본문 대조가 얼마나 더 잡는가** - 두 방식의 차이. 이 값이 커지면 화이트리스트가
   검색 품질을 가리고 있다는 뜻이다.

## 왜 CI 테스트가 아닌가

살아 있는 DB(프로젝트 1)와 임베딩 모델이 필요하다. CI 에는 둘 다 없다. 픽스처만으로
검증할 수 있는 채점기 규칙 자체는 `tests/assistant_eval/test_scorer.py` 가 덮는다.
여기서만 답할 수 있는 것은 "실제 코퍼스에서 얼마나 차이 나는가"다.

## 쓰는 법

    python scripts/recompute_grounding.py

`--project-id` 로 프로젝트를 바꿀 수 있다. 검색만 하므로 운영에 부작용이 없다 -
베이스라인 노트북과 달리 캐시 epoch 를 건드리지 않는다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# 컨테이너 안에서는 환경변수가 이미 있고, 로컬에서는 없다. 베이스라인 노트북과 같은
# 규약으로 .env 를 찾는다 - 같은 것을 재는 두 도구가 서로 다른 방법으로 설정을 읽으면
# 한쪽만 도는 이유를 매번 다시 알아내야 한다.
_ENV_FILE = os.getenv("ASSISTANT_EVAL_ENV_FILE") or str(REPO_ROOT.parents[0] / ".env")
if Path(_ENV_FILE).is_file():
    from dotenv import load_dotenv

    load_dotenv(_ENV_FILE)

from core.db import get_pool_instance  # noqa: E402
from llm_rag_assistant.app.services.embedding_service import embed_text  # noqa: E402
from llm_rag_assistant.app.services.retrieval_service import (  # noqa: E402
    search_chunks_for_question,
)
from tests.assistant_eval.scorer import score_grounding  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "assistant_eval"

# 응답에 실리는 본문은 여기서 잘린다(chat_service._SNIPPET_MAX_LEN). 노트북이 채점기에
# 넘기는 것도 잘린 값이므로, 여기서 전체 본문을 쓰면 노트북보다 후하게 재게 된다.
SNIPPET_MAX_LEN = 200


def _shorten(value: str, max_len: int = SNIPPET_MAX_LEN) -> str:
    return value if len(value) <= max_len else value[: max_len - 1] + "…"


async def main(project_id: int) -> int:
    pool = await get_pool_instance()
    by_category: dict[str, list[tuple[float, float]]] = {}
    changed: list[tuple[str, float, float, tuple[str, ...]]] = []

    for path in sorted(FIXTURES.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        embedding = await embed_text(raw["question"])
        rows = await search_chunks_for_question(
            pool, project_id, raw["question"], embedding, top_k=5
        )
        ids = [f"{row['source_type']}#{row['source_id']}" for row in rows]
        contents = {
            f"{row['source_type']}#{row['source_id']}": _shorten(row["content"]) for row in rows
        }

        id_only = score_grounding(raw, ids)
        with_content = score_grounding(raw, ids, retrieved_contents=contents)
        by_category.setdefault(raw["category"], []).append((id_only.score, with_content.score))
        if with_content.score != id_only.score:
            changed.append(
                (raw["case_id"], id_only.score, with_content.score, with_content.content_only_fact_ids)
            )

    print(f"{'분류':<12}{'id 전용':>10}{'본문 포함':>12}{'차이':>10}")
    old_all: list[float] = []
    new_all: list[float] = []
    for category, pairs in sorted(by_category.items()):
        old = sum(p[0] for p in pairs) / len(pairs)
        new = sum(p[1] for p in pairs) / len(pairs)
        old_all += [p[0] for p in pairs]
        new_all += [p[1] for p in pairs]
        print(f"{category:<12}{old:>10.3f}{new:>12.3f}{new - old:>+10.3f}")
    old = sum(old_all) / len(old_all)
    new = sum(new_all) / len(new_all)
    print(f"{'전체':<12}{old:>10.3f}{new:>12.3f}{new - old:>+10.3f}")

    print(f"\n점수가 달라진 케이스 {len(changed)}건")
    for case_id, before, after, facts in changed:
        print(f"  {case_id:<14} {before:.2f} -> {after:.2f}   본문으로만 잡힌 사실 {list(facts)}")

    # RESULT.md 가 기록한 id 전용 값. 어긋나면 "검색이 결정적"이라는 정정의 전제가 깨진 것이다.
    recorded = 0.783
    if abs(old - recorded) >= 0.001:
        print(f"\n[경고] id 전용 전체가 {old:.3f} 로 RESULT.md 의 {recorded} 와 다르다.")
        print("       검색 결과가 달라졌다는 뜻이므로 RESULT.md 의 채점기 정정을 다시 확인한다.")
        return 1
    print(f"\n[OK] id 전용 전체 {old:.3f} 로 RESULT.md 기록과 일치한다.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", type=int, default=1)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.project_id)))
