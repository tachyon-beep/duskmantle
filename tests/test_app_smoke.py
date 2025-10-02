from __future__ import annotations

import json
import time
import logging
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from gateway.api.app import create_app
from gateway.api.connections import DependencyStatus
from gateway.config.settings import get_settings
from gateway.ingest.audit import AuditLogger



@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _stub_connection_managers(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubNeo4jManager:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401
            self.revision = 0

        def get_write_driver(self) -> mock.Mock:
            return mock.Mock()

        def get_readonly_driver(self) -> mock.Mock:
            return mock.Mock()

        def mark_failure(self, exc: Exception | None = None) -> None:  # pragma: no cover - unused
            self.revision += 1

        def heartbeat(self) -> bool:  # pragma: no cover - unused
            return True

        def describe(self) -> DependencyStatus:  # pragma: no cover - unused
            return DependencyStatus("ok", self.revision, None, None, None)

    class StubQdrantManager:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401
            self.revision = 0

        def get_client(self) -> mock.Mock:
            return mock.Mock()

        def mark_failure(self, exc: Exception | None = None) -> None:  # pragma: no cover - unused
            self.revision += 1

        def heartbeat(self) -> bool:  # pragma: no cover - unused
            return True

        def describe(self) -> DependencyStatus:  # pragma: no cover - unused
            return DependencyStatus("ok", self.revision, None, None, None)

    monkeypatch.setattr("gateway.api.app.Neo4jConnectionManager", StubNeo4jManager)
    monkeypatch.setattr("gateway.api.app.QdrantConnectionManager", StubQdrantManager)


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
    assert "graph" in payload["checks"]
    assert "qdrant" in payload["checks"]
    graph_check = payload["checks"]["graph"]
    assert "status" in graph_check
    assert "revision" in graph_check


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
    assert data["status"] in {"ok", "degraded"}
    assert data["checks"]["coverage"]["status"] == "ok"
    assert data["checks"]["audit"]["status"] == "ok"


def test_ready_endpoint_returns_ready() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_lifecycle_history_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state"
    history_dir = state_path / "reports" / "lifecycle_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    sample_payload = {
        "generated_at": time.time(),
        "generated_at_iso": "2025-01-01T00:00:00Z",
        "stale_docs": [{"path": "docs/foo.md", "subsystem": "Kasmina", "git_timestamp": time.time() - 86400}],
        "isolated": {"DesignDoc": [{"id": "DesignDoc:docs/orphan.md", "properties": {"path": "docs/orphan.md"}}]},
        "missing_tests": [{"subsystem": "Kasmina", "source_files": 2, "test_cases": 0}],
        "removed_artifacts": [{"path": "docs/removed.md"}],
    }
    (history_dir / "lifecycle_20240101T000000000000.json").write_text(json.dumps(sample_payload))

    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    monkeypatch.setenv("KM_LIFECYCLE_HISTORY_LIMIT", "5")

    app = create_app()
    client = TestClient(app)

    response = client.get("/lifecycle/history?limit=5")
    assert response.status_code == 200
    payload = response.json()
    assert payload["history"]
    entry = payload["history"][0]
    assert entry["counts"]["stale_docs"] == 1
    assert entry["counts"]["isolated_nodes"] == 1
    assert entry["counts"]["removed_artifacts"] == 1


def test_requires_non_default_neo4j_password_when_auth_enabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "maintainer-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "neo4jadmin")
    monkeypatch.delenv("KM_NEO4J_AUTH_ENABLED", raising=False)

    _stub_connection_managers(monkeypatch)

    with pytest.raises(RuntimeError) as excinfo:
        create_app()

    assert "KM_NEO4J_PASSWORD" in str(excinfo.value)


def test_requires_non_empty_neo4j_password_when_auth_enabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "maintainer-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "")
    monkeypatch.delenv("KM_NEO4J_AUTH_ENABLED", raising=False)

    _stub_connection_managers(monkeypatch)

    with pytest.raises(RuntimeError) as excinfo:
        create_app()

    assert "KM_NEO4J_PASSWORD" in str(excinfo.value)


def test_logs_warning_when_neo4j_auth_disabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_NEO4J_AUTH_ENABLED", "false")
    monkeypatch.delenv("KM_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("KM_ADMIN_TOKEN", raising=False)

    _stub_connection_managers(monkeypatch)

    caplog.set_level(logging.WARNING, logger="gateway.api.app")
    app = create_app()
    assert app is not None
    assert any(
        "Neo4j authentication disabled" in record.getMessage()
        for record in caplog.records
    )
