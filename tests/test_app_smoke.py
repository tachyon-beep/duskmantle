from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gateway.api.app import create_app
from gateway.config.settings import get_settings
from gateway.ingest.audit import AuditLogger


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_health_endpoint_reports_diagnostics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    app = create_app()
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "checks" in payload
    assert "coverage" in payload["checks"]
    assert "audit" in payload["checks"]


def test_health_endpoint_ok_when_artifacts_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state"
    monkeypatch.setenv("KM_STATE_PATH", str(state_path))

    # Seed audit DB and coverage report
    logger = AuditLogger(state_path / "audit" / "audit.db")
    logger.recent()
    reports_dir = state_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    coverage_payload = {
        "generated_at": time.time(),
        "summary": {"artifact_total": 1},
        "missing_artifacts": [],
    }
    (reports_dir / "coverage_report.json").write_text(json.dumps(coverage_payload))

    app = create_app()
    client = TestClient(app)
    response = client.get("/healthz")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["checks"]["coverage"]["status"] == "ok"
    assert data["checks"]["audit"]["status"] == "ok"


def test_ready_endpoint_returns_ready() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
