from __future__ import annotations

from tests.assistant_eval.scorer import score_grounding
from tests.assistant_eval.test_dataset import load_raw_cases

# 사실 둘이 서로 다른 출처에 흩어져 있고, 한 사실은 발췌가 글자까지 같은 출처 두 벌을
# 갖는다. 사실 단위 채점과 케이스 단위 채점이 갈리는 자리를 한 케이스로 다 덮는다.
_SPLIT_CASE = {
    "case_id": "mixed-99",
    "expected_source_ids": ["action_item#452", "action_item#488", "meeting#75"],
    "expected_source_excerpts": {
        "action_item#452": "LightGBM 하이퍼파라미터 튜닝은 제가 맡겠습니다",
        "action_item#488": "LightGBM 하이퍼파라미터 튜닝은 제가 맡겠습니다",
        "meeting#75": "결정사항: 기본 모델은 LightGBM으로 고정한다",
    },
    "must_include_facts": [
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
    ],
}


def test_all_supporting_sources_retrieved_scores_one():
    score = score_grounding(_SPLIT_CASE, ["action_item#452", "meeting#75"])

    assert score.score == 1.0
    assert score.grounded_fact_ids == ("F1", "F2")
    assert score.ungrounded_fact_ids == ()


def test_no_sources_scores_zero():
    score = score_grounding(_SPLIT_CASE, [])

    assert score.score == 0.0
    assert score.ungrounded_fact_ids == ("F1", "F2")


def test_whitelisted_source_does_not_ground_a_fact_it_does_not_carry():
    """케이스 단위 채점과 사실 단위 채점이 갈리는 자리.

    `meeting#75` 는 화이트리스트 안이라 "기대 출처가 올라왔는가"만 보면 만점이다. 그런데
    그 발췌는 F1 을 뒷받침하지 않는다 - F1 은 근거 없이 말한 셈이고, 사실 단위로 재야
    그게 드러난다. 이 테스트가 깨지면 채점이 답변 단위로 되돌아간 것이다.
    """
    score = score_grounding(_SPLIT_CASE, ["meeting#75"])

    assert score.score == 0.5
    assert score.grounded_fact_ids == ("F2",)
    assert score.ungrounded_fact_ids == ("F1",)
    assert score.off_whitelist_sources == ()


def test_duplicate_copies_of_a_source_are_interchangeable():
    """발췌가 글자까지 같은 중복 적재분 중 어느 쪽이 올라와도 같은 점수여야 한다.

    어느 벌이 검색에 올라올지는 정답지가 고정할 수 없다(test_dataset docstring).
    """
    first = score_grounding(_SPLIT_CASE, ["action_item#452"])
    second = score_grounding(_SPLIT_CASE, ["action_item#488"])

    assert first.score == second.score == 0.5
    assert first.grounded_fact_ids == second.grounded_fact_ids == ("F1",)


def test_sources_outside_the_whitelist_are_reported_but_never_score():
    """화이트리스트 밖 출처는 어느 사실도 뒷받침하지 못해 이미 0점이다.

    거기에 감점을 더 얹으면 같은 실패를 두 번 세게 되므로 진단 항목으로만 남긴다.
    """
    score = score_grounding(_SPLIT_CASE, ["task#62", "meeting#75"])

    assert score.score == 0.5
    assert score.off_whitelist_sources == ("task#62",)
    assert score.retrieved_sources == ("meeting#75", "task#62")


def test_every_fixture_case_is_perfectly_scorable_by_its_expected_sources():
    """기대 출처가 전부 올라오면 어느 케이스든 만점이 나와야 한다.

    사실 하나라도 정답 집합이 비어 있으면 그 케이스는 무슨 답을 해도 만점을 못 받는다 -
    채점기가 실제 응답이 아니라 정답지 결함을 재게 된다. 픽스처와 채점기를 맞물려 본다.
    """
    for raw in load_raw_cases():
        score = score_grounding(raw, raw["expected_source_ids"])
        assert score.score == 1.0, (raw["case_id"], score.ungrounded_fact_ids)
