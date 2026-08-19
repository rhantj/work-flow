from __future__ import annotations

from tests.assistant_eval.judge import judge_answer

_FACTS = [
    {
        "fact_id": "F1",
        "statement": "태오가 LightGBM 튜닝을 맡기로 했다",
        "evidence_snippet": "LightGBM 하이퍼파라미터 튜닝은 제가 맡겠습니다",
    },
    {
        "fact_id": "F2",
        "statement": "기본 모델은 LightGBM으로 고정하기로 했다",
        "evidence_snippet": "기본 모델은 LightGBM으로 고정한다",
    },
]
_CLAIMS = [
    {
        "claim_id": "N1",
        "statement": "LightGBM 튜닝의 마감일을 특정한다",
        "reason": "근거 발언에 기한이 없다",
    }
]


def _answers(mapping):
    """문항 문면으로 응답을 고르는 가짜 심사기.

    프롬프트 전체가 아니라 질문 블록만 본다. 답변문에도 사실 문면과 같은 낱말이 들어 있어
    전체에서 찾으면 엉뚱한 문항의 응답이 돌아온다.
    """

    def ask(prompt: str) -> str:
        question = prompt.split("[질문]")[-1]
        for needle, reply in mapping.items():
            if needle in question:
                return reply
        return "아니오"

    return ask


def test_all_facts_covered_and_nothing_invented_scores_one():
    score = judge_answer(
        "태오가 LightGBM 튜닝을 맡습니다. 기본 모델은 LightGBM으로 고정합니다.",
        _FACTS,
        _CLAIMS,
        ask=_answers({"담고 있습니까": "예", "하고 있습니까": "아니오"}),
    )

    assert score.coverage == 1.0
    assert score.safety == 1.0
    assert score.score == 1.0


def test_vacuous_answer_scores_zero():
    """아무 말도 안 한 답변은 환각 문항을 거저 통과한다.

    두 축을 평균하면 그것만으로 바닥값이 0.5가 되고, 침묵하는 답변이 상위권에 올라온다.
    회의록 평가에서 실제로 그런 일이 있었다. 지어내지 않은 것은 담아낸 것이 아니다.
    """
    score = judge_answer(
        "관련 자료를 찾지 못했습니다.",
        _FACTS,
        _CLAIMS,
        ask=_answers({"담고 있습니까": "아니오", "하고 있습니까": "아니오"}),
    )

    assert score.coverage == 0.0
    assert score.safety == 1.0
    assert score.score == 0.0


def test_hallucinated_answer_forfeits_its_coverage():
    """담아낸 내용이 아무리 많아도 지어낸 답변은 쓸 수 없다."""
    score = judge_answer(
        "태오가 LightGBM 튜닝을 8월 30일까지 끝냅니다. 기본 모델은 LightGBM입니다.",
        _FACTS,
        _CLAIMS,
        ask=_answers({"담고 있습니까": "예", "하고 있습니까": "예"}),
    )

    assert score.coverage == 1.0
    assert score.safety == 0.0
    assert score.score == 0.0
    assert [verdict.passed for verdict in score.claim_verdicts] == [False]


def test_partially_covered_answer_scores_the_fraction():
    score = judge_answer(
        "태오가 LightGBM 튜닝을 맡습니다.",
        _FACTS,
        _CLAIMS,
        ask=_answers({"태오가": "예", "기본 모델은": "아니오", "하고 있습니까": "아니오"}),
    )

    assert score.coverage == 0.5
    assert score.score == 0.5
    assert [verdict.item_id for verdict in score.fact_verdicts] == ["F1", "F2"]


def test_safety_defaults_to_one_when_no_forbidden_claim_is_declared():
    """어길 제약이 없으면 충실도가 그대로 점수다.

    충실도 쪽은 반대로 0.0이 기본값이다. 잰 것이 없으면 점수를 줄 근거도 없다.
    """
    score = judge_answer("답변", _FACTS, [], ask=lambda prompt: "예")

    assert score.safety == 1.0
    assert score.score == 1.0


def test_coverage_defaults_to_zero_when_no_fact_is_declared():
    score = judge_answer("답변", [], _CLAIMS, ask=lambda prompt: "아니오")

    assert score.coverage == 0.0
    assert score.score == 0.0


def test_unparseable_answer_counts_as_fail_for_coverage():
    score = judge_answer(
        "답변", _FACTS, [], ask=lambda prompt: "글쎄요 판단하기 어렵습니다"
    )

    assert score.coverage == 0.0


def test_facts_are_judged_on_the_answer_alone():
    """충실도 문항에 근거 스니펫이나 원문 발췌를 넘기지 않는다.

    회의록 평가에서 심사기에 요약과 원문을 같이 넘겨, 문항은 "요약에 담겼나"인데 실제로
    잰 것은 "어딘가에 있나"가 된 사고가 있었다(PR #611). 규칙 기반 점수가 내려가야 할
    자리에서 0.649 -> 0.794 로 오른 것이 단서였다. 여기서 새어 들어올 수 있는 것은
    `evidence_snippet` 이라, 프롬프트에 그것이 없음을 직접 확인한다.
    """
    seen = []

    def fake_ask(prompt):
        seen.append(prompt)
        return "예"

    judge_answer("답변본", _FACTS, [], ask=fake_ask)

    assert len(seen) == 2
    for prompt in seen:
        assert "답변본" in prompt
        for fact in _FACTS:
            assert fact["evidence_snippet"] not in prompt


def test_forbidden_claims_are_judged_on_the_answer_alone():
    """환각 문항에도 답변문과 금지 문면만 넘긴다.

    `reason` 은 "근거 발언에 기한이 없다"처럼 원문 사정을 적은 정답지 메모라, 넘기면
    심사기가 답변이 아니라 그 메모를 읽고 답할 여지가 생긴다.
    """
    seen = []

    def fake_ask(prompt):
        seen.append(prompt)
        return "아니오"

    judge_answer("답변본", [], _CLAIMS, ask=fake_ask)

    assert len(seen) == 1
    assert "답변본" in seen[0]
    assert _CLAIMS[0]["statement"] in seen[0]
    assert _CLAIMS[0]["reason"] not in seen[0]


def test_question_ids_are_carried_back_for_diagnosis():
    """어느 항목이 떨어졌는지 못 되짚으면 점수만 보고 고칠 데를 찾을 수 없다."""
    score = judge_answer(
        "답변",
        _FACTS,
        _CLAIMS,
        ask=_answers({"태오가": "예", "기본 모델은": "아니오", "하고 있습니까": "예"}),
    )

    assert [(v.item_id, v.passed) for v in score.fact_verdicts] == [("F1", True), ("F2", False)]
    assert [(v.item_id, v.passed) for v in score.claim_verdicts] == [("N1", False)]
