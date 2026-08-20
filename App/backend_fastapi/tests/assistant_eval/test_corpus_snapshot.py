"""평가 코퍼스 스냅샷이 원본과 어긋나거나 실명을 흘리지 않는지 지킨다.

스냅샷의 출처(동결 Supabase)는 삭제 예정이라, 한 번 어긋나면 원본과 대조할 방법이 없다.
그래서 재추출이 조용히 망가지지 않도록 여기서 못을 박는다.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "assistant_eval" / "corpus"
CASE_FIXTURES = CORPUS.parent
# 코퍼스·케이스 픽스처·검색 평가셋 셋 다 같은 인물을 나눠 들고 있다. 한 곳만 지키면
# 나머지에서 실명이 살아남는다(2026-08-20 에 실제로 mixed-05 에서 그렇게 빠져나갔다).
RETRIEVAL_EVALSET = (
    Path(__file__).resolve().parents[4] / "output" / "hybrid_rag_eval" / "data" / "evalset.json"
)

# 2026-08-20 동결 Supabase 프로젝트 1 실측치. 재추출 결과가 여기서 벗어나면 원본이 바뀌었거나
# 추출 쿼리가 바뀐 것이므로, 숫자를 고치기 전에 어느 쪽인지부터 밝혀야 한다.
EXPECTED_ROWS = {"chunks": 308, "tasks": 166, "meetings": 17, "action_items": 66}

# 청크가 가리키는 source_id 중 원본에도 대응 행이 없는 건수. 청크 생성 후 원본 행이 지워졌거나
# 다른 프로젝트 회의에 속해 어시스턴트 쿼리(project_id 로 범위를 좁힌다)에 안 잡히는 것들이다.
# 원본에서도 같은 수라 스냅샷 결함이 아니다. 이 수가 변하면 추출 범위가 달라진 것이다.
EXPECTED_DANGLING = {"task": 18, "action_item": 57, "meeting": 9}

# 화자 표기(`이름:`)와 참석자 목록에 나올 수 있는, 사람 이름이 아닌 낱말들.
# 여기 없는 한글 토큰이 그 자리에 나오면 마스킹이 빠진 실명일 가능성이 높다.
SPEAKER_SLOT_VOCABULARY = frozenset(
    {"근거", "목적", "시나리오", "기능", "결정사항", "위험요소", "제목", "일자", "유형", "참석자", "위험"}
)

# 마스킹 대상이던 실명 21개의 해시.
#
# 이것은 **비밀이 아니다.** 소금이 바로 아래 평문으로 있고 평문 공간은 2~3자 한글 이름이라
# 전수 대입이 몇 분이면 끝난다. 실명을 감추는 장치로 오해하지 말 것. 이름을 목록으로
# 나열하지 않았을 뿐이고, 같은 이름들은 이미 레포 곳곳과 git 히스토리에 평문으로 있다.
# 여기서 해시를 쓰는 이유는 하나다 - 이 파일을 읽는 사람 눈에 실명 목록이 바로 들어오지
# 않게 하는 것. 그 이상을 기대하면 안 된다.
#
# 화자·담당 패턴으로는 못 잡는다. 2026-08-20 에 빠져나간 것은 `담당을 박상준으로` 였는데
# 이름이 `담당` 뒤에 와서 두 패턴 어디에도 안 걸렸다. 그래서 위치를 보지 않고 본문 전체의
# 한글 토막을 훑는다.
_NAME_SALT = "workflow-eval-corpus"
# 아래 집합에 4자 이상 이름의 해시를 더하면 이 길이도 같이 늘려야 한다. 안 그러면 스캐너가
# 그 길이의 토막을 아예 만들지 않아 조용히 검사에서 빠진다.
_NAME_LENGTHS = (2, 3)
_MASKED_NAME_DIGESTS = frozenset({
    "0caf46d9cc98b270", "21d04170e1d5e683", "6628a5b7ec7dbc2d", "67f9f12ef2bc840b",
    "7996afcdbb255f45", "7db2409daea2f22c", "7dfc8160a34b4e6a", "8428808ad5ef33d1",
    "92f68284bc72edae", "ac8eb1c5d8d2bf10", "b336e8c7f08598af", "c1b33cc7f9801f97",
    "c305ab6f5363a4e2", "ca58aa8badd9e4c0", "d5fd402f53904123", "d8f273e313f43f23",
    "d91e5e55aa129107", "d9554fbbef4b182c", "ea1a7a442026fb19", "ee83264f4b686b84",
    "f41370c68bf47384",
})
_HANGUL_RUN = re.compile(r"[가-힣]+")

_ALIAS = re.compile(r"^구성원[A-Z]$")
# 별칭(`구성원A:`)도 잡아야 한다. 한글만 잡으면 화자 자리에 오는 별칭이 아예 안 걸려서
# 아래 _ALIAS 검사가 한 번도 실행되지 않는 죽은 가지가 된다.
_SPEAKER_SLOT = re.compile(r"(?:^|[\s,\[])([가-힣]{2,4}[A-Z]?)\s*:")
_ATTENDEE_LINE = re.compile(r"참석자:\s*([^\[\]\n]+)")


def _load(name: str) -> list[dict]:
    with open(CORPUS / f"{name}.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def corpus() -> dict:
    people = json.loads((CORPUS / "people.json").read_text(encoding="utf-8"))
    return {
        "chunks": _load("chunks"),
        "tasks": _load("tasks"),
        "meetings": _load("meetings"),
        "action_items": _load("action_items"),
        "people": people,
    }


def _all_text(corpus: dict) -> str:
    parts = [c["content"] for c in corpus["chunks"]]
    parts += [f"{t['title'] or ''} {t['description'] or ''}" for t in corpus["tasks"]]
    return "\n".join(parts)


@pytest.mark.parametrize("name", sorted(EXPECTED_ROWS))
def test_snapshot_row_counts_match_the_origin(corpus, name):
    assert len(corpus[name]) == EXPECTED_ROWS[name]


def test_person_slots_contain_only_aliases_or_known_words(corpus):
    """화자·참석자 자리에 별칭도 낱말도 아닌 한글이 있으면 마스킹이 빠진 것이다."""
    text = _all_text(corpus)
    found = set(_SPEAKER_SLOT.findall(text))
    for line in _ATTENDEE_LINE.findall(text):
        found.update(
            tok for tok in re.split(r"[,\s]+", line.strip()) if re.fullmatch(r"[가-힣]{2,4}", tok)
        )
    leaked = {tok for tok in found if not _ALIAS.match(tok) and tok not in SPEAKER_SLOT_VOCABULARY}
    assert not leaked, (
        f"화자/참석자 자리에 별칭이 아닌 한글 토큰이 있다: {sorted(leaked)}. "
        f"실명이면 추출기의 EXTRA_NAMES 에 넣고 다시 뜨고, 일반 낱말이면 "
        f"SPEAKER_SLOT_VOCABULARY 에 넣는다."
    )


def _digest(token: str) -> str:
    return hashlib.sha256((_NAME_SALT + token).encode("utf-8")).hexdigest()[:16]


def _masked_names_in(text: str) -> list[tuple[int, str]]:
    """(오프셋, 걸린 토큰) 목록. 어디서 걸렸는지 알아야 고칠 수 있다."""
    hits = []
    for run in _HANGUL_RUN.finditer(text):
        chunk = run.group()
        for size in _NAME_LENGTHS:
            for i in range(len(chunk) - size + 1):
                token = chunk[i : i + size]
                if _digest(token) in _MASKED_NAME_DIGESTS:
                    hits.append((run.start() + i, token))
    return hits


def _sources(label: str) -> list[Path]:
    if label == "corpus":
        return sorted(CORPUS.glob("*.jsonl")) + [CORPUS / "people.json", CORPUS / "README.md"]
    if label == "case_fixtures":
        return sorted(CASE_FIXTURES.glob("*.json"))
    return [RETRIEVAL_EVALSET]


@pytest.mark.parametrize(
    "label",
    ["corpus", "case_fixtures", "retrieval_evalset"],
)
def test_no_masked_person_name_survives_anywhere(label):
    """치환했어야 할 실명이 어느 파일에도 남아 있으면 안 된다.

    코퍼스·케이스 픽스처·검색 평가셋은 같은 인물을 나눠 들고 있다. 한 곳만 지키면 나머지에서
    살아남는다 - 실제로 코퍼스만 검사하던 동안 mixed-05 의 `reason` 에 실명이 남아 있었다.
    문서도 본다. 그때 빠져나간 두 곳 중 하나가 코퍼스 README 였다.
    """
    leaked = [
        f"{path.name}:{offset} ({token[0]}{'*' * (len(token) - 1)})"
        for path in _sources(label)
        for offset, token in _masked_names_in(path.read_text(encoding="utf-8"))
    ]
    assert not leaked, (
        f"{label} 에 치환되지 않은 실명 {len(leaked)}건: {', '.join(leaked)}. "
        f"사람 이름이면 별칭으로 바꾸고, 사람 이름이 아닌데 걸렸다면 그 낱말이 "
        f"_MASKED_NAME_DIGESTS 의 이름과 겹치는 것이므로 표현을 바꾼다."
    )


def test_every_referenced_assignee_has_an_alias(corpus):
    known = {int(k) for k in corpus["people"]["users"]}
    referenced = (
        {c["assignee_id"] for c in corpus["chunks"]}
        | {t["assignee_id"] for t in corpus["tasks"]}
        | {a["final_assignee_id"] for a in corpus["action_items"]}
    )
    assert referenced - {None} <= known


def test_aliases_are_unique_and_well_formed(corpus):
    users = corpus["people"]["users"]
    transcript_only = corpus["people"]["transcript_only"]
    every = list(users.values()) + list(transcript_only)
    assert all(_ALIAS.match(a) for a in every), "별칭 형식이 아닌 값이 있다 - 실명이 남았을 수 있다"
    assert len(set(every)) == len(every), "별칭이 중복되면 서로 다른 사람이 한 사람으로 보인다"


def test_action_items_stay_inside_the_snapshot_meetings(corpus):
    meeting_ids = {m["id"] for m in corpus["meetings"]}
    assert all(a["meeting_id"] in meeting_ids for a in corpus["action_items"])


def test_dangling_source_ids_match_the_origin(corpus):
    ids = {
        "task": {t["id"] for t in corpus["tasks"]},
        "action_item": {a["id"] for a in corpus["action_items"]},
        "meeting": {m["id"] for m in corpus["meetings"]},
    }
    actual = {
        source_type: sum(
            1
            for c in corpus["chunks"]
            if c["source_type"] == source_type and c["source_id"] not in known
        )
        for source_type, known in ids.items()
    }
    assert actual == EXPECTED_DANGLING
