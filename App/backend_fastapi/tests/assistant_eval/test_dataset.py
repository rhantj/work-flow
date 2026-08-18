"""어시스턴트 답변 평가셋의 스키마와 불변조건.

검색 평가(`output/hybrid_rag_eval`)는 어느 청크가 올라왔는지까지만 잰다. 그 뒤 생성된
답이 맞는지는 아직 아무도 재지 않는다. 이 픽스처가 그 채점의 정답지다.

케이스 파일 하나의 형태:

    {
      "case_id": "mixed-01",                  # 파일 이름과 같다
      "category": "mixed",                    # identifier | semantic | mixed
      "retrieval_case_id": "C01",             # 검색 평가셋 evalset.json 의 id
      "question": "결제 API는 언제까지 하기로 했어?",
      "must_include_facts": [                 # 사실 충실도 축
        {"fact_id": "F1", "statement": "...", "evidence_snippet": "..."}
      ],
      "expected_source_ids": ["meeting#1"],   # 근거 인용 축, "{source_type}#{source_id}"
      "expected_source_excerpts": {"meeting#1": "..."},
      "must_not_claim": [                     # 환각 축
        {"claim_id": "N1", "statement": "...", "reason": "..."}
      ]
    }

`expected_source_ids` 가 청크 id 가 아니라 `source_type#source_id` 인 이유는 검색 결과와
프롬프트의 출처 줄이 그 조합으로만 식별되기 때문이다(`generation_service` 의 `[출처 N -
task#62]`). 청크 id 는 답변 어디에도 나타나지 않아 채점에 쓸 수 없다. 대신 검색 평가셋과의
연결은 `retrieval_case_id` 로 유지한다.

`expected_source_ids` 는 정답이 근거로 삼을 수 있는 출처의 화이트리스트다. 좋은 답은 이
중 최소 하나를 인용해야 하고, 여기 없는 출처만으로 답하면 근거 인용 실패로 본다. 전부를
인용해야 하는 것은 아니다 - 같은 내용의 청크가 여러 벌 적재돼 있어 어느 벌이 올라올지는
검색이 정한다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "assistant_eval"

CATEGORIES = frozenset({"identifier", "semantic", "mixed"})
TOP_LEVEL_KEYS = frozenset({
    "case_id",
    "category",
    "retrieval_case_id",
    "question",
    "must_include_facts",
    "expected_source_ids",
    "expected_source_excerpts",
    "must_not_claim",
})
SOURCE_ID_PATTERN = re.compile(r"^(task|meeting|action_item)#\d+$")
RETRIEVAL_ID_PATTERN = re.compile(r"^[ABC]\d{2}$")
RETRIEVAL_ID_PREFIX = {"identifier": "A", "semantic": "B", "mixed": "C"}
MINIMUM_PER_CATEGORY = 5


def load_raw_cases() -> List[Dict]:
    paths = sorted(FIXTURES.glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def squeeze(text: str) -> str:
    return "".join(text.split())


def test_fixture_directory_has_cases():
    assert load_raw_cases(), f"{FIXTURES} 에 케이스 파일이 없다"


def test_case_id_matches_file_name_and_is_unique():
    """파일 이름과 case_id 가 어긋나면 채점 보고서에서 케이스를 되짚지 못한다."""
    case_ids = []
    for path in sorted(FIXTURES.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert raw["case_id"] == path.stem, path.name
        case_ids.append(raw["case_id"])

    assert len(case_ids) == len(set(case_ids)), case_ids


def test_every_case_has_exactly_the_schema_keys():
    """키를 하나 빠뜨리거나 오타를 내면 채점기가 그 축을 조용히 건너뛴다."""
    for raw in load_raw_cases():
        assert set(raw) == TOP_LEVEL_KEYS, raw.get("case_id")


def test_category_is_one_of_the_three_kinds():
    for raw in load_raw_cases():
        assert raw["category"] in CATEGORIES, raw["case_id"]


def test_each_category_has_at_least_five_cases():
    counts: Dict[str, int] = {name: 0 for name in CATEGORIES}
    for raw in load_raw_cases():
        counts[raw["category"]] += 1

    for name, count in counts.items():
        assert count >= MINIMUM_PER_CATEGORY, (name, counts)


def test_questions_are_non_empty_and_distinct():
    """같은 질문이 두 번 들어가면 그 유형만 점수에 두 배로 반영된다."""
    questions = []
    for raw in load_raw_cases():
        assert raw["question"].strip(), raw["case_id"]
        questions.append(raw["question"])

    assert len(questions) == len(set(questions)), questions


def test_retrieval_case_ids_are_well_formed_and_distinct():
    """검색 평가셋과 답변 평가셋을 나란히 놓으려면 연결 키가 1:1 이어야 한다."""
    retrieval_ids = []
    for raw in load_raw_cases():
        retrieval_id = raw["retrieval_case_id"]
        assert RETRIEVAL_ID_PATTERN.match(retrieval_id), (raw["case_id"], retrieval_id)
        retrieval_ids.append(retrieval_id)

    assert len(retrieval_ids) == len(set(retrieval_ids)), retrieval_ids


def test_retrieval_case_id_prefix_matches_the_category():
    """케이스를 복사해 만들 때 연결 키만 그대로 두면 분류별 점수가 엉뚱한 질문을 가리킨다."""
    for raw in load_raw_cases():
        expected = RETRIEVAL_ID_PREFIX[raw["category"]]
        assert raw["retrieval_case_id"].startswith(expected), (
            raw["case_id"],
            raw["retrieval_case_id"],
        )


def test_expected_source_ids_are_non_empty_unique_and_well_formed():
    for raw in load_raw_cases():
        source_ids = raw["expected_source_ids"]
        assert source_ids, raw["case_id"]
        assert len(source_ids) == len(set(source_ids)), (raw["case_id"], source_ids)
        for source_id in source_ids:
            assert SOURCE_ID_PATTERN.match(source_id), (raw["case_id"], source_id)


def test_every_expected_source_carries_an_excerpt():
    """발췌가 없으면 인용이 맞는지 사람도 채점기도 확인할 방법이 없다."""
    for raw in load_raw_cases():
        excerpts = raw["expected_source_excerpts"]
        assert set(excerpts) == set(raw["expected_source_ids"]), raw["case_id"]
        for source_id, excerpt in excerpts.items():
            assert excerpt.strip(), (raw["case_id"], source_id)


def test_facts_are_non_empty_with_unique_ids():
    for raw in load_raw_cases():
        facts = raw["must_include_facts"]
        assert facts, raw["case_id"]
        for fact in facts:
            assert set(fact) == {"fact_id", "statement", "evidence_snippet"}, raw["case_id"]
            assert fact["statement"].strip(), (raw["case_id"], fact["fact_id"])
        fact_ids = [fact["fact_id"] for fact in facts]
        assert len(fact_ids) == len(set(fact_ids)), (raw["case_id"], fact_ids)


def test_fact_statements_are_distinct_within_a_case():
    """같은 사실을 두 번 적으면 그 케이스 하나가 사실 충실도를 왜곡한다."""
    for raw in load_raw_cases():
        statements = [fact["statement"] for fact in raw["must_include_facts"]]
        assert len(statements) == len(set(statements)), raw["case_id"]


def test_every_fact_snippet_appears_in_an_expected_source_excerpt():
    """정답을 손으로 쓰다 보면 근거에 없는 문장을 적기 쉽다. 여기서 막는다.

    발췌를 이어 붙여 한 번에 찾으면 두 출처의 경계에 걸친 문자열도 통과한다. 어느 출처에도
    없는 문장이 근거로 인정되므로 발췌 하나하나와 대조한다.
    """
    for raw in load_raw_cases():
        haystacks = [squeeze(text) for text in raw["expected_source_excerpts"].values()]
        for fact in raw["must_include_facts"]:
            snippet = squeeze(fact["evidence_snippet"])
            assert snippet, (raw["case_id"], fact["fact_id"])
            assert any(snippet in haystack for haystack in haystacks), (
                f"{raw['case_id']}/{fact['fact_id']}: {snippet}"
            )


def test_forbidden_claims_are_non_empty_with_reasons():
    """환각 축은 '무엇을 지어내면 안 되는가'가 있어야 잴 수 있다."""
    for raw in load_raw_cases():
        claims = raw["must_not_claim"]
        assert claims, raw["case_id"]
        for claim in claims:
            assert set(claim) == {"claim_id", "statement", "reason"}, raw["case_id"]
            assert claim["statement"].strip(), (raw["case_id"], claim["claim_id"])
            assert claim["reason"].strip(), (raw["case_id"], claim["claim_id"])
        claim_ids = [claim["claim_id"] for claim in claims]
        assert len(claim_ids) == len(set(claim_ids)), (raw["case_id"], claim_ids)


def test_cases_are_sorted_by_case_id():
    case_ids = [raw["case_id"] for raw in load_raw_cases()]

    assert case_ids == sorted(case_ids)
