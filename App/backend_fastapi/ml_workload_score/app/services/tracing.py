from __future__ import annotations

import logging
import os

from dotenv import dotenv_values

logger = logging.getLogger(__name__)


def setup_langsmith(project_name: str = "workflow-workload-score") -> bool:
    """
    LangSmith 트레이싱 활성화.

    workload_db.py/embedding_difficulty.py와 동일한 패턴으로 dotenv_values()를 직접
    읽는다 - core.config.get_settings()는 이 dev 환경에서 App/.env를 못 찾아
    ValidationError가 나는 게 확인된 상태라 재사용하지 않는다.

    필요 환경변수:
      LANGSMITH_API_KEY - LangSmith API 키 (smith.langchain.com에서 발급)
      LANGSMITH_PROJECT - 대시보드에 표시될 프로젝트명 (선택, 없으면 project_name 사용)
    """
    env = {**dotenv_values(), **os.environ}
    api_key = env.get("LANGSMITH_API_KEY")

    if not api_key:
        logger.warning(
            "LANGSMITH_API_KEY 미설정 - 워크로드 스코어 트레이싱 비활성화 상태로 진행"
        )
        return False

    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = env.get("LANGSMITH_PROJECT", project_name)
    logger.info("LangSmith 트레이싱 활성화됨 (project=%s)", os.environ["LANGSMITH_PROJECT"])
    return True
