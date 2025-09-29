from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient

from gateway.api.app import create_app
from gateway.search.service import SearchResult, SearchResponse


class DummySearchService:
    def __init__(self) -> None:
        self.last_filters: dict[str, Any] | None = None

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
    ):
        self.last_filters = filters or {}
        return SearchResponse(
            query=query,
            results=[
                SearchResult(
                    chunk={
                        "chunk_id": "path::0",
                        "artifact_path": "src/module.py",
                        "artifact_type": "code",
                        "subsystem": "core",
                        "text": "snippet",
                        "score": 0.9,
                    },
                    graph_context={"primary_node": {"id": "SourceFile:src/module.py"}},
                    scoring={
                        "vector_score": 0.9,
                        "adjusted_score": 0.95,
                        "signals": {"subsystem_affinity": 1.0},
                    },
                )
            ],
            metadata={
                "result_count": 1,
                "graph_context_included": include_graph,
                "warnings": [],
                "scoring_mode": "heuristic",
            },
        )


def test_search_endpoint_returns_results(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    service = DummySearchService()
    app.dependency_overrides[app.state.search_service_dependency] = lambda: service
    client = TestClient(app)

    resp = client.post("/search", json={"query": "telemetry"})
    assert resp.status_code == 200
    request_id_header = resp.headers.get("x-request-id")
    assert request_id_header
    data = resp.json()
    assert data["results"][0]["chunk"]["artifact_path"] == "src/module.py"
    assert "scoring" in data["results"][0]
    assert data["results"][0]["graph_context"]["primary_node"]["id"] == "SourceFile:src/module.py"
    assert data["results"][0]["scoring"]["signals"]["subsystem_affinity"] == 1.0
    assert data["metadata"]["scoring_mode"] == "heuristic"
    assert data["metadata"]["request_id"] == request_id_header


def test_search_reuses_incoming_request_id(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    service = DummySearchService()
    app.dependency_overrides[app.state.search_service_dependency] = lambda: service
    client = TestClient(app)

    custom_request_id = "test-request-123"
    resp = client.post(
        "/search",
        json={"query": "telemetry"},
        headers={"X-Request-ID": custom_request_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert resp.headers.get("x-request-id") == custom_request_id
    assert data["metadata"]["request_id"] == custom_request_id


def test_search_requires_reader_token(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    service = DummySearchService()
    app.dependency_overrides[app.state.search_service_dependency] = lambda: service
    client = TestClient(app)

    resp = client.post("/search", json={"query": "telemetry"})
    assert resp.status_code == 401

    resp = client.post(
        "/search",
        json={"query": "telemetry"},
        headers={"Authorization": "Bearer reader-token"},
    )
    assert resp.status_code == 200


def test_search_allows_maintainer_token(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    service = DummySearchService()
    app.dependency_overrides[app.state.search_service_dependency] = lambda: service
    client = TestClient(app)

    resp = client.post(
        "/search",
        json={"query": "telemetry"},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200


def test_search_feedback_logged(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    service = DummySearchService()
    app.dependency_overrides[app.state.search_service_dependency] = lambda: service
    client = TestClient(app)

    resp = client.post(
        "/search",
        json={
            "query": "telemetry",
            "feedback": {"vote": 4, "note": "useful"},
            "context": {"task": "deep-dive"},
        },
    )
    assert resp.status_code == 200

    events_path = tmp_path / "feedback" / "events.log"
    assert events_path.exists()
    rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    assert rows
    row = rows[0]
    assert row["feedback_vote"] == 4.0
    assert row["context"] == {"task": "deep-dive"}
    assert row["artifact_path"] == "src/module.py"
    assert row["request_id"] == resp.json()["metadata"]["request_id"]


def test_search_filters_passed_to_service(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    service = DummySearchService()
    app.dependency_overrides[app.state.search_service_dependency] = lambda: service
    client = TestClient(app)

    resp = client.post(
        "/search",
        json={
            "query": "telemetry",
            "filters": {
                "subsystems": ["Telemetry", "Analytics "],
                "artifact_types": ["code", "doc"],
                "namespaces": ["src", "docs"],
                "tags": ["IntegrationAlpha", "telemetrySignal"],
                "updated_after": "2024-01-01T00:00:00Z",
                "max_age_days": 14,
            },
        },
    )
    assert resp.status_code == 200
    assert service.last_filters is not None
    filters = service.last_filters
    assert filters["subsystems"] == ["Telemetry", "Analytics"]
    assert filters["artifact_types"] == ["code", "doc"]
    assert filters["namespaces"] == ["src", "docs"]
    assert filters["tags"] == ["IntegrationAlpha", "telemetrySignal"]
    assert isinstance(filters["updated_after"], datetime)
    assert filters["updated_after"].tzinfo is not None
    assert filters["max_age_days"] == 14


def test_search_filters_invalid_type(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    resp = client.post(
        "/search",
        json={
            "query": "telemetry",
            "filters": {"artifact_types": ["invalid"]},
        },
    )
    assert resp.status_code == 422


def test_search_filters_invalid_namespaces(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    resp = client.post(
        "/search",
        json={
            "query": "telemetry",
            "filters": {"namespaces": "src"},
        },
    )
    assert resp.status_code == 422


def test_search_filters_invalid_updated_after(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    resp = client.post(
        "/search",
        json={
            "query": "telemetry",
            "filters": {"updated_after": "not-a-date"},
        },
    )
    assert resp.status_code == 422


def test_search_filters_invalid_max_age(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    resp = client.post(
        "/search",
        json={
            "query": "telemetry",
            "filters": {"max_age_days": 0},
        },
    )
    assert resp.status_code == 422


def test_search_weights_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "maintainer-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))

    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    resp = client.get("/search/weights")
    assert resp.status_code == 401

    resp = client.get(
        "/search/weights",
        headers={"Authorization": "Bearer maintainer-token"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert "profile" in payload
    assert "weights" in payload
    assert "weight_criticality" in payload["weights"]
