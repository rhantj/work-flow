from __future__ import annotations

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from requests.exceptions import HTTPError as RequestsHTTPError

from core.db import get_pool
from llm_rag_assistant.app.schema.assistant_schema import (
    AssistantCommandRequest,
    AssistantResponse,
)
from llm_rag_assistant.app.security import verify_internal_api_key
from llm_rag_assistant.app.services.chat_service import answer_question
from llm_rag_assistant.app.services.command_classifier import is_command_candidate
from llm_rag_assistant.app.services.generation_service import RagConfigurationError

router = APIRouter(prefix="/ai/assistant", tags=["assistant"], dependencies=[Depends(verify_internal_api_key)])

# 2단계에서 그래프가 붙기 전까지의 안내. 명령을 인식했다는 사실 자체는 알려줘야
# 사용자가 "왜 무시당했지"라고 느끼지 않는다.
_COMMAND_NOT_READY_NOTE = (
    "\n\n(업무를 직접 변경하는 기능은 아직 준비 중입니다. 지금은 업무 보드에서 직접 수정해주세요.)"
)


@router.post("/command", response_model=AssistantResponse)
async def command(request: AssistantCommandRequest, pool=Depends(get_pool)) -> AssistantResponse:
    # project_id/user_id/user_role은 Spring AssistantController가 인증 세션 값으로 덮어써서 보낸다.
    # 대화 기록(history)에서는 어떤 권한값도 유도하지 않는다.
    # RAG 호출은 분류기 판정 바깥에 둔다. 분류기가 질문을 명령으로 오탐해도 답변은
    # 그대로 나오고 안내 문구만 덧붙으므로, 규칙의 정확도가 기존 질문 기능의
    # 가용성을 좌우하지 않는다.
    history = [{"role": m.role, "content": m.content} for m in request.history]
    try:
        result = await answer_question(
            pool, request.project_id, request.question, request.user_id, history=history
        )
    except (aiohttp.ClientError, RequestsHTTPError) as exc:
        raise HTTPException(status_code=503, detail={"error": "llm_unavailable"}) from exc
    except RagConfigurationError as exc:
        raise HTTPException(status_code=503, detail={"error": "llm_unavailable"}) from exc
    message = result.answer
    if is_command_candidate(request.question):
        message += _COMMAND_NOT_READY_NOTE
    return AssistantResponse(type="answer", message=message, sources=result.sources)
