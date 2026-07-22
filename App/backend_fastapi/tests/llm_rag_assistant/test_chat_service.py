from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from llm_rag_assistant.app.services.chat_service import answer_question


@pytest.mark.asyncio
async def test_answer_question_returns_answer_with_sources() -> None:
    pool = object()
    rows = [
        {"source_type": "meeting", "source_id": 1, "content": "회의록 상세 내용" * 30, "similarity": 0.87},
    ]

    with (
        patch(
            "llm_rag_assistant.app.services.chat_service.embed_text",
            new=AsyncMock(return_value=[0.1, 0.2]),
        ),
        patch(
            "llm_rag_assistant.app.services.chat_service.search_similar_chunks",
            new=AsyncMock(return_value=rows),
        ) as mock_search,
        patch(
            "llm_rag_assistant.app.services.chat_service.generate_answer",
            new=AsyncMock(return_value="이것이 답변입니다"),
        ),
    ):
        result = await answer_question(pool, project_id=5, question="질문")

    mock_search.assert_awaited_once_with(pool, 5, [0.1, 0.2], top_k=5, assignee_id=None)
    assert result.answer == "이것이 답변입니다"
    assert len(result.sources) == 1
    assert result.sources[0].source_type == "meeting"
    assert result.sources[0].source_id == 1
    assert len(result.sources[0].content_snippet) <= 200
    assert result.sources[0].similarity == 0.87


@pytest.mark.asyncio
async def test_answer_question_handles_no_matching_chunks() -> None:
    pool = object()

    with (
        patch(
            "llm_rag_assistant.app.services.chat_service.embed_text",
            new=AsyncMock(return_value=[0.1]),
        ),
        patch(
            "llm_rag_assistant.app.services.chat_service.search_similar_chunks",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "llm_rag_assistant.app.services.chat_service.generate_answer",
            new=AsyncMock(return_value="근거 없음: 관련 자료를 찾지 못했습니다"),
        ),
    ):
        result = await answer_question(pool, project_id=5, question="관련 없는 질문")

    assert result.sources == []
    assert "근거 없음" in result.answer


@pytest.mark.asyncio
async def test_answer_question_filters_by_assignee_when_personal_intent_and_user_id_given() -> None:
    pool = object()
    rows = [{"source_type": "task", "source_id": 3, "content": "내 업무", "similarity": 0.9}]

    with (
        patch(
            "llm_rag_assistant.app.services.chat_service.embed_text",
            new=AsyncMock(return_value=[0.1]),
        ),
        patch(
            "llm_rag_assistant.app.services.chat_service.search_similar_chunks",
            new=AsyncMock(return_value=rows),
        ) as mock_search,
        patch(
            "llm_rag_assistant.app.services.chat_service.generate_answer",
            new=AsyncMock(return_value="답변"),
        ),
    ):
        await answer_question(pool, project_id=5, question="내가 담당한 업무 알려줘", user_id=42)

    mock_search.assert_awaited_once_with(pool, 5, [0.1], top_k=5, assignee_id=42)


@pytest.mark.asyncio
async def test_answer_question_does_not_filter_by_assignee_for_non_personal_question() -> None:
    pool = object()

    with (
        patch(
            "llm_rag_assistant.app.services.chat_service.embed_text",
            new=AsyncMock(return_value=[0.1]),
        ),
        patch(
            "llm_rag_assistant.app.services.chat_service.search_similar_chunks",
            new=AsyncMock(return_value=[]),
        ) as mock_search,
        patch(
            "llm_rag_assistant.app.services.chat_service.generate_answer",
            new=AsyncMock(return_value="답변"),
        ),
    ):
        await answer_question(pool, project_id=5, question="프로젝트 전체 업무 현황 알려줘", user_id=42)

    mock_search.assert_awaited_once_with(pool, 5, [0.1], top_k=5, assignee_id=None)
