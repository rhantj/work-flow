from __future__ import annotations

import os
from unittest.mock import patch

from ml_workload_score.app.services.tracing import setup_langsmith


def test_setup_langsmith_returns_false_without_api_key(monkeypatch):
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)

    with patch(
        "ml_workload_score.app.services.tracing.dotenv_values",
        return_value={},
    ):
        result = setup_langsmith()

    assert result is False
    assert "LANGSMITH_TRACING" not in os.environ


def test_setup_langsmith_clears_preexisting_tracing_flag_without_api_key(monkeypatch):
    """docker-compose가 LANGSMITH_TRACING=${LANGSMITH_TRACING:-false}로 프로세스에
    이미 "true"를 주입해 놓은 상태에서 API 키만 빠지면, 반환값(False)과 실제
    환경변수 상태가 어긋나지 않도록 LANGSMITH_TRACING을 지워야 한다(리뷰 지적사항)."""
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)

    with patch(
        "ml_workload_score.app.services.tracing.dotenv_values",
        return_value={},
    ):
        result = setup_langsmith()

    assert result is False
    assert "LANGSMITH_TRACING" not in os.environ


def test_setup_langsmith_enables_tracing_with_default_project(monkeypatch):
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)

    with patch(
        "ml_workload_score.app.services.tracing.dotenv_values",
        return_value={},
    ):
        result = setup_langsmith()

    assert result is True
    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_PROJECT"] == "workflow-workload-score"


def test_setup_langsmith_respects_custom_project_name(monkeypatch):
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)

    with patch(
        "ml_workload_score.app.services.tracing.dotenv_values",
        return_value={},
    ):
        result = setup_langsmith(project_name="custom-project")

    assert result is True
    assert os.environ["LANGSMITH_PROJECT"] == "custom-project"
