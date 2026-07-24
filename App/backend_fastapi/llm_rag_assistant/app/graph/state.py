from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

# 도구 목록을 한 곳에서만 정의한다. 계획 노드의 허용 목록, 권한 판정, 프론트 실행기 매핑이
# 서로 어긋나면 "카드는 떴는데 실행이 안 되는" 상태가 되므로 여기가 유일한 기준이다.
MEMBER_TOOLS: frozenset[str] = frozenset({"change_status", "add_comment", "toggle_checklist"})
LEADER_TOOLS: frozenset[str] = frozenset({"rename_task", "set_due_date", "change_assignee", "delete_task"})
ALL_TOOLS: frozenset[str] = MEMBER_TOOLS | LEADER_TOOLS

ToolName = Literal[
    "change_status",
    "add_comment",
    "toggle_checklist",
    "rename_task",
    "set_due_date",
    "change_assignee",
    "delete_task",
]


def requires_leader(tool: str) -> bool:
    return tool in LEADER_TOOLS


class Action(BaseModel):
    """계획 노드가 만든 작업 하나. Literal 덕분에 모르는 도구 이름은 파싱 단계에서 거부된다."""

    tool: ToolName
    # "WF-250" 또는 "로그인 업무" - 아직 실제 id가 아니다. task_resolver가 변환한다.
    task_ref: str
    args: dict[str, Any] = Field(default_factory=dict)


class CommandState(TypedDict, total=False):
    question: str
    history: list[dict]
    # 아래 3개는 Spring이 인증 세션에서 주입한 값이다. 대화 기록에서 유도하지 않는다.
    project_id: int
    user_id: int | None
    user_role: str
    plan: list[dict]      # Action.model_dump() 목록 (체크포인터 직렬화를 위해 dict로 보관)
    cursor: int
    results: list[dict]
    final_message: str
