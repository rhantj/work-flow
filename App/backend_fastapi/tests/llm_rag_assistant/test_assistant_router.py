from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from core.db import get_pool
from llm_rag_assistant.app.schema.chat_schema import RagQueryResponse, RagSource
from llm_rag_assistant.app.security import verify_internal_api_key


def _override_pool():
    async def _fake_pool():
        yield object()

    app.dependency_overrides[get_pool] = _fake_pool
    app.dependency_overrides[verify_internal_api_key] = lambda: None


def _body(question: str, **extra) -> dict:
    payload = {"project_id": 1, "question": question, "user_id": 2, "user_role": "MEMBER", "history": []}
    payload.update(extra)
    return payload


def test_question_goes_through_existing_rag_pipeline() -> None:
    _override_pool()
    fake = RagQueryResponse(
        answer="담당 업무는 3건입니다",
        sources=[RagSource(source_type="task", source_id=37, content_snippet="요약", similarity=0.9)],
    )
    with patch(
        "llm_rag_assistant.app.routers.assistant_router.answer_question",
        new=AsyncMock(return_value=fake),
    ) as mock_answer:
        client = TestClient(app)
        response = client.post("/ai/assistant/command", json=_body("내 업무가 뭐야?"))

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "answer"
    assert body["message"] == "담당 업무는 3건입니다"
    assert body["sources"][0]["source_id"] == 37
    mock_answer.assert_awaited_once()


def test_question_path_receives_history_as_dicts() -> None:
    """query_rewrite_service._format_history가 turn.get()을 쓰므로 dict여야 한다."""
    _override_pool()
    history = [
        {"role": "user", "content": "내 업무가 뭐야?"},
        {"role": "assistant", "content": "로그인 API 구현이 있습니다"},
    ]
    with patch(
        "llm_rag_assistant.app.routers.assistant_router.answer_question",
        new=AsyncMock(return_value=RagQueryResponse(answer="답변", sources=[])),
    ) as mock_answer:
        client = TestClient(app)
        client.post("/ai/assistant/command", json=_body("그 업무 언제까지야?", history=history))

    app.dependency_overrides.clear()
    passed = mock_answer.await_args.kwargs["history"]
    assert passed == history
    assert all(isinstance(turn, dict) for turn in passed)


def test_command_candidate_still_gets_rag_answer_with_note() -> None:
    """명령으로 분류돼도 RAG 답변은 그대로 나와야 한다.

    분류기가 질문을 오탐했을 때 답변이 통째로 사라지면 기존 질문 기능이 회귀한다.
    """
    _override_pool()
    with patch(
        "llm_rag_assistant.app.routers.assistant_router.answer_question",
        new=AsyncMock(return_value=RagQueryResponse(answer="답변", sources=[])),
    ) as mock_answer:
        client = TestClient(app)
        response = client.post("/ai/assistant/command", json=_body("WF-250 완료로 바꿔줘"))

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["type"] == "answer"
    mock_answer.assert_awaited_once()
    assert response.json()["message"].startswith("답변")
    assert "준비 중" in response.json()["message"]


def test_question_answer_has_no_command_note() -> None:
    _override_pool()
    with patch(
        "llm_rag_assistant.app.routers.assistant_router.answer_question",
        new=AsyncMock(return_value=RagQueryResponse(answer="답변", sources=[])),
    ):
        client = TestClient(app)
        response = client.post("/ai/assistant/command", json=_body("완료된 업무 목록 좀 줘"))

    app.dependency_overrides.clear()
    assert response.json()["message"] == "답변"


def test_invalid_user_role_is_rejected() -> None:
    _override_pool()
    client = TestClient(app)
    response = client.post("/ai/assistant/command", json=_body("질문", user_role="SUPERUSER"))
    app.dependency_overrides.clear()
    assert response.status_code == 422
