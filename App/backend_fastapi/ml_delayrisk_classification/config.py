"""ML 업무 지연 위험도 예측 모델(정상/주의/위험 3단계 분류) 설정.

환경변수는 DELAY_RISK_ 접두사로 오버라이드 가능 (예: DELAY_RISK_MONGO_URI).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

MODULE_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DELAY_RISK_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # MongoDB (Zenodo Apache Jira Issue Tracking Dataset)
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "ml_dashboard"
    issues_collection: str = "issues"
    events_collection: str = "events"
    comments_collection: str = "comments"
    worklogs_collection: str = "worklogs"

    # 학습 데이터 구성 (다중 스냅샷)
    snapshot_offsets_days: list[int] = [1, 3, 7, 14, 30]
    """이슈 생성 후 각 시점(일)마다 스냅샷을 떠서 그 순간의 위험도를 라벨링한다.
    이슈가 해당 시점 이전에 이미 종료됐다면 그 스냅샷은 건너뛴다."""
    min_duration_hours: float = 1.0
    """이보다 빨리 종료된 이슈(중복 처리 등 노이즈)는 마감일(Proxy Deadline) 산정용
    그룹 중앙값 계산에서 제외한다."""
    min_group_size_for_sla: int = 10
    """(issuetype, priority) 그룹별 Proxy Deadline(중앙값)을 신뢰하기 위한 최소 표본 수."""

    # 3단계 라벨링 임계값 (방법론 문서 기준)
    risk_blocked_ratio: float = 0.30
    """블로커류 상태 누적시간 / Proxy Deadline 비율이 이보다 크면 '위험'(장기간 정체)."""
    warning_blocked_ratio: float = 0.10
    """위 비율이 이보다 크면 '주의' (문서의 '전체 예상 시간의 10% 이하'는 정상 범위 기준)."""
    warning_imbalance_index: float = 0.30
    """진행률 불균형 지수(시간경과율-진행률)가 이보다 크면 '주의' (경과 대비 진행 저조)."""

    # 최근 활동 모멘텀
    recent_activity_window_days: int = 3
    """기한 임박 시 최근 N일간 활동(댓글/상태변경/작업기록)이 없으면 '위험' 전조로 본다."""

    # 모델 아티팩트
    model_dir: str = str(MODULE_ROOT / "models")
    model_filename: str = "delayrisk_model.pkl"

    # 시각화 자료(혼동행렬, 피처 중요도 등) 저장 위치 — 팀 문서 폴더에 모아 둔다.
    visualization_dir: str = r"D:\AIproject\project\Team\work-flow\document_유소은\view"


@lru_cache
def get_settings() -> Settings:
    return Settings()
