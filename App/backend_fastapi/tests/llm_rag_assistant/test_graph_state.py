from __future__ import annotations

import pytest
from pydantic import ValidationError

from llm_rag_assistant.app.graph.state import (
    LEADER_TOOLS,
    MEMBER_TOOLS,
    Action,
    requires_leader,
)


def test_action_accepts_known_tool() -> None:
    action = Action(tool="change_status", task_ref="WF-250", args={"to": "done"})
    assert action.tool == "change_status"


def test_action_rejects_unknown_tool() -> None:
    """모델이 만들어낸 도구 이름이 실행 경로로 새어나가면 안 된다."""
    with pytest.raises(ValidationError):
        Action(tool="drop_database", task_ref="WF-250", args={})


def test_member_and_leader_tool_sets_are_disjoint() -> None:
    assert MEMBER_TOOLS.isdisjoint(LEADER_TOOLS)


def test_requires_leader_flags_only_leader_tools() -> None:
    assert requires_leader("delete_task") is True
    assert requires_leader("set_due_date") is True
    assert requires_leader("add_comment") is False
    assert requires_leader("change_status") is False
