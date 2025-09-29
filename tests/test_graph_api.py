from __future__ import annotations

from pathlib import Path
import os
from typing import Any

from neo4j import GraphDatabase

from gateway.graph.migrations.runner import MigrationRunner
from gateway.ingest.neo4j_writer import Neo4jWriter
from gateway.ingest.pipeline import IngestionConfig, IngestionPipeline

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

    def get_subsystem_graph(self, name: str, *, depth: int) -> dict[str, Any]:
        return self._responses["subsystem_graph"]

    def list_orphan_nodes(self, *, label: str | None, cursor: str | None, limit: int) -> dict[str, Any]:
        return self._responses["orphans"]

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
                            "hops": 1,
                            "path": [
                                {
                                    "type": "DEPENDS_ON",
                                    "direction": "OUT",
                                    "source": "Subsystem:telemetry",
                                    "target": "Subsystem:analytics",
                                }
                            ],
                        }
                    ],
                    "cursor": None,
                    "total": 1,
                },
                "artifacts": [
                    {
                        "id": "DesignDoc:docs/telemetry.md",
                        "labels": ["DesignDoc"],
                        "properties": {"path": "docs/telemetry.md"},
                    }
                ],
            },
            "subsystem_graph": {
                "subsystem": {
                    "id": "Subsystem:telemetry",
                    "labels": ["Subsystem"],
                    "properties": {"name": "telemetry", "criticality": "high"},
                },
                "nodes": [
                    {
                        "id": "Subsystem:telemetry",
                        "labels": ["Subsystem"],
                        "properties": {"name": "telemetry", "criticality": "high"},
                    },
                    {
                        "id": "Subsystem:analytics",
                        "labels": ["Subsystem"],
                        "properties": {"name": "analytics"},
                    },
                ],
                "edges": [
                    {
                        "type": "DEPENDS_ON",
                        "direction": "OUT",
                        "source": "Subsystem:telemetry",
                        "target": "Subsystem:analytics",
                    }
                ],
                "artifacts": [
                    {
                        "id": "DesignDoc:docs/telemetry.md",
                        "labels": ["DesignDoc"],
                        "properties": {"path": "docs/telemetry.md"},
                    }
                ],
            },
            "orphans": {
                "nodes": [
                    {
                        "id": "DesignDoc:docs/orphan.md",
                        "labels": ["DesignDoc"],
                        "properties": {"path": "docs/orphan.md"},
                    }
                ],
                "cursor": None,
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
                            "id": "IntegrationMessage:IntegrationSync",
                            "labels": ["IntegrationMessage"],
                            "properties": {"name": "IntegrationSync"},
                        },
                    }
                ],
            },
            "search": [{"id": "Subsystem:telemetry", "label": "Subsystem", "score": 0.9, "snippet": "telemetry"}],
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
    assert body["related"]["total"] == 1
    related_entry = body["related"]["nodes"][0]
    assert related_entry["relationship"] == "DEPENDS_ON"
    assert related_entry["path"][0]["target"] == "Subsystem:analytics"
    assert body["artifacts"][0]["id"].startswith("DesignDoc:")


def test_graph_subsystem_not_found(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/subsystems/missing")
    assert response.status_code == 404


def test_graph_subsystem_graph_endpoint(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/subsystems/telemetry/graph")
    assert response.status_code == 200
    data = response.json()
    assert any(edge["type"] == "DEPENDS_ON" for edge in data["edges"])
    assert data["nodes"][0]["id"] == "Subsystem:telemetry"


def test_graph_orphans_endpoint(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/orphans")
    assert response.status_code == 200
    payload = response.json()
    assert payload["nodes"][0]["id"] == "DesignDoc:docs/orphan.md"


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


@pytest.mark.neo4j
def test_graph_node_endpoint_live(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.PathLike[str]) -> None:
    uri = os.getenv("NEO4J_TEST_URI")
    user = os.getenv("NEO4J_TEST_USER", "neo4j")
    password = os.getenv("NEO4J_TEST_PASSWORD", "neo4jadmin")
    database = os.getenv("NEO4J_TEST_DATABASE", "knowledge")

    if not uri:
        pytest.skip("Set NEO4J_TEST_URI to run Neo4j integration tests")

    monkeypatch.setenv("KM_NEO4J_DATABASE", database)
    monkeypatch.setenv("KM_NEO4J_URI", uri)
    monkeypatch.setenv("KM_NEO4J_USER", user)
    monkeypatch.setenv("KM_NEO4J_PASSWORD", password)
    from gateway.config.settings import get_settings

    repo_root = Path(tmp_path) / "repo"
    (repo_root / "docs").mkdir(parents=True)
    doc_path = repo_root / "docs" / "sample.md"
    doc_path.write_text("# Sample\nGraph validation doc.\n")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        MigrationRunner(driver=driver, database=database).run()
        writer = Neo4jWriter(driver, database=database)
        writer.ensure_constraints()
        pipeline = IngestionPipeline(
            qdrant_writer=None,
            neo4j_writer=writer,
            config=IngestionConfig(
                repo_root=repo_root,
                dry_run=False,
                use_dummy_embeddings=True,
            ),
        )
        assert pipeline.run().success
    finally:
        driver.close()

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.get("/graph/nodes/DesignDoc%3Adocs%2Fsample.md")
    assert response.status_code == 200
    payload = response.json()
    assert payload["node"]["id"] == "DesignDoc:docs/sample.md"
    assert any(rel["type"] == "HAS_CHUNK" for rel in payload["relationships"])


@pytest.mark.neo4j
def test_graph_search_endpoint_live(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.PathLike[str]) -> None:
    uri = os.getenv("NEO4J_TEST_URI")
    user = os.getenv("NEO4J_TEST_USER", "neo4j")
    password = os.getenv("NEO4J_TEST_PASSWORD", "neo4jadmin")
    database = os.getenv("NEO4J_TEST_DATABASE", "knowledge")

    if not uri:
        pytest.skip("Set NEO4J_TEST_URI to run Neo4j integration tests")

    monkeypatch.setenv("KM_NEO4J_DATABASE", database)
    monkeypatch.setenv("KM_NEO4J_URI", uri)
    monkeypatch.setenv("KM_NEO4J_USER", user)
    monkeypatch.setenv("KM_NEO4J_PASSWORD", password)
    from gateway.config.settings import get_settings

    repo_root = Path(tmp_path) / "repo"
    (repo_root / "docs").mkdir(parents=True)
    (repo_root / "src" / "project" / "telemetry").mkdir(parents=True)
    (repo_root / "docs" / "sample.md").write_text("# Sample\nGraph validation doc.\n")
    (repo_root / "src" / "project" / "telemetry" / "module.py").write_text("def handler():\n    return 'ok'\n")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        MigrationRunner(driver=driver, database=database).run()
        writer = Neo4jWriter(driver, database=database)
        writer.ensure_constraints()
        pipeline = IngestionPipeline(
            qdrant_writer=None,
            neo4j_writer=writer,
            config=IngestionConfig(
                repo_root=repo_root,
                dry_run=False,
                use_dummy_embeddings=True,
            ),
        )
        assert pipeline.run().success
    finally:
        driver.close()

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.get("/graph/search", params={"q": "sample", "limit": 5})
    assert response.status_code == 200
    results = response.json()["results"]
    assert results, "expected graph search to return results"
    assert any(item["label"] == "DesignDoc" for item in results)


def test_graph_search_endpoint(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/graph/search", params={"q": "tele"})
    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == "Subsystem:telemetry"


def test_graph_cypher_requires_maintainer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "admin-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")
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
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "secure-pass")
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
    assert (
        client.get(
            "/graph/subsystems/kasmina",
            headers={"Authorization": "Bearer nope"},
        ).status_code
        == 403
    )

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
