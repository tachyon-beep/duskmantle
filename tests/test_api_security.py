from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gateway.api.app import create_app
from gateway.search.service import SearchResult, SearchResponse
from gateway.config.settings import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_audit_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")

    app = create_app()
    client = TestClient(app)

    # Missing credentials
    resp = client.get("/audit/history")
    assert resp.status_code == 401

    # Wrong token
    resp = client.get("/audit/history", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 403

    # Correct maintainer token
    resp = client.get(
        "/audit/history",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_coverage_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state"
    report_path = state_path / "reports"
    report_path.mkdir(parents=True)
    (report_path / "coverage_report.json").write_text(
        json.dumps({"summary": {"artifact_total": 2}})
    )

    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")

    app = create_app()
    client = TestClient(app)

    # Reject non-maintainer token
    resp = client.get(
        "/coverage",
        headers={"Authorization": "Bearer reader-token"},
    )
    assert resp.status_code == 403

    resp = client.get(
        "/coverage",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["summary"]["artifact_total"] == 2


def test_coverage_missing_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")

    app = create_app()
    client = TestClient(app)

    resp = client.get(
        "/coverage",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Coverage report not found"

def test_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("KM_RATE_LIMIT_WINDOW", "60")

    app = create_app()
    client = TestClient(app)

    assert client.get("/metrics").status_code == 200
    assert client.get("/metrics").status_code == 200
    resp = client.get("/metrics")
    assert resp.status_code == 429
    assert resp.json()["detail"] == "Rate limit exceeded"


def test_rate_limiting_search(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KM_RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("KM_RATE_LIMIT_WINDOW", "60")
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    app = create_app()
    def _dummy_search_service():
        class _Dummy:
            def search(
                self,
                *,
                query: str,
                limit: int,
                include_graph: bool,
                graph_service,
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
    client = TestClient(app)

    payload = {"query": "telemetry"}
    assert client.post("/search", json=payload).status_code == 200
    assert client.post("/search", json=payload).status_code == 200
    resp = client.post("/search", json=payload)
    assert resp.status_code == 429
    assert resp.json()["detail"] == "Rate limit exceeded"
