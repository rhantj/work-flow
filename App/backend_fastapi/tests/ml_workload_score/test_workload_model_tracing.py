from __future__ import annotations

from ml_workload_score.app.services.workload_model import (
    build_features,
    detect_overload_anomalies_auto,
)


def test_build_features_name_preserved_after_traceable():
    assert build_features.__name__ == "build_features"


def test_detect_overload_anomalies_auto_name_preserved_after_traceable():
    assert detect_overload_anomalies_auto.__name__ == "detect_overload_anomalies_auto"
