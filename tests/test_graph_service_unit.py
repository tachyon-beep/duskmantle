from __future__ import annotations

from collections.abc import Callable, Iterable
from types import SimpleNamespace, TracebackType
from unittest import mock

import pytest

from gateway.graph import service as graph_service
from gateway.graph.service import GraphNotFoundError, GraphQueryError, GraphService
from gateway.observability.metrics import GRAPH_CYPHER_DENIED_TOTAL

DriverFixture = tuple[GraphService, "DummySession", "DummyDriver"]


def _reset_metric(reason: str) -> None:
    try:
        GRAPH_CYPHER_DENIED_TOTAL.remove(reason)
    except KeyError:
        pass


def _metric_value(reason: str) -> float:
    sample = GRAPH_CYPHER_DENIED_TOTAL._metrics.get((reason,))
    return sample._value.get() if sample else 0.0


class DummyNode(dict[str, object]):
    def __init__(self, labels: Iterable[str], element_id: str, **props: object) -> None:
        super().__init__(props)
        self.labels = frozenset(labels)
        self.element_id = element_id


class DummyRelationship(dict[str, object]):
    def __init__(
        self,
        start_node: DummyNode,
        end_node: DummyNode,
        rel_type: str,
        **props: object,
    ) -> None:
        super().__init__(props)
        self.start_node = start_node
        self.end_node = end_node
        self.type = rel_type


class DummySession:
    def __init__(self) -> None:
        self.run_calls: list[tuple[str, dict[str, object]]] = []
        self.run_result = SimpleNamespace(
            single=lambda: None,
        )

    def __enter__(self) -> DummySession:  # pragma: no cover - trivial
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:  # pragma: no cover - trivial
        return None

    def execute_read(self, func: Callable[..., object], *args: object, **kwargs: object) -> object:
        return func(None, *args, **kwargs)

    def run(self, query: str, **params: object) -> SimpleNamespace:
        self.run_calls.append((query, params))
        return self.run_result


class DummyDriver:
    def __init__(self, session: DummySession) -> None:
        self._session = session
        self.last_execute_query: tuple[str, dict[str, object], str] | None = None
        self.execute_query_result = SimpleNamespace(
            records=[],
            summary=SimpleNamespace(
                result_available_after=None,
                database=None,
                counters=SimpleNamespace(contains_updates=False),
            ),
        )

    def session(self, **kwargs: object) -> DummySession:
        return self._session

    def execute_query(
        self,
        query: str,
        parameters: dict[str, object],
        database_: str,
    ) -> SimpleNamespace:
        self.last_execute_query = (query, parameters, database_)
        return self.execute_query_result


@pytest.fixture(autouse=True)
def patch_graph_types(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(graph_service, "Node", DummyNode)
    monkeypatch.setattr(graph_service, "Relationship", DummyRelationship)


@pytest.fixture
def dummy_driver() -> DriverFixture:
    session = DummySession()
    driver = DummyDriver(session)
    service = GraphService(
        driver_provider=lambda: driver,
        database="knowledge",
        readonly_provider=lambda: driver,
    )
    return service, session, driver


def test_get_subsystem_paginates_and_includes_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    dummy_driver: DriverFixture,
) -> None:
    service, _, _ = dummy_driver

    subsystem = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina", description="Analysis")
    related_node = DummyNode(["DesignDoc"], "DesignDoc:docs/design.md", path="docs/design.md")
    relationship = DummyRelationship(subsystem, related_node, "DESCRIBES")
    sibling_node = DummyNode(["DesignDoc"], "DesignDoc:docs/other.md", path="docs/other.md")
    sibling_relationship = DummyRelationship(subsystem, sibling_node, "DESCRIBES")
    artifact_node = DummyNode(["SourceFile"], "SourceFile:gateway/api.py", path="gateway/api.py")

    def fake_fetch_subsystem_node(_tx: object, name: str) -> DummyNode:
        assert name == "Kasmina"
        return subsystem

    def fake_fetch_paths(_tx: object, name: str, depth: int) -> list[dict[str, object]]:
        assert depth == 2
        return [
            {"node": related_node, "nodes": [subsystem, related_node], "relationships": [relationship]},
            {"node": sibling_node, "nodes": [subsystem, sibling_node], "relationships": [sibling_relationship]},
        ]

    def fake_fetch_artifacts(_tx: object, name: str) -> list[DummyNode]:
        return [artifact_node]

    monkeypatch.setattr(graph_service, "_fetch_subsystem_node", fake_fetch_subsystem_node)
    monkeypatch.setattr(graph_service, "_fetch_subsystem_paths", fake_fetch_paths)
    monkeypatch.setattr(graph_service, "_fetch_artifacts_for_subsystem", fake_fetch_artifacts)

    result = service.get_subsystem(
        "Kasmina",
        depth=2,
        limit=1,
        cursor=None,
        include_artifacts=True,
    )

    assert result["subsystem"]["properties"]["name"] == "Kasmina"
    assert result["related"]["total"] == 2
    first_related = result["related"]["nodes"][0]
    assert first_related["relationship"] == "DESCRIBES"
    assert first_related["path"][0]["target"] == "DesignDoc:docs/design.md"
    assert result["related"]["cursor"] is not None  # pagination cursor emitted when more records remain
    assert result["artifacts"][0]["properties"]["path"] == "gateway/api.py"


def test_get_subsystem_missing_raises(
    monkeypatch: pytest.MonkeyPatch,
    dummy_driver: DriverFixture,
) -> None:
    service, _, _ = dummy_driver

    def fake_fetch_subsystem_node(_tx: object, name: str) -> DummyNode:
        return None

    monkeypatch.setattr(graph_service, "_fetch_subsystem_node", fake_fetch_subsystem_node)

    with pytest.raises(GraphNotFoundError):
        service.get_subsystem("Unknown", depth=1, limit=5, cursor=None, include_artifacts=False)


def test_get_subsystem_graph_returns_nodes_and_edges(
    monkeypatch: pytest.MonkeyPatch,
    dummy_driver: DriverFixture,
) -> None:
    service, _, _ = dummy_driver

    subsystem = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina")
    mid = DummyNode(["Subsystem"], "Subsystem:Telemetry", name="Telemetry")
    target = DummyNode(["IntegrationMessage"], "IntegrationMessage:Sync", name="Sync")
    rel_one = DummyRelationship(subsystem, mid, "DEPENDS_ON")
    rel_two = DummyRelationship(mid, target, "IMPLEMENTS")
    artifact_node = DummyNode(["DesignDoc"], "DesignDoc:docs/telemetry.md", path="docs/telemetry.md")

    def fake_fetch_subsystem_node(_tx: object, name: str) -> DummyNode:
        assert name == "Kasmina"
        return subsystem

    def fake_fetch_paths(_tx: object, name: str, depth: int) -> list[dict[str, object]]:
        assert depth == 3
        return [
            {"node": target, "nodes": [subsystem, mid, target], "relationships": [rel_one, rel_two]},
        ]

    def fake_fetch_artifacts(_tx: object, name: str) -> list[DummyNode]:
        return [artifact_node]

    monkeypatch.setattr(graph_service, "_fetch_subsystem_node", fake_fetch_subsystem_node)
    monkeypatch.setattr(graph_service, "_fetch_subsystem_paths", fake_fetch_paths)
    monkeypatch.setattr(graph_service, "_fetch_artifacts_for_subsystem", fake_fetch_artifacts)

    graph_payload = service.get_subsystem_graph("Kasmina", depth=3)

    edge_types = {edge["type"] for edge in graph_payload["edges"]}
    assert {"DEPENDS_ON", "IMPLEMENTS"}.issubset(edge_types)
    node_ids = {node["id"] for node in graph_payload["nodes"]}
    assert node_ids.issuperset({"Subsystem:Kasmina", "Subsystem:Telemetry", "IntegrationMessage:Sync"})
    assert graph_payload["artifacts"][0]["id"] == "DesignDoc:docs/telemetry.md"


def test_fetch_subsystem_paths_inlines_depth_literal(monkeypatch: pytest.MonkeyPatch) -> None:
    tx = mock.Mock()
    tx.run.return_value = []

    graph_service._fetch_subsystem_paths(tx, name="Kasmina", depth=3)

    assert tx.run.call_count == 1
    args = tx.run.call_args.args
    kwargs = tx.run.call_args.kwargs
    assert "*1..3" in args[0]
    assert kwargs == {"name": "Kasmina"}


def test_get_node_with_relationships(
    monkeypatch: pytest.MonkeyPatch,
    dummy_driver: DriverFixture,
) -> None:
    service, _, _ = dummy_driver

    primary = DummyNode(["SourceFile"], "SourceFile:gateway/app.py", path="gateway/app.py")
    neighbor = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina")
    relationship = DummyRelationship(primary, neighbor, "BELONGS_TO")

    def fake_fetch_node_by_id(_tx: object, label: str, key: str, value: str) -> DummyNode:
        assert (label, key, value) == ("SourceFile", "path", "gateway/app.py")
        return primary

    def fake_fetch_node_relationships(
        _tx: object,
        label: str,
        key: str,
        value: str,
        direction: str,
        limit: int,
    ) -> list[dict[str, object]]:
        assert direction == "all"
        assert limit == 3
        return [{"relationship": relationship, "node": neighbor}]

    monkeypatch.setattr(graph_service, "_fetch_node_by_id", fake_fetch_node_by_id)
    monkeypatch.setattr(graph_service, "_fetch_node_relationships", fake_fetch_node_relationships)

    result = service.get_node("SourceFile:gateway/app.py", relationships="all", limit=3)

    assert result["node"]["properties"]["path"] == "gateway/app.py"
    assert result["relationships"][0]["type"] == "BELONGS_TO"


def test_list_orphan_nodes_rejects_unknown_label(dummy_driver: DriverFixture) -> None:
    service, _, _ = dummy_driver
    with pytest.raises(GraphQueryError):
        service.list_orphan_nodes(label="Unknown", cursor=None, limit=5)


def test_list_orphan_nodes_serializes_results(
    monkeypatch: pytest.MonkeyPatch,
    dummy_driver: DriverFixture,
) -> None:
    service, _, _ = dummy_driver

    orphan = DummyNode(["DesignDoc"], "DesignDoc:docs/orphan.md", path="docs/orphan.md")

    def fake_fetch_orphans(_tx: object, label: str | None, skip: int, limit: int) -> list[DummyNode]:
        assert label is None
        assert skip == 0
        assert limit == 5
        return [orphan]

    monkeypatch.setattr(graph_service, "_fetch_orphan_nodes", fake_fetch_orphans)

    payload = service.list_orphan_nodes(label=None, cursor=None, limit=5)
    assert payload["nodes"][0]["id"] == "DesignDoc:docs/orphan.md"
    assert payload["cursor"] is None


def test_get_node_missing_raises(
    monkeypatch: pytest.MonkeyPatch,
    dummy_driver: DriverFixture,
) -> None:
    service, _, _ = dummy_driver

    def fake_fetch_node_by_id(_tx: object, label: str, key: str, value: str) -> DummyNode:
        return None

    monkeypatch.setattr(graph_service, "_fetch_node_by_id", fake_fetch_node_by_id)

    with pytest.raises(GraphNotFoundError):
        service.get_node("SourceFile:missing.py", relationships="all", limit=5)


def test_search_serializes_results(
    monkeypatch: pytest.MonkeyPatch,
    dummy_driver: DriverFixture,
) -> None:
    service, _, _ = dummy_driver

    node = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina")

    def fake_search_entities(_tx: object, term: str, limit: int) -> list[dict[str, object]]:
        assert term == "kasmina"
        assert limit == 4
        return [{"node": node, "label": "Subsystem", "score": 0.95, "snippet": "Kasmina"}]

    monkeypatch.setattr(graph_service, "_search_entities", fake_search_entities)

    result = service.search("Kasmina", limit=4)

    assert result["results"][0]["id"] == "Subsystem:Kasmina"
    assert result["results"][0]["score"] == 0.95


def test_shortest_path_depth(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None:
    service, session, _ = dummy_driver

    session.run_result = SimpleNamespace(
        single=lambda: {"depth": 3},
    )

    depth = service.shortest_path_depth("SourceFile:gateway/app.py", max_depth=5)

    query, params = session.run_calls[0]
    assert "shortestPath" in query
    assert params == {"value": "gateway/app.py"}
    assert depth == 3


def test_shortest_path_depth_none(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None:
    service, session, _ = dummy_driver

    session.run_result = SimpleNamespace(single=lambda: None)

    assert service.shortest_path_depth("SourceFile:missing.py", max_depth=2) is None


def test_run_cypher_serializes_records(monkeypatch: pytest.MonkeyPatch, dummy_driver: DriverFixture) -> None:
    service, _, driver = dummy_driver

    node = DummyNode(["Subsystem"], "Subsystem:Kasmina", name="Kasmina")

    class DummyRecord:
        def __init__(self, values: list[object]) -> None:
            self._values = values

        def values(self) -> list[object]:
            return self._values

    driver.execute_query_result = SimpleNamespace(
        records=[DummyRecord([node, 42])],
        summary=SimpleNamespace(
            result_available_after=12,
            database=SimpleNamespace(name="knowledge"),
            counters=SimpleNamespace(contains_updates=False),
        ),
    )

    payload = service.run_cypher("MATCH (n) RETURN n LIMIT 1", parameters=None)

    assert payload["data"][0]["row"][0]["id"] == "Subsystem:Kasmina"
    assert payload["summary"]["resultConsumedAfterMs"] == 12
    assert driver.last_execute_query[0] == "MATCH (n) RETURN n LIMIT 1"


def test_run_cypher_rejects_non_read_queries(dummy_driver: DriverFixture) -> None:
    service, _, _ = dummy_driver

    _reset_metric("keyword")
    before = _metric_value("keyword")
    with pytest.raises(GraphQueryError):
        service.run_cypher("CREATE (n:Test) RETURN n LIMIT 1", parameters=None)

    after = _metric_value("keyword")
    assert after == pytest.approx(before + 1)


def test_run_cypher_rejects_updates_detected_in_counters(dummy_driver: DriverFixture) -> None:
    service, _, driver = dummy_driver
    driver.execute_query_result = SimpleNamespace(
        records=[],
        summary=SimpleNamespace(
            result_available_after=None,
            database=None,
            counters=SimpleNamespace(contains_updates=True),
        ),
    )

    _reset_metric("mutation")
    before = _metric_value("mutation")
    with pytest.raises(GraphQueryError):
        service.run_cypher("MATCH (n) RETURN n LIMIT 1", parameters=None)

    after = _metric_value("mutation")
    assert after == pytest.approx(before + 1)


def test_run_cypher_allows_whitelisted_procedure(dummy_driver: DriverFixture) -> None:
    service, _, driver = dummy_driver
    driver.execute_query_result = SimpleNamespace(
        records=[],
        summary=SimpleNamespace(
            result_available_after=None,
            database=None,
            counters=SimpleNamespace(contains_updates=False),
        ),
    )

    _reset_metric("procedure")
    service.run_cypher(
        "CALL db.schema.nodeTypeProperties() YIELD nodeType RETURN nodeType LIMIT 5",
        parameters=None,
    )

    assert driver.last_execute_query[0].startswith("CALL db.schema")
    assert _metric_value("procedure") == 0


def test_run_cypher_rejects_disallowed_procedure(dummy_driver: DriverFixture) -> None:
    service, _, _ = dummy_driver

    _reset_metric("procedure")
    before = _metric_value("procedure")
    with pytest.raises(GraphQueryError):
        service.run_cypher(
            "CALL dbms.procedures() YIELD name RETURN name LIMIT 5",
            parameters=None,
        )

    after = _metric_value("procedure")
    assert after == pytest.approx(before + 1)
