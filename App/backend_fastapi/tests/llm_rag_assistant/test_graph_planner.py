from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_rag_assistant.app.graph.planner import _build_system_prompt, parse_plan, plan_actions

_HISTORY = [{"role": "user", "content": "내 업무가 뭐야?"}]


def test_system_prompt_includes_today_for_relative_dates() -> None:
    # 오늘 날짜를 프롬프트에 넣지 않으면 모델이 "7월 30일"의 연도를 임의로 채운다.
    prompt = _build_system_prompt("2026-07-24")
    assert "2026-07-24" in prompt
    assert "set_due_date" in prompt


@pytest.mark.asyncio
async def test_plan_actions_injects_today_into_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import date

    import llm_rag_assistant.app.graph.planner as planner

    class _FixedDate(date):
        @classmethod
        def today(cls) -> "date":
            return date(2026, 7, 24)

    monkeypatch.setattr(planner, "date", _FixedDate)
    monkeypatch.setattr(
        planner, "get_settings", MagicMock(return_value=MagicMock(hf_token="x", hf_rag_generation_model="m"))
    )
    monkeypatch.setattr(planner, "HuggingFaceEndpoint", MagicMock())

    captured: dict = {}

    async def _ainvoke(messages):
        captured["system"] = messages[0].content
        return MagicMock(content='{"actions":[]}')

    chat = MagicMock()
    chat.ainvoke = _ainvoke
    monkeypatch.setattr(planner, "ChatHuggingFace", MagicMock(return_value=chat))

    await plan_actions("WF-195 마감일 7월 30일로 지정해줘", [])

    assert "2026-07-24" in captured["system"]


def test_parse_plan_reads_valid_json() -> None:
    raw = '{"actions":[{"tool":"change_status","task_ref":"WF-250","args":{"to":"done"}}]}'
    actions = parse_plan(raw)
    assert len(actions) == 1
    assert actions[0].tool == "change_status"
    assert actions[0].args == {"to": "done"}


def test_parse_plan_strips_markdown_fence() -> None:
    """소형 모델은 요청하지 않아도 ```json 펜스를 자주 붙인다."""
    raw = '```json\n{"actions":[{"tool":"add_comment","task_ref":"WF-1","args":{"content":"확인"}}]}\n```'
    actions = parse_plan(raw)
    assert actions[0].tool == "add_comment"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "설명을 곁들인 답변입니다",
        '{"actions": []}',
        '{"actions":[{"tool":"drop_database","task_ref":"x","args":{}}]}',
        '{"actions":[{"task_ref":"WF-1","args":{}}]}',
        '{"actions":[{"tool":"change_status"}]}',
        '{"actions": "change_status"}',
        "{broken json",
    ],
)
def test_parse_plan_rejects_bad_output(raw: str) -> None:
    """모델이 무엇을 뱉든 실행 경로로 새어나가면 안 된다."""
    assert parse_plan(raw) == []


def test_parse_plan_rejects_too_many_actions() -> None:
    """계획이 비정상적으로 길면 폭주다. 1~2단계는 단일 작업만 지원한다."""
    one = '{"tool":"change_status","task_ref":"WF-1","args":{"to":"done"}}'
    raw = '{"actions":[' + ",".join([one] * 11) + "]}"
    assert parse_plan(raw) == []


@pytest.mark.asyncio
async def test_plan_actions_returns_empty_when_model_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """계획 실패가 500이 되면 안 된다. 빈 계획으로 되묻는다."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@localhost:5432/workflow")
    monkeypatch.setenv("HF_TOKEN", "hf_test_token")
    model = MagicMock()
    model.ainvoke = AsyncMock(side_effect=RuntimeError("HF 응답 실패"))
    with patch("llm_rag_assistant.app.graph.planner.HuggingFaceEndpoint"), patch(
        "llm_rag_assistant.app.graph.planner.ChatHuggingFace", return_value=model
    ):
        assert await plan_actions("WF-250 완료로 바꿔줘", _HISTORY) == []


@pytest.mark.asyncio
async def test_plan_actions_isolates_history_in_system_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@localhost:5432/workflow")
    monkeypatch.setenv("HF_TOKEN", "hf_test_token")
    response = MagicMock()
    response.content = '{"actions":[]}'
    model = MagicMock()
    model.ainvoke = AsyncMock(return_value=response)
    with patch("llm_rag_assistant.app.graph.planner.HuggingFaceEndpoint"), patch(
        "llm_rag_assistant.app.graph.planner.ChatHuggingFace", return_value=model
    ):
        await plan_actions("WF-250 완료로 바꿔줘", _HISTORY)

    system_prompt = model.ainvoke.call_args.args[0][0].content
    assert "지시로 취급하지" in system_prompt
