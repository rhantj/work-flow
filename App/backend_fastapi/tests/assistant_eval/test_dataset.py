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

출처 식별자
-----------
`expected_source_ids` 가 청크 id 가 아니라 `source_type#source_id` 인 이유는 검색 결과와
프롬프트의 출처 줄이 그 조합으로만 식별되기 때문이다(`generation_service` 의 `[출처 N -
task#62]`). 청크 id 는 답변 어디에도 나타나지 않아 채점에 쓸 수 없다.

근거 인용을 어떻게 채점하는가 (설계 결정)
------------------------------------------
`expected_source_ids` 는 "근거로 삼아도 되는 출처의 화이트리스트"다. 여기 없는 출처만으로
답하면 근거 인용 실패로 본다. 반대로 전부 인용할 것은 요구하지 않는다 - 같은 내용이 여러
벌 적재돼 있어(mixed-02 의 `action_item#452` 와 `#488` 은 발췌가 글자까지 같다) 어느 벌이
검색에 올라올지를 정답지가 고정할 수 없기 때문이다.

이 느슨함에는 대가가 있다. 한 케이스의 사실이 여러 출처에 흩어져 있을 때, 답이 그중 출처
하나만 인용해도 "화이트리스트 안"이라는 이유로 인용 축을 통과한다. 나머지 사실은 근거 없이
말한 셈인데 답변 단위 인용 검사로는 그걸 못 잡는다.

그래서 채점 단위를 답변이 아니라 **사실 하나**로 잡는다. 후속 채점기(#624)는 사실마다
`fact_evidence_sources()` 로 그 사실의 `evidence_snippet` 을 품은 출처 집합을 구하고, 답이
그 집합에서 최소 하나를 인용했을 때만 해당 사실을 "근거 있음"으로 센다. 중복 적재는 같은
사실을 품은 출처가 여러 개라는 뜻이라 이 규칙에 그대로 흡수되고, 사실이 흩어진 케이스는
출처 하나만 인용하면 나머지 사실에서 점수를 잃는다. 화이트리스트는 상한(무엇을 인용해도
되는가)만 정하고, 하한(무엇을 인용해야 하는가)은 사실별 집합이 정한다.

두 전제 - 중복 출처가 실제로 있다는 것, 사실이 실제로 흩어져 있다는 것 - 은
`test_some_expected_sources_are_duplicate_copies_of_each_other` 와
`test_facts_usually_span_more_than_one_source` 가 잡아둔다. 적재 파이프라인이 중복 청크를
없애서 앞의 테스트가 깨지는 날, 화이트리스트를 "전부 인용"으로 조일 수 있는지 이 문단부터
다시 본다.

사실 문장이 근거와 어긋나는 것을 어디까지 잡는가
------------------------------------------------
`evidence_snippet` 이 발췌 안에 실재하는지는 위 테스트가 본다. 그것만으로는 `statement` 가
그 근거와 다른 말을 해도 통과한다 - 스니펫은 진짜인데 문장이 "담당자는 구성원다"이라고
덧붙이는 식이다. 정답지가 틀리면 그 위에서 나온 품질 지표가 전부 틀리므로, 기계로 판정할 수
있는 어긋남은 여기서 끊는다.

`statement` 에서 **판별 토큰**을 뽑아, 그 사실을 뒷받침하는 출처 발췌 **하나**가 토큰을 전부
품고 있어야 한다고 요구한다. 판별 토큰은 조사·어미에 흔들리지 않으면서 문장을 특정 대상·
수량에 못 박는 것들이다.

- 업무 코드 (`WF-207`, `FS-3`)
- 수량 - 숫자에 단위 한 글자를 붙여 `7월`·`13일`·`1차` 로 본다. 단위를 떼면 발췌 어딘가에
  무관한 `7` 과 `13` 이 따로 있기만 해도 통과한다
- 라틴 문자 낱말 (`LightGBM`, `pgvector`, `OAuth`)
- 인물 이름 - 발췌의 화자 표기(`근거: 구성원커:`)와 담당 표기(`구성원나가 담당`)에서 캐낸다

한국어 서술부는 조사·어미 때문에 부분문자열 비교가 곧 거짓 양성이라 토큰으로 삼지 않는다.
비교 대상을 스니펫이 아니라 **스니펫을 품은 발췌 전체**로 잡는 이유는, 스니펫이 "청크의 어디를
가리키는가"일 뿐이고 사실을 뒷받침하는 것은 그 청크이기 때문이다. identifier 계열의 `WF-207`
은 스니펫 바깥·같은 청크 안에 있다. 발췌를 이어 붙이지 않고 하나씩 보는 것은, 사실 하나는
청크 하나로 뒷받침된다는 위 채점 규칙과 같은 요구다.

남는 것은 셋이다. 하나, 판별 토큰이 전부 맞는데 문장이 근거를 잘못 읽은 경우 - 관계를
뒤집거나(A가 B에게 → B가 A에게), 조건을 빼거나, 한국어 서술부만 바꾼 경우다. 둘, 평가셋 어느
발췌에도 없는 이름을 새로 지어낸 경우 - 이름 목록을 발췌에서 캐내는 이상 목록에 없는 이름은
이름으로 보이지 않는다(발췌에 있는 이름을 잘못 가져다 쓴 경우는 잡는다). 셋, 이름에
`NAME_PARTICLES` 밖의 조사가 붙은 경우 - `구성원다조차` 는 이름 언급으로 세지 않는다.

앞의 둘은 자연어 함의 판정이라 LLM 없이는 못 가른다. 그건 #624 심사기 몫이고, 이 테스트는 그
심사기가 딛고 설 정답지에서 기계로 드러나는 결함만 걷어낸다. 셋째는 조사를 넓힐수록 이름으로
시작하는 다른 낱말을 잘못 잡을 확률이 같이 오르므로, 통과시키는 쪽으로 남겨둔 선택이다.
정답지 문장이 그런 조사를 쓸 일이 생기면 그때 목록을 넓힌다.

검색 평가셋과의 연결
--------------------
`retrieval_case_id` 는 검색 평가셋 `output/hybrid_rag_eval/data/evalset.json` 의 id 다.
`output/` 은 산출물이라 통째로 무시되지만 이 파일 하나만 `.gitignore` 에서 예외로 열어
추적한다 - 답변 평가의 정답지가 그 위에 얹히는데 기준이 저장소 밖에 있으면 CI 가 어긋남을
잡을 방법이 없기 때문이다.

그래서 대조 상대는 파생물이 아니라 원본이다. 픽스처의 질문·분류를 고치면서 연결 키를 그대로
두거나 없는 id 를 가리키면 CI 에서 걸린다. 검색 평가셋을 다시 만들어 질문이 바뀌었는데
픽스처를 안 고친 경우도 마찬가지다.

한때 세 필드만 추린 사본(`assistant_eval_retrieval_index.json`)을 두고 그것과 대조했는데,
그건 원본이 미추적이던 시절의 대체물이었다. 사본과 픽스처를 나란히 고치면 둘이 서로 맞아
전부 통과하고 원본에서 밀린 것은 드러나지 않았다. 원본을 추적하면서 사본은 지웠다 - 중복된
상태를 테스트로 감시하는 것보다 상태를 없애는 쪽이 낫다.

"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "assistant_eval"
# 저장소 루트/output/... - .gitignore 에서 이 파일만 예외로 열어 추적한다.
RETRIEVAL_EVALSET = (
    Path(__file__).resolve().parents[4] / "output" / "hybrid_rag_eval" / "data" / "evalset.json"
)

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
CASE_ID_PATTERN = re.compile(r"^(identifier|semantic|mixed)-(\d{2})$")
RETRIEVAL_ID_PATTERN = re.compile(r"^[ABC]\d{2}$")
RETRIEVAL_ID_PREFIX = {"identifier": "A", "semantic": "B", "mixed": "C"}
MINIMUM_PER_CATEGORY = 5

# 2026-08-19 기준 30건 중 14건은 사실이 여러 출처에 흩어져 있고, 8건은 발췌가 글자까지 같은
# 중복 출처를 갖는다. 하한만 두는 이유는 케이스를 더할 때마다 숫자를 고치지 않기 위해서다.
MINIMUM_MULTI_SOURCE_CASES = 10
MINIMUM_DUPLICATE_SOURCE_CASES = 5

# 판별 토큰 (모듈 docstring 의 "사실 문장이 근거와 어긋나는 것을 어디까지 잡는가" 참고).
# 떼어내는 순서가 있다. 코드를 먼저 떼야 WF-207 이 낱말 wf 와 수량 207 로 쪼개지지 않고,
# 낱말을 그다음에 떼야 E2E 나 Jira01 에서 수량 2, 1 이 딸려 나오지 않는다.
WORK_CODE_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9]*-\d+")
LATIN_WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
# 수량은 뒤에 붙는 단위 한 글자까지 묶는다. "7월 13일" 을 {7, 13} 으로 쪼개면 발췌 어딘가에
# 무관한 7 과 13 이 따로 있기만 해도 통과한다. 단위를 붙이면 "7월"·"13일" 로 맞춰야 한다.
QUANTITY_PATTERN = re.compile(r"(\d+)([가-힣]?)")

# 적재 파이프라인이 발췌에 남기는 인물 표기 두 가지. 이름 목록을 상수로 박으면 케이스를
# 더할 때 갱신을 잊어도 조용히 통과하므로 발췌에서 캐낸다. 발췌가 "근거:" 로 시작하면 그
# 라벨 자체가 이름으로 잡히므로 앞에서 끊는다.
SPEAKER_PATTERN = re.compile(r"(?:^|근거:\s*)(?!근거:)([가-힣]{2,4}):")
ASSIGNEE_PATTERN = re.compile(r"(?<![가-힣])([가-힣]{2,4})[가이]\s*(?:담당|리뷰)")
# 이름 뒤에 올 수 있는 조사. 긴 것부터 적어야 "에게" 가 "에" 로 잘리지 않는다.
#
# 2026-08-20: "으로" 계열이 빠져 있어서 마스킹이 `박상준으로` 를 통째로 놓쳤다. 이름 뒤
# 글자가 한글이면 경계 규칙에 걸려 탈락하는데, 조사 목록에도 없으면 빠져나갈 길이 없다.
NAME_PARTICLES = (
    "께서", "에게", "한테", "으로", "에서", "부터", "까지", "로",
    "은", "는", "이", "가", "을", "를", "의", "와", "과", "도",
)
# 2026-08-20 기준 발췌에서 캐지는 인물은 별칭 형태로 존재한다. 정규식을 고치다 목록이 비면 인물 규칙이
# 아무것도 안 하는 상태로 통과하므로 하한을 둔다.
MINIMUM_PERSON_NAMES = 5


def load_raw_cases() -> List[Dict]:
    paths = sorted(FIXTURES.glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def load_retrieval_evalset() -> Dict[str, Dict[str, str]]:
    cases = json.loads(RETRIEVAL_EVALSET.read_text(encoding="utf-8"))
    index = {case["id"]: case for case in cases}
    # id 가 겹치면 뒤엣것만 남아 항목 하나가 소리 없이 사라진다. 개수가 여전히 30이면
    # 1:1 대조도 그걸 못 잡으므로 여기서 먼저 끊는다.
    assert len(index) == len(cases), RETRIEVAL_EVALSET
    return index


def squeeze(text: str) -> str:
    return "".join(text.split())


def fact_evidence_sources(raw: Dict, fact: Dict) -> set[str]:
    """이 사실을 실제로 품고 있는 출처들. 사실 단위 인용 채점의 정답 집합이다."""
    snippet = squeeze(fact["evidence_snippet"])
    if not snippet:
        return set()
    return {
        source_id
        for source_id, excerpt in raw["expected_source_excerpts"].items()
        if snippet in squeeze(excerpt)
    }


def discriminative_tokens(text: str) -> set[tuple[str, str]]:
    """조사·어미에 흔들리지 않으면서 문장을 특정 대상·수량에 못 박는 토큰들."""
    codes = {("code", match.group(0).lower()) for match in WORK_CODE_PATTERN.finditer(text)}
    rest = WORK_CODE_PATTERN.sub(" ", text)
    words = {("word", match.group(0).lower()) for match in LATIN_WORD_PATTERN.finditer(rest)}
    rest = LATIN_WORD_PATTERN.sub(" ", rest)
    # "07월"과 "7월"은 같은 달이다. 앞자리 0 만으로 어긋났다고 보지 않는다.
    quantities = {
        ("num", f"{match.group(1).lstrip('0') or '0'}{match.group(2)}")
        for match in QUANTITY_PATTERN.finditer(rest)
    }
    return codes | words | quantities


def person_names() -> set[str]:
    """평가셋 발췌 전체에서 캐낸 인물 이름."""
    names: set[str] = set()
    for raw in load_raw_cases():
        for excerpt in raw["expected_source_excerpts"].values():
            names.update(SPEAKER_PATTERN.findall(excerpt))
            names.update(ASSIGNEE_PATTERN.findall(excerpt))
    return names


def mentions_person(statement: str, name: str) -> bool:
    """문장이 이 사람을 가리키는가.

    부분문자열로 찾으면 2자 이름이 더 긴 낱말의 앞머리로 들어앉은 자리까지 걸려 멀쩡한
    케이스가 깨진다. 이름에 조사 하나를 붙인 것이 한글 덩어리 전체와 맞아떨어질 때만 센다.
    """
    particles = "|".join(NAME_PARTICLES)
    pattern = rf"(?<![가-힣]){re.escape(name)}(?:{particles})?(?![가-힣])"
    return re.search(pattern, statement) is not None


def statement_mismatch(statement: str, excerpt: str, names: set[str]) -> set[str]:
    """발췌가 문장의 판별 토큰을 다 품고 있지 않다면 무엇이 빠졌는지 돌려준다.

    발췌 쪽은 경계를 따지지 않고 부분문자열로 본다. 판정은 문장 쪽에서 끝났고, 발췌를 넓게
    보는 실수는 통과시키는 방향이라 멀쩡한 케이스를 깨지 않는다.
    """
    missing = {
        f"{kind}:{value}"
        for kind, value in discriminative_tokens(statement) - discriminative_tokens(excerpt)
    }
    hidden = {
        name for name in names if mentions_person(statement, name) and name not in excerpt
    }
    return missing | {f"name:{name}" for name in hidden}


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


def test_case_ids_are_contiguously_numbered_within_each_category():
    """분류별로 01 부터 빈칸 없이 이어져야 한다.

    픽스처 파일이 지워지거나 번호를 건너뛰고 새로 만들면 케이스 수는 줄어드는데 분류별
    하한(5건)에는 한동안 걸리지 않는다. 그 사이 품질 지표는 조용히 좁아진 평가셋 위에서
    나온다. case_id 접두사가 category 와 같은지도 여기서 함께 본다.
    """
    numbers: Dict[str, List[int]] = {name: [] for name in CATEGORIES}
    for raw in load_raw_cases():
        match = CASE_ID_PATTERN.match(raw["case_id"])
        assert match, raw["case_id"]
        assert match.group(1) == raw["category"], (raw["case_id"], raw["category"])
        numbers[raw["category"]].append(int(match.group(2)))

    for name, found in numbers.items():
        assert sorted(found) == list(range(1, len(found) + 1)), (name, sorted(found))


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


def test_case_number_matches_the_linked_retrieval_case_number():
    """identifier-07 은 A07 을 가리켜야 한다.

    앞 테스트는 글자(A/B/C)만 본다. 케이스를 복사해 만들면서 번호를 안 고치면 분류는 맞는데
    질문과 검색 케이스가 한 칸씩 어긋난 상태로 남는다.
    """
    for raw in load_raw_cases():
        match = CASE_ID_PATTERN.match(raw["case_id"])
        assert match, raw["case_id"]
        assert raw["retrieval_case_id"][1:] == match.group(2), (
            raw["case_id"],
            raw["retrieval_case_id"],
        )


def test_each_case_matches_its_retrieval_evalset_entry():
    """연결한 검색 케이스의 질문·분류가 원본 평가셋 항목과 같은지 대조한다.

    번호 규칙만 맞추면 존재하지 않는 id(A99)를 가리켜도, 픽스처 질문만 바꿔도 통과한다.
    """
    evalset = load_retrieval_evalset()
    for raw in load_raw_cases():
        entry = evalset.get(raw["retrieval_case_id"])
        assert entry is not None, (raw["case_id"], raw["retrieval_case_id"])
        assert entry["question"] == raw["question"], (
            raw["case_id"],
            raw["question"],
            entry["question"],
        )
        assert entry["category"] == raw["category"], (raw["case_id"], entry["category"])


def test_retrieval_evalset_and_fixtures_are_one_to_one():
    """검색 케이스 전부에 답변 정답지가 하나씩 있어야 두 지표를 나란히 놓을 수 있다.

    검색 평가셋에 케이스를 더하고 답변 픽스처를 안 만들면, 답변 품질은 좁아진 표본 위에서
    측정되는데 검색 지표와 같은 30문항인 것처럼 읽힌다.
    """
    evalset = load_retrieval_evalset()
    linked = sorted(raw["retrieval_case_id"] for raw in load_raw_cases())

    assert linked == sorted(evalset), (linked, sorted(evalset))


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


def test_every_fact_is_carried_by_at_least_one_expected_source():
    """정답을 손으로 쓰다 보면 근거에 없는 문장을 적기 쉽다. 여기서 막는다.

    발췌를 이어 붙여 한 번에 찾으면 두 출처의 경계에 걸친 문자열도 통과한다. 어느 출처에도
    없는 문장이 근거로 인정되므로 `fact_evidence_sources` 로 발췌 하나하나와 대조한다.
    이 매핑이 곧 사실 단위 인용 채점의 정답 집합이다(모듈 docstring 참고).
    """
    for raw in load_raw_cases():
        for fact in raw["must_include_facts"]:
            assert squeeze(fact["evidence_snippet"]), (raw["case_id"], fact["fact_id"])
            assert fact_evidence_sources(raw, fact), (
                f"{raw['case_id']}/{fact['fact_id']}: {fact['evidence_snippet']}"
            )


def test_person_names_are_minable_from_the_excerpts():
    """인물 규칙이 실제로 볼 이름이 있는지 먼저 확인한다.

    이름 목록이 비면 `test_every_fact_statement_matches_its_evidence` 의 인물 검사는 아무
    문장도 걸러내지 못한 채 통과한다. 방어선이 있는 척하는 쪽이 없는 것보다 나쁘다.
    """
    names = person_names()
    assert len(names) >= MINIMUM_PERSON_NAMES, sorted(names)


def test_every_fact_statement_matches_its_evidence():
    """사실 문장의 판별 토큰이 근거 발췌 하나 안에 전부 있어야 한다.

    스니펫이 실재하는지만 보면 문장이 근거에 없는 담당자·날짜·업무 코드를 덧붙여도 통과한다.
    정답지가 틀리면 그 위에서 나온 품질 지표가 전부 틀리므로, 기계로 판정할 수 있는 어긋남은
    여기서 끊는다. 무엇을 토큰으로 보고 무엇이 남는지는 모듈 docstring 에 적었다.
    """
    names = person_names()
    for raw in load_raw_cases():
        for fact in raw["must_include_facts"]:
            excerpts = [
                raw["expected_source_excerpts"][source_id]
                for source_id in fact_evidence_sources(raw, fact)
            ]
            assert excerpts, (raw["case_id"], fact["fact_id"])

            mismatches = [
                statement_mismatch(fact["statement"], excerpt, names) for excerpt in excerpts
            ]
            assert any(not missing for missing in mismatches), (
                f"{raw['case_id']}/{fact['fact_id']}: {fact['statement']} "
                f"- 근거에 없는 것 {sorted(min(mismatches, key=len))}"
            )


def test_facts_usually_span_more_than_one_source():
    """사실이 한 출처에 몰려 있지 않은 케이스가 충분히 있어야 한다.

    모든 케이스에서 출처 하나가 사실 전부를 품는다면 "화이트리스트 중 하나만 인용" 규칙과
    사실 단위 규칙이 같은 점수를 내고, 사실 단위 채점을 하는 의미가 사라진다. 여기 걸리면
    평가셋이 단일 출처 케이스로 납작해진 것이므로 규칙보다 픽스처를 먼저 본다.
    """
    spanning = 0
    for raw in load_raw_cases():
        per_fact = [fact_evidence_sources(raw, fact) for fact in raw["must_include_facts"]]
        # 빈 리스트면 set.intersection 이 TypeError 로 터진다. 다른 테스트가 보장하는
        # 조건에 기대지 않고 여기서 직접 끊는다.
        assert per_fact, raw["case_id"]
        if not set.intersection(*per_fact):
            spanning += 1

    assert spanning >= MINIMUM_MULTI_SOURCE_CASES, spanning


def test_some_expected_sources_are_duplicate_copies_of_each_other():
    """화이트리스트를 '전부 인용'으로 조이지 못하는 근거가 픽스처 안에 실제로 있는지 본다.

    발췌가 글자까지 같은 출처가 둘 이상이면 어느 쪽이 검색에 올라올지 정답지가 고를 수 없다.
    적재에서 중복이 사라져 이 테스트가 깨지면, 그때는 규칙을 조일 수 있는지 다시 판단한다.
    """
    duplicated = 0
    for raw in load_raw_cases():
        excerpts = [squeeze(text) for text in raw["expected_source_excerpts"].values()]
        if len(excerpts) != len(set(excerpts)):
            duplicated += 1

    assert duplicated >= MINIMUM_DUPLICATE_SOURCE_CASES, duplicated


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


def test_evidence_snippets_are_long_enough_to_be_discriminative() -> None:
    """조각은 검색된 청크 본문에서 부분 문자열로 찾는다(scorer.score_grounding).
    짧고 상투적인 조각은 무관한 청크에도 걸려 근거 있음으로 오판된다.

    하한은 현재 실측 최소값(10자)이다. 여유를 두지 않는 것은 이 저장소의 하한 규약과
    같다 - 여유를 두면 그만큼 짧아져도 아무도 모른다. 더 짧은 조각이 정말 필요하면
    이 값을 내리되, 그 조각이 무엇과 충돌하지 않는지 확인하고 이유를 남긴다.
    """
    minimum = 10
    too_short = [
        (raw["case_id"], fact["fact_id"], fact["evidence_snippet"])
        for raw in load_raw_cases()
        for fact in raw["must_include_facts"]
        if len(squeeze(fact["evidence_snippet"])) < minimum
    ]

    assert too_short == []
