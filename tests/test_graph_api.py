from __future__ import annotations

from typing import Any

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from gateway.api.app import create_app
from gateway.graph import GraphNotFoundError


class DummyGraphService:
    def __init__(self, responses: dict[str, Any]):
        self._responses = responses
        self.last_node_id: str | None = None

    def get_subsystem(self, name: str, **kwargs: Any) -> dict[str, Any]:
        if name == "missing":
            raise GraphNotFoundError("Subsystem 'missing' not found")
        return self._responses["subsystem"]

    def get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:
        self.last_node_id = node_id
        if node_id == "Subsystem:missing":
            raise GraphNotFoundError("Node not found")
        return self._responses["node"]

    def search(self, term: str, *, limit: int) -> dict[str, Any]:
        return {"results": self._responses.get("search", [])}

    def run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:
        return {"data": [{"row": ["ok"]}], "summary": {"resultConsumedAfterMs": 1, "database": "knowledge"}}


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    dummy_service = DummyGraphService(
        {
            "subsystem": {
                "subsystem": {
                    "id": "Subsystem:telemetry",
                    "labels": ["Subsystem"],
                    "properties": {"name": "telemetry", "criticality": "high"},
                },
                "related": {
                    "nodes": [
                        {
                            "relationship": "DEPENDS_ON",
                            "direction": "OUT",
                            "target": {
                                "id": "Subsystem:analytics",
                                "labels": ["Subsystem"],
                                "properties": {"name": "analytics"},
                            },
                        }
                    ],
                    "cursor": None,
                },
                "artifacts": [
                    {
                        "id": "DesignDoc:docs/telemetry.md",
                        "labels": ["DesignDoc"],
                        "properties": {"path": "docs/telemetry.md"},
                    }
                ],
            },
            "node": {
                "node": {
                    "id": "Subsystem:telemetry",
                    "labels": ["Subsystem"],
                    "properties": {"name": "telemetry"},
                },
                "relationships": [
                    {
                        "type": "IMPLEMENTS",
                        "direction": "OUT",
                        "target": {
                            "id": "LeylineMessage:LeylineSync",
                            "labels": ["LeylineMessage"],
                            "properties": {"name": "LeylineSync"},
                        },
                    }
                ],
            },
            "search": [
                {"id": "Subsystem:telemetry", "label": "Subsystem", "score": 0.9, "snippet": "telemetry"}
            ],
        }
    )
    app.dependency_overrides[app.state.graph_service_dependency] = lambda: dummy_service
    app.state._dummy_graph_service = dummy_service
    return app


def test_graph_subsystem_returns_payload(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/subsystems/telemetry")
    assert response.status_code == 200
    body = response.json()
    assert body["subsystem"]["id"] == "Subsystem:telemetry"
    assert body["subsystem"]["properties"]["criticality"] == "high"
    assert body["related"]["nodes"][0]["relationship"] == "DEPENDS_ON"
    assert body["artifacts"][0]["id"].startswith("DesignDoc:")


def test_graph_subsystem_not_found(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/subsystems/missing")
    assert response.status_code == 404


def test_graph_node_endpoint(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/nodes/Subsystem:telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["node"]["id"] == "Subsystem:telemetry"
    assert data["relationships"][0]["type"] == "IMPLEMENTS"


def test_graph_node_accepts_slash_encoded_ids(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/nodes/DesignDoc%3Adocs%2Fdesign.md")
    assert response.status_code == 200
    service = app.state._dummy_graph_service
    assert service.last_node_id == "DesignDoc:docs/design.md"


def test_graph_search_endpoint(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/search", params={"q": "tele"})
    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == "Subsystem:telemetry"


def test_graph_cypher_requires_maintainer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    dummy_service = DummyGraphService({})
    app.dependency_overrides[app.state.graph_service_dependency] = lambda: dummy_service
    client = TestClient(app)

    # missing token -> unauthorized
    resp = client.post("/graph/cypher", json={"query": "MATCH (n) RETURN n LIMIT 1"})
    assert resp.status_code == 401

    # maintainer token -> success
    resp = client.post(
        "/graph/cypher",
        json={"query": "MATCH (n) RETURN n LIMIT 1"},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"][0]["row"] == ["ok"]


def test_graph_reader_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    app = create_app()
    dummy_service = DummyGraphService(
        {
            "subsystem": {
                "subsystem": {"id": "Subsystem:kasmina", "properties": {"name": "kasmina"}},
                "related": {"nodes": [], "cursor": None},
                "artifacts": [],
            },
            "node": {
                "node": {"id": "Subsystem:kasmina", "properties": {"name": "kasmina"}},
                "relationships": [],
            },
        }
    )
    app.dependency_overrides[app.state.graph_service_dependency] = lambda: dummy_service
    client = TestClient(app)

    assert client.get("/graph/subsystems/kasmina").status_code == 401
    assert client.get(
        "/graph/subsystems/kasmina",
        headers={"Authorization": "Bearer nope"},
    ).status_code == 403

    ok_reader = client.get(
        "/graph/subsystems/kasmina",
        headers={"Authorization": "Bearer reader-token"},
    )
    assert ok_reader.status_code == 200

    ok_admin = client.get(
        "/graph/subsystems/kasmina",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert ok_admin.status_code == 200
