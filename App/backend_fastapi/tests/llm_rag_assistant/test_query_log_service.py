"""어시스턴트 질의 로그.

## 무엇을 지키는 테스트인가

이 로그는 "코드 없는 고유명사 질문의 검색 실패율"을 재려고 질문 원문을 남긴다
(docs/decisions, 이슈 #626). 원문을 남기는 순간 두 가지가 동시에 위험해진다.

1. **개인정보** — 질문 본문에 이메일·전화번호가 섞여 들어온다. 저장 전에 지워야 하고,
   "지웠는지"는 눈으로 확인할 수 있는 게 아니라 테스트가 못 박아야 한다.
2. **답변 경로** — 관측을 붙이려다 기능을 잃으면 안 된다. DB가 죽어도, 죽지 않고
   느려지기만 해도 답변은 그대로 나가야 한다.

user_id 를 담지 않는 것도 여기서 못 박는다. 컬럼을 나중에 슬쩍 늘리면 "누가 무엇을
물었나"가 재구성돼 #626이 없앤 부담이 그대로 돌아온다.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from llm_rag_assistant.app.services import query_log_service
from llm_rag_assistant.app.services.query_log_service import (
    mask_sensitive_text,
    purge_expired_rows,
    record_query_log,
)


@pytest.fixture
def logging_enabled(monkeypatch) -> None:
    """스위치는 기본이 꺼짐이다. 기록 동작을 보는 테스트는 명시적으로 켠다."""
    monkeypatch.setenv("ASSISTANT_QUERY_LOG_ENABLED", "true")


class _FakeConn:
    def __init__(self, delay: float = 0.0, table_exists: bool = True) -> None:
        self.calls: list[tuple] = []
        self._delay = delay
        self._table_exists = table_exists

    async def fetchval(self, query: str, *args):
        return "assistant_query_log" if self._table_exists else None

    async def execute(self, query: str, *args):
        if self._delay:
            await asyncio.sleep(self._delay)
        self.calls.append((query, args))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakePool:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    def acquire(self):
        return self._conn


class _RaisingConn:
    async def execute(self, query: str, *args):
        raise RuntimeError("DB 장애")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _RaisingPool:
    def acquire(self):
        return _RaisingConn()


@pytest.mark.parametrize(
    "raw",
    [
        "kim@example.com 으로 보낸 자료 어디 있어",
        "담당자 메일 kim.min-jun+work@sub.example.co.kr 맞나요",
    ],
)
def test_email_addresses_are_replaced_before_storage(raw: str) -> None:
    masked = mask_sensitive_text(raw)

    assert "@" not in masked
    assert "[EMAIL]" in masked


@pytest.mark.parametrize(
    "raw",
    [
        "010-1234-5678 로 연락 달라고 했는데",
        "01012345678 이 누구 번호야",
        "010 1234 5678 확인",
        "사무실 02-123-4567 맞아?",
        "+82-10-1234-5678 국제번호",
        "+82 (0)10-1234-5678 국제표기",
        # 국번을 010 계열로만 좁히면 +82 유선번호가 남고, 구분자에 괄호가 없으면
        # 사람이 흔히 쓰는 (010) 1234-5678 표기가 통째로 새어 나간다.
        "+82-2-1234-5678 사무실",
        "+82 2 1234 5678 확인",
        "(010) 1234-5678 로 연락",
        "02)1234-5678 내선",
    ],
)
def test_korean_phone_numbers_are_replaced_before_storage(raw: str) -> None:
    masked = mask_sensitive_text(raw)

    assert "[PHONE]" in masked
    assert "1234" not in masked


@pytest.mark.parametrize(
    "raw",
    [
        "2026-08-19 마감 업무 알려줘",
        "TASK-230 진행 상황",
        "230번 업무 언제까지야",
    ],
)
def test_dates_and_task_codes_are_not_mistaken_for_phone_numbers(raw: str) -> None:
    """마스킹이 과하면 분석 대상인 질문 자체가 뭉개진다. 실패율을 재려고 남긴 원문이
    코드와 날짜를 잃으면 로그를 남긴 목적이 사라진다."""
    assert mask_sensitive_text(raw) == raw


@pytest.mark.asyncio
async def test_stored_question_is_masked_not_the_raw_input(logging_enabled) -> None:
    conn = _FakeConn()

    await record_query_log(
        _FakePool(conn),
        project_id=7,
        question="kim@example.com 010-1234-5678 로 연락",
        source_ids=[3, 9],
        provider="gemini",
    )

    (_, args) = conn.calls[0]
    stored_question = args[1]
    assert "kim@example.com" not in stored_question
    assert "010-1234-5678" not in stored_question
    assert "[EMAIL]" in stored_question and "[PHONE]" in stored_question


@pytest.mark.asyncio
async def test_stored_columns_are_exactly_the_agreed_five(logging_enabled) -> None:
    """#626이 정한 저장 항목: 질문 원문, project_id, source_id 목록, provider, 생성 시각."""
    conn = _FakeConn()

    await record_query_log(
        _FakePool(conn),
        project_id=7,
        question="로그인 API 누가 맡았어",
        source_ids=[3, 9],
        provider="gemini",
    )

    (query, args) = conn.calls[0]
    assert args == (7, "로그인 API 누가 맡았어", [3, 9], "gemini")
    assert "user_id" not in query
    assert "answer" not in query


@pytest.mark.asyncio
async def test_nothing_is_written_while_logging_is_switched_off(monkeypatch) -> None:
    """스위치가 꺼져 있으면 쓰기 경로는 DB 를 건드리지 않는다.

    삭제까지 멈추는 것은 아니다 - 만료 삭제는 스위치와 무관한 일일 작업이 따로 책임진다
    (test_expired_rows_are_purged_even_while_logging_is_switched_off).
    """
    monkeypatch.delenv("ASSISTANT_QUERY_LOG_ENABLED", raising=False)
    conn = _FakeConn()

    await record_query_log(
        _FakePool(conn), project_id=1, question="질문", source_ids=[1], provider="ollama"
    )

    assert conn.calls == []


@pytest.mark.asyncio
async def test_rows_older_than_the_retention_window_are_deleted_by_the_write(logging_enabled) -> None:
    """보존기간 90일은 지우는 주체가 있어야 지켜진다. 쓰기가 곧 청소다."""
    conn = _FakeConn()

    await record_query_log(
        _FakePool(conn), project_id=1, question="질문", source_ids=[], provider="ollama"
    )

    (query, _) = conn.calls[0]
    normalized = " ".join(query.split()).upper()
    assert "DELETE FROM ASSISTANT_QUERY_LOG" in normalized
    assert "90 DAYS" in normalized


@pytest.mark.asyncio
async def test_a_dead_database_does_not_break_the_answer(
    logging_enabled, caplog: pytest.LogCaptureFixture
) -> None:
    await record_query_log(
        _RaisingPool(), project_id=1, question="질문", source_ids=[1], provider="ollama"
    )

    assert any("질의 로그" in message for message in caplog.messages)


@pytest.mark.asyncio
async def test_a_slow_database_does_not_hold_the_answer(logging_enabled, monkeypatch) -> None:
    """예외를 삼키는 것만으로는 부족하다. 죽지 않고 느려지기만 하면 그 지연이 그대로
    답변 지연이 된다(rag_stats._increment_daily_counters 와 같은 이유)."""
    monkeypatch.setattr(query_log_service, "_WRITE_TIMEOUT_SECONDS", 0.01)
    conn = _FakeConn(delay=5)

    await asyncio.wait_for(
        record_query_log(
            _FakePool(conn), project_id=1, question="질문", source_ids=[], provider="ollama"
        ),
        timeout=1,
    )

    assert conn.calls == []


@pytest.mark.asyncio
async def test_logging_is_off_unless_the_switch_is_turned_on(monkeypatch) -> None:
    """되돌리는 1단계가 "스위치를 끈다"라, 스위치가 없으면 배포 없이는 멈출 수 없다.
    기본값을 꺼짐으로 두는 이유: 질문 원문을 남기는 기능이 설정 실수로 조용히 켜져 있는 것보다
    켜야 할 곳에서 안 켜져 있는 편이 낫다."""
    monkeypatch.delenv("ASSISTANT_QUERY_LOG_ENABLED", raising=False)
    conn = _FakeConn()

    await record_query_log(
        _FakePool(conn), project_id=1, question="질문", source_ids=[1], provider="ollama"
    )

    assert conn.calls == []


@pytest.mark.asyncio
async def test_the_switch_can_be_turned_off_without_a_deploy(monkeypatch) -> None:
    """모듈 로드 시점에 값을 굳히면 컨테이너를 다시 띄우기 전에는 끌 수 없다."""
    monkeypatch.setenv("ASSISTANT_QUERY_LOG_ENABLED", "true")
    conn = _FakeConn()
    await record_query_log(
        _FakePool(conn), project_id=1, question="질문", source_ids=[], provider="ollama"
    )
    assert len(conn.calls) == 1

    monkeypatch.setenv("ASSISTANT_QUERY_LOG_ENABLED", "false")
    await record_query_log(
        _FakePool(conn), project_id=1, question="질문", source_ids=[], provider="ollama"
    )
    assert len(conn.calls) == 1


@pytest.mark.asyncio
async def test_expired_rows_are_purged_even_while_logging_is_switched_off(monkeypatch) -> None:
    """보존기간은 트래픽에 기대면 안 되는 약속이다.

    쓰기 경로의 CTE 만으로는 스위치를 끄거나 질의가 뜸할 때 만료가 멈춘다. 일일 작업은
    스위치를 보지 않아야 하고, 이 테스트가 그것을 못박는다. 삭제 조건도 함께 고정한다 -
    보존일수가 조용히 바뀌면 개인정보 약속이 바뀌는 것이다.
    """
    monkeypatch.delenv("ASSISTANT_QUERY_LOG_ENABLED", raising=False)
    conn = _FakeConn()

    await purge_expired_rows(_FakePool(conn))

    assert len(conn.calls) == 1
    query = conn.calls[0][0]
    assert "DELETE FROM assistant_query_log" in query
    assert "90 days" in query


def test_masking_stays_linear_on_a_very_long_question() -> None:
    """마스킹은 동기 코드라 asyncio.wait_for 가 끊지 못한다. 정규식이 길이의 제곱에
    비례하면 긴 질문 한 건이 이벤트 루프를 통째로 세운다 - 상한이 아니라 정지다.

    입력을 2만자로 잡은 것은 의도적이다. 20만자로 잡으면 경계 검사를 지웠을 때 테스트가
    "실패"하는 대신 몇 분간 매달려, 깨진 것을 알려주는 대신 CI 를 세운다. 2만자면 고친
    쪽은 1ms 미만, 깨진 쪽은 1.5초 안팎이라 0.5초 상한이 둘을 확실히 가른다.
    절대 시간이 아니라 차수를 보는 테스트다.
    """
    long_question = "가" * 20_000

    started = time.perf_counter()
    mask_sensitive_text(long_question)

    assert time.perf_counter() - started < 0.5


@pytest.mark.asyncio
async def test_purge_is_skipped_quietly_when_the_table_does_not_exist() -> None:
    """이 작업은 기록 스위치와 무관하게 돈다. 마이그레이션이 적용되지 않은 환경
    (spring.flyway.enabled 기본값이 false)에서는 테이블 자체가 없으므로, 넘어가지 않으면
    기능을 켜지도 않은 곳이 매일 오류를 쌓는다."""
    conn = _FakeConn(table_exists=False)

    await purge_expired_rows(_FakePool(conn))

    assert conn.calls == []
