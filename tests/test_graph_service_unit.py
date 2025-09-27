from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Iterable

import pytest

from gateway.graph import service as graph_service
from gateway.graph.service import (
    GraphNotFoundError,
    GraphQueryError,
    GraphService,
)


class DummyNode(dict):
    def __init__(self, labels: Iterable[str], element_id: str, **props: Any) -> None:
        super().__init__(props)
        self.labels = frozenset(labels)
        self.element_id = element_id


class DummyRelationship(dict):
    def __init__(
        self,
        start_node: DummyNode,
        end_node: DummyNode,
        rel_type: str,
        **props: Any,
    ) -> None:
        super().__init__(props)
        self.start_node = start_node
        self.end_node = end_node
        self.type = rel_type


class DummySession:
    def __init__(self) -> None:
        self.run_calls: list[tuple[str, dict[str, Any]]] = []
        self.run_result = SimpleNamespace(
            single=lambda: None,
        )

    def __enter__(self) -> "DummySession":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None

    def execute_read(self, func, *args: Any, **kwargs: Any) -> Any:
        return func(None, *args, **kwargs)

    def run(self, query: str, **params: Any):
        self.run_calls.append((query, params))
        return self.run_result


class DummyDriver:
    def __init__(self, session: DummySession) -> None:
        self._session = session
        self.last_execute_query: tuple[str, dict[str, Any], str] | None = None
        self.execute_query_result = SimpleNamespace(
            records=[],
            summary=SimpleNamespace(result_available_after=None, database=None),
        )

    def session(self, **kwargs: Any) -> DummySession:
        return self._session

    def execute_query(self, query: str, parameters: dict[str, Any], database_: str):
        self.last_execute_query = (query, parameters, database_)
        return self.execute_query_result


@pytest.fixture(autouse=True)
def patch_graph_types(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(graph_service, "Node", DummyNode)
    monkeypatch.setattr(graph_service, "Relationship", DummyRelationship)


@pytest.fixture
def dummy_driver() -> tuple[GraphService, DummySession, DummyDriver]:
    session = DummySession()
    driver = DummyDriver(session)
    service = GraphService(driver=driver, database="knowledge")
    return service, session, driver


def test_get_subsystem_paginates_and_includes_artifacts(monkeypatch: pytest.MonkeyPatch, dummy_driver):
    service, session, _ = dummy_driver

    subsystem = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina", description="Analysis")
    related_node = DummyNode(["DesignDoc"], "DesignDoc:docs/design.md", path="docs/design.md")
    relationship = DummyRelationship(subsystem, related_node, "DESCRIBES")
    artifact_node = DummyNode(["SourceFile"], "SourceFile:gateway/api.py", path="gateway/api.py")

    def fake_fetch_subsystem_node(tx, name: str):
        assert name == "Kasmina"
        return subsystem

    def fake_fetch_related_nodes(tx, name: str, depth: int, skip: int, limit: int):
        assert (depth, skip, limit) == (2, 0, 1)
        return [{"relationship": relationship, "node": related_node}]

    def fake_fetch_artifacts(tx, name: str):
        return [{"artifact": artifact_node}]

    monkeypatch.setattr(graph_service, "_fetch_subsystem_node", fake_fetch_subsystem_node)
    monkeypatch.setattr(graph_service, "_fetch_related_nodes", fake_fetch_related_nodes)
    monkeypatch.setattr(graph_service, "_fetch_artifacts_for_subsystem", fake_fetch_artifacts)

    result = service.get_subsystem(
        "Kasmina",
        depth=2,
        limit=1,
        cursor=None,
        include_artifacts=True,
    )

    assert result["subsystem"]["properties"]["name"] == "Kasmina"
    assert result["related"]["nodes"][0]["relationship"] == "DESCRIBES"
    assert result["related"]["cursor"] is not None  # limit reached -> pagination cursor emitted
    assert result["artifacts"][0]["properties"]["path"] == "gateway/api.py"


def test_get_subsystem_missing_raises(monkeypatch: pytest.MonkeyPatch, dummy_driver):
    service, _, _ = dummy_driver

    def fake_fetch_subsystem_node(tx, name: str):
        return None

    monkeypatch.setattr(graph_service, "_fetch_subsystem_node", fake_fetch_subsystem_node)

    with pytest.raises(GraphNotFoundError):
        service.get_subsystem("Unknown", depth=1, limit=5, cursor=None, include_artifacts=False)


def test_get_node_with_relationships(monkeypatch: pytest.MonkeyPatch, dummy_driver):
    service, _, _ = dummy_driver

    primary = DummyNode(["SourceFile"], "SourceFile:gateway/app.py", path="gateway/app.py")
    neighbor = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina")
    relationship = DummyRelationship(primary, neighbor, "BELONGS_TO")

    def fake_fetch_node_by_id(tx, label: str, key: str, value: Any):
        assert (label, key, value) == ("SourceFile", "path", "gateway/app.py")
        return primary

    def fake_fetch_node_relationships(tx, label, key, value, direction, limit):
        assert direction == "all"
        assert limit == 3
        return [{"relationship": relationship, "node": neighbor}]

    monkeypatch.setattr(graph_service, "_fetch_node_by_id", fake_fetch_node_by_id)
    monkeypatch.setattr(graph_service, "_fetch_node_relationships", fake_fetch_node_relationships)

    result = service.get_node("SourceFile:gateway/app.py", relationships="all", limit=3)

    assert result["node"]["properties"]["path"] == "gateway/app.py"
    assert result["relationships"][0]["type"] == "BELONGS_TO"


def test_get_node_missing_raises(monkeypatch: pytest.MonkeyPatch, dummy_driver):
    service, _, _ = dummy_driver

    def fake_fetch_node_by_id(tx, label: str, key: str, value: Any):
        return None

    monkeypatch.setattr(graph_service, "_fetch_node_by_id", fake_fetch_node_by_id)

    with pytest.raises(GraphNotFoundError):
        service.get_node("SourceFile:missing.py", relationships="all", limit=5)


def test_search_serializes_results(monkeypatch: pytest.MonkeyPatch, dummy_driver):
    service, _, _ = dummy_driver

    node = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina")

    def fake_search_entities(tx, term: str, limit: int):
        assert term == "kasmina"
        assert limit == 4
        return [{"node": node, "label": "Subsystem", "score": 0.95, "snippet": "Kasmina"}]

    monkeypatch.setattr(graph_service, "_search_entities", fake_search_entities)

    result = service.search("Kasmina", limit=4)

    assert result["results"][0]["id"] == "Subsystem:Kasmina"
    assert result["results"][0]["score"] == 0.95


def test_shortest_path_depth(monkeypatch: pytest.MonkeyPatch, dummy_driver):
    service, session, _ = dummy_driver

    session.run_result = SimpleNamespace(
        single=lambda: {"depth": 3},
    )

    depth = service.shortest_path_depth("SourceFile:gateway/app.py", max_depth=5)

    query, params = session.run_calls[0]
    assert "shortestPath" in query
    assert params == {"value": "gateway/app.py"}
    assert depth == 3


def test_shortest_path_depth_none(monkeypatch: pytest.MonkeyPatch, dummy_driver):
    service, session, _ = dummy_driver

    session.run_result = SimpleNamespace(single=lambda: None)

    assert service.shortest_path_depth("SourceFile:missing.py", max_depth=2) is None


def test_run_cypher_serializes_records(monkeypatch: pytest.MonkeyPatch, dummy_driver):
    service, _, driver = dummy_driver

    node = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina")

    class DummyRecord:
        def __init__(self, values: list[Any]) -> None:
            self._values = values

        def values(self) -> list[Any]:
            return self._values

    driver.execute_query_result = SimpleNamespace(
        records=[DummyRecord([node, 42])],
        summary=SimpleNamespace(result_available_after=12, database=SimpleNamespace(name="knowledge")),
    )

    payload = service.run_cypher("MATCH (n) RETURN n LIMIT 1", parameters=None)

    assert payload["data"][0]["row"][0]["id"] == "Subsystem:Kasmina"
    assert payload["summary"]["resultConsumedAfterMs"] == 12
    assert driver.last_execute_query[0] == "MATCH (n) RETURN n LIMIT 1"


def test_run_cypher_rejects_non_read_queries(dummy_driver):
    service, _, _ = dummy_driver

    with pytest.raises(GraphQueryError):
        service.run_cypher("CREATE (n:Test) RETURN n LIMIT 1", parameters=None)
