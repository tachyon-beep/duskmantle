from __future__ import annotations

import time
from typing import Any

import pytest

from gateway.graph.service import GraphService
from gateway.search.filtering import build_filter_state
from gateway.search.graph_enricher import GraphEnricher


def _metric_value(name: str, labels: dict[str, str] | None = None) -> float:
    from prometheus_client import REGISTRY

    value = REGISTRY.get_sample_value(name, labels or {})
    return float(value) if value is not None else 0.0


class DummyGraphService(GraphService):  # type: ignore[misc]
    def __init__(self, response: dict[str, Any], *, delay: float = 0.0) -> None:
        self._response = response
        self._delay = delay
        self.node_calls = 0
        self.depth_calls = 0

    def get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:  # type: ignore[override]
        self.node_calls += 1
        if self._delay:
            time.sleep(self._delay)
        return self._response

    def shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None:  # type: ignore[override]
        self.depth_calls += 1
        return 2

    def get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]:  # pragma: no cover - unused
        raise NotImplementedError

    def search(self, term: str, *, limit: int) -> dict[str, Any]:  # pragma: no cover - unused
        raise NotImplementedError

    def run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError


@pytest.fixture()
def graph_payload() -> dict[str, Any]:
    return {
        "chunk_id": "path::0",
        "path": "src/module.py",
        "artifact_type": "code",
        "subsystem": "core",
        "git_timestamp": 1704067200,
    }


@pytest.fixture()
def graph_response() -> dict[str, Any]:
    return {
        "node": {
            "id": "SourceFile:src/module.py",
            "labels": ["SourceFile"],
            "properties": {"path": "src/module.py", "subsystem": "core"},
        },
        "relationships": [],
        "related_artifacts": [],
    }


def test_graph_enricher_caches_results(graph_payload: dict[str, Any], graph_response: dict[str, Any]) -> None:
    state = build_filter_state({})
    service = DummyGraphService(graph_response)
    enricher = GraphEnricher(
        graph_service=service,
        include_graph=True,
        filter_state=state,
        graph_max_results=5,
        time_budget_seconds=1.0,
        slow_warn_seconds=5.0,
        request_id="req",
    )

    miss_before = _metric_value("km_search_graph_cache_events_total", {"status": "miss"})
    hit_before = _metric_value("km_search_graph_cache_events_total", {"status": "hit"})

    result_first = enricher.resolve(graph_payload, subsystem_match=True, warnings=[])
    result_second = enricher.resolve(graph_payload, subsystem_match=True, warnings=[])

    assert result_first.graph_context is not None
    assert result_second.graph_context is not None
    assert service.node_calls == 1
    assert _metric_value("km_search_graph_cache_events_total", {"status": "miss"}) >= miss_before + 1
    assert _metric_value("km_search_graph_cache_events_total", {"status": "hit"}) >= hit_before + 1


def test_graph_enricher_respects_result_budget(graph_payload: dict[str, Any], graph_response: dict[str, Any]) -> None:
    state = build_filter_state({})
    service = DummyGraphService(graph_response)
    enricher = GraphEnricher(
        graph_service=service,
        include_graph=True,
        filter_state=state,
        graph_max_results=1,
        time_budget_seconds=1.0,
        slow_warn_seconds=5.0,
        request_id="req",
    )

    skipped_before = _metric_value("km_search_graph_skipped_total", {"reason": "limit"})

    first = enricher.resolve(graph_payload, subsystem_match=True, warnings=[])
    second_payload = {**graph_payload, "chunk_id": "path::1", "path": "src/other.py"}
    second = enricher.resolve(second_payload, subsystem_match=True, warnings=[])

    assert first.graph_context is not None
    assert second.graph_context is None
    assert enricher.slots_exhausted is True
    assert _metric_value("km_search_graph_skipped_total", {"reason": "limit"}) >= skipped_before + 1


def test_graph_enricher_respects_time_budget(graph_payload: dict[str, Any], graph_response: dict[str, Any]) -> None:
    state = build_filter_state({})
    service = DummyGraphService(graph_response, delay=0.05)
    enricher = GraphEnricher(
        graph_service=service,
        include_graph=True,
        filter_state=state,
        graph_max_results=5,
        time_budget_seconds=0.02,
        slow_warn_seconds=5.0,
        request_id="req",
    )

    skipped_before = _metric_value("km_search_graph_skipped_total", {"reason": "time"})

    first = enricher.resolve(graph_payload, subsystem_match=True, warnings=[])
    assert first.graph_context is not None

    second_payload = {**graph_payload, "chunk_id": "path::1", "path": "src/other.py"}
    second = enricher.resolve(second_payload, subsystem_match=True, warnings=[])

    assert second.graph_context is None
    assert enricher.time_exhausted is True
    assert _metric_value("km_search_graph_skipped_total", {"reason": "time"}) >= skipped_before + 1
