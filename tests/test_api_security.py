from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gateway import get_version
from gateway.api.app import create_app
from gateway.api.constants import API_V1_PREFIX
from gateway.config.settings import get_settings
from gateway.graph.service import GraphService
from gateway.ingest.audit import AuditLogger
from gateway.ingest.pipeline import IngestionResult
from gateway.search.service import SearchResponse


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_audit_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state"
    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")

    app = create_app()
    client = TestClient(app)

    # Missing credentials
    resp = client.get(f"{API_V1_PREFIX}/audit/history")
    assert resp.status_code == 401

    # Wrong token
    resp = client.get(f"{API_V1_PREFIX}/audit/history", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 403

    # Correct maintainer token
    resp = client.get(
        f"{API_V1_PREFIX}/audit/history",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_audit_history_limit_clamped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state"
    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_AUDIT_HISTORY_MAX_LIMIT", "3")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")

    audit_logger = AuditLogger(state_path / "audit" / "audit.db")
    for idx in range(5):
        audit_logger.record(
            IngestionResult(
                run_id=f"run-{idx}",
                profile="local",
                started_at=float(idx),
                duration_seconds=1.0,
                artifact_counts={"docs": 1},
                chunk_count=idx,
                repo_head=f"sha-{idx}",
                success=True,
            )
        )

    app = create_app()
    client = TestClient(app)

    resp = client.get(
        f"{API_V1_PREFIX}/audit/history?limit=10",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 3
    assert resp.headers["X-KM-Audit-Limit"] == "3"
    assert "Warning" in resp.headers
    assert "exceeds cap" in resp.headers["Warning"]


def test_audit_history_limit_too_low_normalized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state"
    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")

    audit_logger = AuditLogger(state_path / "audit" / "audit.db")
    for idx in range(2):
        audit_logger.record(
            IngestionResult(
                run_id=f"low-{idx}",
                profile="local",
                started_at=float(idx),
                duration_seconds=1.0,
                artifact_counts={"docs": 1},
                chunk_count=idx,
                repo_head=f"sha-{idx}",
                success=True,
            )
        )

    app = create_app()
    client = TestClient(app)

    resp = client.get(
        f"{API_V1_PREFIX}/audit/history?limit=0",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 1
    assert resp.headers["X-KM-Audit-Limit"] == "1"
    warning_header = resp.headers.get("Warning")
    assert warning_header is not None and "below minimum" in warning_header


def test_coverage_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state"
    report_path = state_path / "reports"
    report_path.mkdir(parents=True)
    (report_path / "coverage_report.json").write_text(json.dumps({"summary": {"artifact_total": 2}}))

    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")

    app = create_app()
    client = TestClient(app)

    # Reject non-maintainer token
    resp = client.get(
        f"{API_V1_PREFIX}/coverage",
        headers={"Authorization": "Bearer reader-token"},
    )
    assert resp.status_code == 403

    resp = client.get(
        f"{API_V1_PREFIX}/coverage",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["summary"]["artifact_total"] == 2


def test_coverage_missing_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")

    app = create_app()
    client = TestClient(app)

    resp = client.get(
        f"{API_V1_PREFIX}/coverage",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Coverage report not found"


def test_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("KM_RATE_LIMIT_WINDOW", "60")

    app = create_app()
    client = TestClient(app)

    assert client.get("/metrics").status_code == 200
    resp = client.get("/metrics")
    assert resp.status_code == 429
    assert resp.json()["detail"] == "Rate limit exceeded"


def test_startup_logs_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))

    with caplog.at_level(logging.INFO):
        create_app()

    startup_records = [record for record in caplog.records if getattr(record, "event", "") == "startup_config"]
    assert startup_records, "expected startup_config log record"
    record = startup_records[-1]
    assert record.version == get_version()
    assert record.embedding_model
    assert record.text_embedding_model
    assert record.image_embedding_model
    assert isinstance(record.search_weights, dict)
    assert record.search_weight_profile


def test_secure_mode_without_admin_token_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "super-secure")
    monkeypatch.delenv("KM_ADMIN_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="KM_ADMIN_TOKEN"):
        create_app()


def test_secure_mode_requires_custom_neo4j_password(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "maintainer-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "neo4jadmin")

    with pytest.raises(RuntimeError, match="KM_NEO4J_PASSWORD"):
        create_app()


def test_rate_limiting_search(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KM_RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("KM_RATE_LIMIT_WINDOW", "60")
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    app = create_app()

    def _dummy_search_service() -> object:
        class _Dummy:
            def search(
                self,
                *,
                query: str,
                limit: int,
                include_graph: bool,
                graph_service: GraphService,
                sort_by_vector: bool = False,
                request_id: str | None = None,
                filters: dict[str, Any] | None = None,
            ) -> SearchResponse:
                metadata = {
                    "result_count": 0,
                    "graph_context_included": False,
                    "warnings": [],
                    "request_id": request_id,
                }
                if filters:
                    metadata["filters_applied"] = filters
                return SearchResponse(query=query, results=[], metadata=metadata)

        return _Dummy()

    app.dependency_overrides[app.state.search_service_dependency] = _dummy_search_service
    storage = getattr(app.state.limiter, "storage", None)
    if storage is not None and hasattr(storage, "clear"):
        storage.clear()
    client = TestClient(app)

    payload = {"query": "telemetry"}
    headers = {"X-Forwarded-For": "203.0.113.10"}
    assert client.post(f"{API_V1_PREFIX}/search", json=payload, headers=headers).status_code == 200
    resp = client.post(f"{API_V1_PREFIX}/search", json=payload, headers=headers)
    assert resp.status_code == 429
    assert resp.json()["detail"] == "Rate limit exceeded"
