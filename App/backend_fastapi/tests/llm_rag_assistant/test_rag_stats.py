"""질의 집계 카운터.

## 무엇을 지키는 테스트인가

이 관측을 만든 이유가 "라우팅의 효과를 모른다"라서, 카운터가 **틀린 조건에 오르면
관측이 없는 것보다 나쁘다.** 없으면 모른다는 걸 알지만, 틀리면 틀린 결론을 내린다.
그래서 필드별 증가 조건을 하나씩 못 박는다.

동시에 통계가 **질의를 죽이지 않는 것**도 지킨다. 부수적인 계측이 본 기능을 실패시키면
그건 관측이 아니라 신규 장애 지점이다.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pytest

from llm_rag_assistant.app.services import rag_stats
from llm_rag_assistant.app.services.rag_stats import (
    QuestionQueryStats,
    _counter_fields,
    _stats_key,
    pinned_stats_day,
    record_answer_provider,
    record_question_query,
)


def _freeze_clock(monkeypatch, start: datetime) -> list[datetime]:
    """날짜 계산만 가짜 시계에 물린다. 반환한 리스트의 0번을 바꾸면 시간이 흐른다.

    _stats_key 자체를 갈아끼우지 않고 인자로 넘기는 이유: 날짜 형식(UTC, YYYY-MM-DD)은
    실제 구현이 계산해야 이 테스트가 형식 회귀까지 잡는다.
    """
    now = [start]
    monkeypatch.setattr(rag_stats, "_stats_key", lambda: _stats_key(now[0]))
    return now


def _stats(**overrides) -> QuestionQueryStats:
    base = {"project_id": 7, "top_k": 5, "personal": False, "source_count": 5}
    return QuestionQueryStats(**{**base, **overrides})


def test_every_question_counts_toward_total_and_its_project():
    """프로젝트 분포가 없으면 '코드 질문 30%'가 실사용인지 데모 조작인지 구분할 수 없다.

    project_id=1 은 테스트 주입 데이터가 섞인 데모다.
    """
    fields = _counter_fields(_stats(project_id=1))

    assert fields["total"] == 1
    assert fields["proj_1"] == 1


def test_personal_questions_are_counted_but_get_no_code_fields():
    """개인화 질문은 라우팅을 타지 않으므로 코드 필드의 분모에 들어가면 안 된다.

    들어가면 '코드 질문 비중'이 라우팅이 닿지도 않는 경로까지 포함해 낮게 나온다.
    """
    fields = _counter_fields(_stats(personal=True, code_count=2))

    assert fields["personal"] == 1
    assert not [name for name in fields if name.startswith("codes_")]
    assert "code_miss" not in fields


@pytest.mark.parametrize(
    ("code_count", "expected"),
    [(0, "codes_0"), (1, "codes_1"), (4, "codes_4"), (5, "codes_5plus"), (9, "codes_5plus")],
)
def test_code_count_lands_in_the_right_bucket(code_count: int, expected: str):
    """5개 이상을 한 칸에 모으는 이유: top_k 가 5라 그 이상은 어차피 잘려 결정에 안 쓰인다."""
    fields = _counter_fields(_stats(code_count=code_count, code_slots=code_count))

    assert fields[expected] == 1


def test_truncation_is_counted_when_codes_outnumber_their_slots():
    """이 값이 top_k 상한을 올릴 이유가 되는지를 결정한다."""
    fields = _counter_fields(_stats(code_count=7, code_slots=5))

    assert fields["codes_truncated"] == 1


def test_no_truncation_when_every_code_got_a_slot():
    fields = _counter_fields(_stats(code_count=4, code_slots=4))

    assert "codes_truncated" not in fields


def test_code_miss_is_counted_when_the_code_matched_nothing():
    """없는 코드를 말했거나 색인이 빠진 경우. 폴백 경로의 크기를 본다."""
    fields = _counter_fields(_stats(code_count=2, code_slots=3, code_hits=0))

    assert fields["code_miss"] == 1


def test_a_failed_code_search_is_not_counted_as_a_miss():
    """'코드가 정말 없음'과 '조회 실패'를 한 칸에 담으면 관측값이 오염된다.

    같은 이유로 실패 경로에서는 라우팅 info 로그도 남기지 않는다(retrieval_service).
    """
    fields = _counter_fields(
        _stats(code_count=2, code_slots=3, code_hits=0, code_search_failed=True)
    )

    assert "code_miss" not in fields


def test_short_evidence_is_counted():
    """중복 제거를 넣고도 근거가 top_k 에 못 미치는 비율을 본다."""
    fields = _counter_fields(_stats(source_count=3, top_k=5))

    assert fields["sources_short"] == 1


def test_full_evidence_is_not_counted_as_short():
    fields = _counter_fields(_stats(source_count=5, top_k=5))

    assert "sources_short" not in fields


def test_stats_key_uses_utc_not_the_server_timezone():
    """서버 타임존 설정에 흔들리면 날짜가 재배포마다 바뀔 수 있다.

    KST 와 9시간 차이가 난다는 점은 읽는 쪽(show_rag_stats.py)과 문서에 함께 적혀 있다.
    """
    kst_midnight_edge = datetime(2026, 8, 2, 16, 30, tzinfo=timezone.utc)

    assert _stats_key(kst_midnight_edge) == "rag_stats:2026-08-02"


@pytest.mark.asyncio
async def test_counters_and_ttl_land_in_redis(rag_stats_redis):
    await record_question_query(_stats(project_id=3, code_count=1, code_slots=3, code_hits=1))

    key = _stats_key()
    assert rag_stats_redis.hashes[key] == {"total": 1, "proj_3": 1, "codes_1": 1}
    # TTL 이 빠지면 키가 영원히 남는다. 90일.
    assert rag_stats_redis.expirations[key] == 90 * 24 * 60 * 60


@pytest.mark.asyncio
async def test_repeated_questions_accumulate(rag_stats_redis):
    await record_question_query(_stats(project_id=3))
    await record_question_query(_stats(project_id=3))

    assert rag_stats_redis.hashes[_stats_key()]["total"] == 2


@pytest.mark.asyncio
async def test_each_answering_backend_gets_its_own_counter(rag_stats_redis):
    """폴백 체인은 조용히 다음 백엔드로 넘어간다. 백엔드를 한 칸에 합쳐 세면 'HF가 답하고
    있다'와 'HF가 죽어 Ollama 가 다 받아내고 있다'가 같은 숫자로 보인다.
    """
    await record_answer_provider("huggingface")
    await record_answer_provider("huggingface")
    await record_answer_provider("gemini")

    key = _stats_key()
    assert rag_stats_redis.hashes[key] == {"provider_huggingface": 2, "provider_gemini": 1}
    # 질의 카운터와 같은 키를 쓰므로 TTL 도 같이 걸려야 한다.
    assert rag_stats_redis.expirations[key] == 90 * 24 * 60 * 60


@pytest.mark.asyncio
async def test_provider_counts_share_the_daily_key_with_the_query_counters(rag_stats_redis):
    """'HF가 몇 %를 답했나'는 provider_* / total 이다. 분자와 분모가 다른 키에 있으면
    두 번 읽어 맞춰야 하고, 날짜 경계에서 서로 다른 날을 볼 수 있다.
    """
    await record_question_query(_stats())
    await record_answer_provider("ollama")

    counts = rag_stats_redis.hashes[_stats_key()]
    assert counts["total"] == 1
    assert counts["provider_ollama"] == 1


@pytest.mark.asyncio
async def test_counting_the_provider_does_not_touch_the_query_counters(rag_stats_redis):
    """생성은 검색 뒤에 따로 집계된다. 여기서 total 을 또 올리면 분모가 두 배가 된다."""
    await record_answer_provider("huggingface")

    assert rag_stats_redis.hashes[_stats_key()] == {"provider_huggingface": 1}


@pytest.mark.asyncio
async def test_a_question_that_crosses_utc_midnight_is_counted_on_one_day(
    rag_stats_redis, monkeypatch
):
    """자정을 넘겨도 분모(total)와 분자(provider_*)가 같은 날 키에 있어야 한다.

    질문은 검색 직후, 프로바이더는 생성이 끝난 뒤에 센다. 그 사이 수 초 동안 날짜가 바뀌면
    어제는 분모만, 오늘은 분자만 늘어 양쪽 날의 비율이 모두 틀린다.
    """
    now = _freeze_clock(monkeypatch, datetime(2026, 8, 3, 23, 59, 58, tzinfo=timezone.utc))

    with pinned_stats_day():
        await record_question_query(_stats())
        now[0] += timedelta(seconds=5)  # 생성에 걸린 시간. 여기서 UTC 자정을 넘는다.
        await record_answer_provider("gemini")

    assert list(rag_stats_redis.hashes) == ["rag_stats:2026-08-03"]
    counts = rag_stats_redis.hashes["rag_stats:2026-08-03"]
    assert counts["total"] == 1
    assert counts["provider_gemini"] == 1


@pytest.mark.asyncio
async def test_the_pinned_day_does_not_outlive_its_block(rag_stats_redis, monkeypatch):
    """못 박은 날짜가 블록 밖으로 새면 다음 날 카운터가 전부 어제 키에 쌓인다.

    ContextVar 는 태스크가 재사용되면 같이 살아남으므로(큐 워커 루프) 반드시 되돌려야 한다.
    """
    now = _freeze_clock(monkeypatch, datetime(2026, 8, 3, 23, 59, 58, tzinfo=timezone.utc))

    with pinned_stats_day():
        await record_answer_provider("gemini")
    now[0] += timedelta(seconds=5)
    await record_answer_provider("ollama")

    assert rag_stats_redis.hashes["rag_stats:2026-08-03"] == {"provider_gemini": 1}
    assert rag_stats_redis.hashes["rag_stats:2026-08-04"] == {"provider_ollama": 1}


@pytest.mark.asyncio
async def test_a_broken_redis_never_fails_the_provider_count(monkeypatch, caplog):
    """프로바이더 집계도 record_question_query 와 같은 정책을 따른다."""
    def _explode():
        raise RuntimeError("redis down")

    monkeypatch.setattr(rag_stats, "get_async_redis_client", _explode)

    with caplog.at_level(logging.WARNING):
        await record_answer_provider("gemini")  # 예외가 나가면 이 줄에서 테스트가 깨진다

    assert "질의 통계 기록 실패" in caplog.text


@pytest.mark.asyncio
async def test_a_broken_redis_never_fails_the_query(monkeypatch, caplog):
    """통계가 답변을 죽이면 그건 관측이 아니라 새로 만든 장애 지점이다.

    advance_rag_project_epoch 와 같은 정책이다.
    """
    def _explode():
        raise RuntimeError("redis down")

    monkeypatch.setattr(rag_stats, "get_async_redis_client", _explode)

    with caplog.at_level(logging.WARNING):
        await record_question_query(_stats())  # 예외가 나가면 이 줄에서 테스트가 깨진다

    assert "질의 통계 기록 실패" in caplog.text
