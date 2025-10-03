from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
import time
from typing import Any

import pytest
from prometheus_client import REGISTRY

from gateway.graph.service import GraphService
from gateway.search import SearchOptions, SearchService, SearchWeights
from gateway.search.trainer import ModelArtifact


def _metric_value(name: str, labels: dict[str, str] | None = None) -> float:
    value = REGISTRY.get_sample_value(name, labels or {})
    return float(value) if value is not None else 0.0


class FakeEmbedder:
    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakePoint:
    def __init__(self, payload: dict[str, Any], score: float) -> None:
        self.payload = payload
        self.score = score


class FakeQdrantClient:
    def __init__(self, points: list[FakePoint]) -> None:
        self._points = points
        self.last_kwargs: dict[str, object] = {}

    def search(self, **kwargs: object) -> list[FakePoint]:
        self.last_kwargs = dict(kwargs)
        return self._points


class DummyGraphService(GraphService):  # type: ignore[misc]
    def __init__(self, response: dict[str, Any]) -> None:
        self._response = response

    def get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:  # type: ignore[override]
        return self._response

    def get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]:  # pragma: no cover - not used
        raise NotImplementedError

    def search(self, term: str, *, limit: int) -> dict[str, Any]:  # pragma: no cover - not used
        raise NotImplementedError

    def run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None:  # type: ignore[override]
        return 1


class SlowGraphService(DummyGraphService):
    def __init__(self, response: dict[str, Any], delay: float) -> None:
        super().__init__(response)
        self._delay = delay

    def get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:  # type: ignore[override]
        time.sleep(self._delay)
        return super().get_node(node_id, relationships=relationships, limit=limit)


@pytest.fixture()
def sample_points() -> list[FakePoint]:
    return [
        FakePoint(
            {
                "chunk_id": "path::0",
                "path": "src/module.py",
                "artifact_type": "code",
                "subsystem": "core",
                "namespace": "src",
                "tags": ["IntegrationAlpha"],
                "git_timestamp": 1704067200,
                "text": "def foo(): pass",
            },
            0.9,
        )
    ]


@pytest.fixture()
def graph_response() -> dict[str, Any]:
    return {
        "node": {
            "id": "SourceFile:src/module.py",
            "labels": ["SourceFile"],
            "properties": {"path": "src/module.py", "subsystem": "core"},
        },
        "relationships": [
            {
                "type": "BELONGS_TO",
                "direction": "OUT",
                "target": {
                    "id": "Subsystem:core",
                    "labels": ["Subsystem"],
                    "properties": {"name": "core"},
                },
            },
            {
                "type": "DESCRIBES",
                "direction": "OUT",
                "target": {
                    "id": "DesignDoc:docs/design/core.md",
                    "labels": ["DesignDoc"],
                    "properties": {"path": "docs/design/core.md"},
                },
            },
        ],
        "related_artifacts": [{"id": "DesignDoc:docs/design/core.md", "relationship": "DESCRIBES"}],
    }


def test_search_service_enriches_with_graph(
    sample_points: list[FakePoint],
    graph_response: dict[str, Any],
) -> None:
    search_service = SearchService(
        qdrant_client=FakeQdrantClient(sample_points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )
    response = search_service.search(
        query="core latency",
        limit=5,
        include_graph=True,
        graph_service=DummyGraphService(graph_response),
    )

    assert response.query == "core latency"
    assert len(response.results) == 1
    result = response.results[0]
    assert result.chunk["artifact_path"] == "src/module.py"
    assert result.graph_context["primary_node"]["id"] == "SourceFile:src/module.py"
    assert response.metadata["graph_context_included"] is True
    assert response.metadata["scoring_mode"] == "heuristic"
    assert response.metadata["weight_profile"] == "custom"
    assert "weights" in response.metadata
    assert "hybrid_weights" in response.metadata
    assert result.scoring["mode"] == "heuristic"
    assert result.scoring["adjusted_score"] > result.scoring["vector_score"]
    assert "lexical_score" in result.scoring
    signals = result.scoring["signals"]
    assert signals["relationship_count"] >= 1
    assert "coverage_ratio" in signals
    assert "path_depth" in signals
    assert "freshness_days" in signals
    assert "criticality_score" in signals
    assert "coverage_penalty" in signals


def test_search_service_handles_missing_graph(sample_points: list[FakePoint]) -> None:
    search_service = SearchService(
        qdrant_client=FakeQdrantClient(sample_points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )
    response = search_service.search(
        query="test",
        limit=5,
        include_graph=False,
        graph_service=None,
    )
    assert response.results[0].graph_context is None
    assert response.metadata["graph_context_included"] is False
    scoring = response.results[0].scoring
    weighted_vector_score = scoring.get("weighted_vector_score", scoring.get("vector_score", 0.0))
    weighted_lexical_score = scoring.get("weighted_lexical_score", 0.0)
    base_component = weighted_vector_score + weighted_lexical_score
    assert scoring["adjusted_score"] == pytest.approx(base_component)
    assert response.metadata["scoring_mode"] == "heuristic"
    assert response.metadata["weight_profile"] == "custom"
    assert scoring["mode"] == "heuristic"
    assert "lexical_score" in scoring
    signals = scoring["signals"]
    assert "coverage_ratio" in signals
    assert "path_depth" in signals


class MapGraphService(GraphService):  # type: ignore[misc]
    def __init__(self, data: dict[str, dict[str, Any]]) -> None:
        self._data = data

    def get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:  # type: ignore[override]
        return self._data.get(node_id, {"node": {}, "relationships": [], "related_artifacts": []})

    def get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]:  # pragma: no cover - unused
        raise NotImplementedError

    def search(self, term: str, *, limit: int) -> dict[str, Any]:  # pragma: no cover - unused
        raise NotImplementedError

    def run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None:  # type: ignore[override]
        return 1


class CountingGraphService(GraphService):  # type: ignore[misc]
    def __init__(self, response: dict[str, Any], depth: int = 2) -> None:
        self._response = response
        self._depth = depth
        self.node_calls = 0
        self.depth_calls = 0

    def get_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:  # type: ignore[override]
        self.node_calls += 1
        return self._response

    def shortest_path_depth(self, node_id: str, *, max_depth: int = 4) -> int | None:  # type: ignore[override]
        self.depth_calls += 1
        return self._depth

    def get_subsystem(self, *args: object, **kwargs: object) -> dict[str, Any]:  # pragma: no cover - unused
        raise NotImplementedError

    def search(self, term: str, *, limit: int) -> dict[str, Any]:  # pragma: no cover - unused
        raise NotImplementedError

    def run_cypher(self, query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError


def test_search_hnsw_search_params(sample_points: list[FakePoint]) -> None:
    client = FakeQdrantClient(sample_points)
    search_service = SearchService(
        qdrant_client=client,
        collection_name="collection",
        embedder=FakeEmbedder(),
        options=SearchOptions(hnsw_ef_search=256),
    )

    response = search_service.search(
        query="core",
        limit=1,
        include_graph=False,
        graph_service=None,
    )

    search_params = client.last_kwargs.get("search_params")
    assert search_params is not None
    assert getattr(search_params, "hnsw_ef", None) == 256
    assert response.metadata.get("hnsw_ef_search") == 256


def test_lexical_score_affects_ranking() -> None:
    points = [
        FakePoint(
            {
                "chunk_id": "foo::0",
                "path": "docs/foo.md",
                "artifact_type": "doc",
                "subsystem": "core",
                "text": "foo details",
            },
            0.6,
        ),
        FakePoint(
            {
                "chunk_id": "bar::0",
                "path": "docs/bar.md",
                "artifact_type": "doc",
                "subsystem": "core",
                "text": "unrelated content",
            },
            0.6,
        ),
    ]

    search_service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
        weights=SearchWeights(lexical=0.5),
    )

    response = search_service.search(
        query="foo",
        limit=2,
        include_graph=False,
        graph_service=None,
    )

    assert response.results[0].chunk["chunk_id"] == "foo::0"
    top_scoring = response.results[0].scoring
    assert top_scoring["lexical_score"] > 0.0
    assert top_scoring["adjusted_score"] > response.results[1].scoring["adjusted_score"]


def test_search_service_orders_by_adjusted_score() -> None:
    points = [
        FakePoint(
            {
                "chunk_id": "core::0",
                "path": "src/core.py",
                "artifact_type": "code",
                "subsystem": "core",
                "text": "core handler",
            },
            0.80,
        ),
        FakePoint(
            {
                "chunk_id": "other::0",
                "path": "src/other.py",
                "artifact_type": "code",
                "subsystem": "other",
                "text": "other handler",
            },
            0.95,
        ),
    ]

    graph_data = {
        "SourceFile:src/core.py": {
            "node": {
                "id": "SourceFile:src/core.py",
                "labels": ["SourceFile"],
                "properties": {"path": "src/core.py", "subsystem": "core"},
            },
            "relationships": [
                {
                    "type": "BELONGS_TO",
                    "direction": "OUT",
                    "target": {
                        "id": "Subsystem:core",
                        "labels": ["Subsystem"],
                        "properties": {"name": "core"},
                    },
                }
            ],
            "related_artifacts": [],
        },
        "SourceFile:src/other.py": {
            "node": {
                "id": "SourceFile:src/other.py",
                "labels": ["SourceFile"],
                "properties": {"path": "src/other.py", "subsystem": "other"},
            },
            "relationships": [],
            "related_artifacts": [],
        },
    }

    service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )

    response = service.search(
        query="core telemetry",
        limit=2,
        include_graph=True,
        graph_service=MapGraphService(graph_data),
    )

    assert [result.chunk["subsystem"] for result in response.results] == ["core", "other"]
    assert response.metadata["scoring_mode"] == "heuristic"
    assert all(result.scoring["mode"] == "heuristic" for result in response.results)
    for result in response.results:
        assert "coverage_ratio" in result.scoring["signals"]

    response_vector_sorted = service.search(
        query="core telemetry",
        limit=2,
        include_graph=True,
        graph_service=MapGraphService(graph_data),
        sort_by_vector=True,
    )
    assert [r.chunk["subsystem"] for r in response_vector_sorted.results] == ["other", "core"]


def test_search_service_caches_graph_lookups(
    sample_points: list[FakePoint],
    graph_response: dict[str, Any],
) -> None:
    points = [
        FakePoint(
            {
                "chunk_id": "path::0",
                "path": "src/module.py",
                "artifact_type": "code",
                "subsystem": "core",
                "text": "def foo(): pass",
            },
            0.9,
        ),
        FakePoint(
            {
                "chunk_id": "path::1",
                "path": "src/module.py",
                "artifact_type": "code",
                "subsystem": "core",
                "text": "def bar(): pass",
            },
            0.85,
        ),
    ]

    graph_service = CountingGraphService(graph_response, depth=2)

    search_service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )

    miss_before = _metric_value("km_search_graph_cache_events_total", {"status": "miss"})
    hit_before = _metric_value("km_search_graph_cache_events_total", {"status": "hit"})
    error_before = _metric_value("km_search_graph_cache_events_total", {"status": "error"})
    lookup_count_before = _metric_value("km_search_graph_lookup_seconds_count")
    score_count_before = _metric_value("km_search_adjusted_minus_vector_count")

    response = search_service.search(
        query="core",
        limit=5,
        include_graph=True,
        graph_service=graph_service,
    )

    assert response.metadata["graph_context_included"] is True
    assert graph_service.node_calls == 1
    assert graph_service.depth_calls == 1
    for result in response.results:
        assert result.scoring["signals"]["path_depth"] == pytest.approx(2.0)

    assert (_metric_value("km_search_graph_cache_events_total", {"status": "miss"}) - miss_before) == pytest.approx(1.0)
    assert (_metric_value("km_search_graph_cache_events_total", {"status": "hit"}) - hit_before) == pytest.approx(1.0)
    assert (_metric_value("km_search_graph_cache_events_total", {"status": "error"}) - error_before) == pytest.approx(0.0)
    assert (_metric_value("km_search_graph_lookup_seconds_count") - lookup_count_before) == pytest.approx(1.0)
    assert (_metric_value("km_search_adjusted_minus_vector_count") - score_count_before) == pytest.approx(len(response.results))


def test_search_service_filters_artifact_types() -> None:
    points = [
        FakePoint(
            {
                "chunk_id": "code::0",
                "path": "src/code.py",
                "artifact_type": "code",
                "subsystem": "core",
                "namespace": "src",
                "tags": ["IntegrationAlpha"],
                "git_timestamp": 1704067200,
                "text": "code chunk",
            },
            0.9,
        ),
        FakePoint(
            {
                "chunk_id": "doc::0",
                "path": "docs/design.md",
                "artifact_type": "doc",
                "subsystem": "core",
                "namespace": "docs",
                "tags": ["Docs"],
                "git_timestamp": 1701734400,
                "text": "doc chunk",
            },
            0.85,
        ),
    ]

    search_service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )

    response = search_service.search(
        query="core",
        limit=5,
        include_graph=False,
        graph_service=None,
        filters={"artifact_types": ["code"]},
    )

    assert len(response.results) == 1
    assert response.results[0].chunk["artifact_type"] == "code"
    assert response.metadata["filters_applied"]["artifact_types"] == ["code"]


def test_search_service_filters_namespaces() -> None:
    points = [
        FakePoint(
            {
                "chunk_id": "src::0",
                "path": "src/core.py",
                "artifact_type": "code",
                "subsystem": "core",
                "namespace": "src",
                "tags": ["IntegrationAlpha"],
                "git_timestamp": 1704067200,
                "text": "core code",
            },
            0.9,
        ),
        FakePoint(
            {
                "chunk_id": "docs::0",
                "path": "docs/guide.md",
                "artifact_type": "doc",
                "subsystem": "core",
                "namespace": "docs",
                "tags": ["Guide"],
                "git_timestamp": 1704067200,
                "text": "guide",
            },
            0.88,
        ),
    ]

    search_service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )

    response = search_service.search(
        query="core",
        limit=5,
        include_graph=False,
        graph_service=None,
        filters={"namespaces": ["docs"]},
    )

    assert len(response.results) == 1
    assert response.results[0].chunk["artifact_path"] == "docs/guide.md"
    assert response.metadata["filters_applied"]["namespaces"] == ["docs"]


def test_search_service_filters_tags() -> None:
    points = [
        FakePoint(
            {
                "chunk_id": "src::0",
                "path": "src/core.py",
                "artifact_type": "code",
                "subsystem": "core",
                "namespace": "src",
                "tags": ["IntegrationAlpha", "Operations"],
                "git_timestamp": 1704067200,
                "text": "core code",
            },
            0.9,
        ),
        FakePoint(
            {
                "chunk_id": "src::1",
                "path": "src/ops.py",
                "artifact_type": "code",
                "subsystem": "ops",
                "namespace": "src",
                "tags": ["TelemetryBeta"],
                "git_timestamp": 1704067200,
                "text": "ops code",
            },
            0.88,
        ),
    ]

    search_service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )

    response = search_service.search(
        query="core",
        limit=5,
        include_graph=False,
        graph_service=None,
        filters={"tags": ["operations"]},
    )

    assert len(response.results) == 1
    assert response.results[0].chunk["artifact_path"] == "src/core.py"
    assert response.metadata["filters_applied"]["tags"] == ["operations"]


def test_search_service_filters_recency_updated_after() -> None:
    recent_ts = datetime.now(UTC) - timedelta(days=5)
    old_ts = datetime.now(UTC) - timedelta(days=120)
    points = [
        FakePoint(
            {
                "chunk_id": "recent::0",
                "path": "src/recent.py",
                "artifact_type": "code",
                "subsystem": "core",
                "namespace": "src",
                "tags": ["IntegrationAlpha"],
                "git_timestamp": int(recent_ts.timestamp()),
                "text": "recent",
            },
            0.9,
        ),
        FakePoint(
            {
                "chunk_id": "old::0",
                "path": "src/old.py",
                "artifact_type": "code",
                "subsystem": "core",
                "namespace": "src",
                "tags": ["Legacy"],
                "git_timestamp": int(old_ts.timestamp()),
                "text": "old",
            },
            0.88,
        ),
    ]

    search_service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )

    cutoff = datetime.now(UTC) - timedelta(days=30)
    response = search_service.search(
        query="core",
        limit=5,
        include_graph=False,
        graph_service=None,
        filters={"updated_after": cutoff},
    )

    assert len(response.results) == 1
    assert response.results[0].chunk["artifact_path"] == "src/recent.py"
    applied = response.metadata["filters_applied"]["updated_after"]
    assert isinstance(applied, str)
    parsed = datetime.fromisoformat(applied.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None


def test_search_service_filters_recency_max_age_days() -> None:
    now = datetime.now(UTC)
    points = [
        FakePoint(
            {
                "chunk_id": "fresh::0",
                "path": "src/fresh.py",
                "artifact_type": "code",
                "subsystem": "core",
                "namespace": "src",
                "tags": ["IntegrationAlpha"],
                "git_timestamp": int((now - timedelta(days=2)).timestamp()),
                "text": "fresh",
            },
            0.9,
        ),
        FakePoint(
            {
                "chunk_id": "stale::0",
                "path": "src/stale.py",
                "artifact_type": "code",
                "subsystem": "core",
                "namespace": "src",
                "tags": ["Legacy"],
                "git_timestamp": int((now - timedelta(days=90)).timestamp()),
                "text": "stale",
            },
            0.88,
        ),
    ]

    search_service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )

    response = search_service.search(
        query="core",
        limit=5,
        include_graph=False,
        graph_service=None,
        filters={"max_age_days": 30},
    )

    assert len(response.results) == 1
    assert response.results[0].chunk["artifact_path"] == "src/fresh.py"
    assert response.metadata["filters_applied"]["max_age_days"] == 30


def test_search_service_filters_subsystem_via_graph(graph_response: dict[str, Any]) -> None:
    points = [
        FakePoint(
            {
                "chunk_id": "chunk::0",
                "path": "src/module.py",
                "artifact_type": "code",
                "subsystem": None,
                "text": "chunk",
            },
            0.9,
        )
    ]

    graph_data = {
        "SourceFile:src/module.py": {
            "node": {
                "id": "SourceFile:src/module.py",
                "labels": ["SourceFile"],
                "properties": {"path": "src/module.py"},
            },
            "relationships": [
                {
                    "type": "BELONGS_TO",
                    "direction": "OUT",
                    "target": {
                        "id": "Subsystem:Telemetry",
                        "labels": ["Subsystem"],
                        "properties": {"name": "Telemetry"},
                    },
                }
            ],
            "related_artifacts": [],
        },
    }

    search_service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
    )

    response = search_service.search(
        query="telemetry",
        limit=5,
        include_graph=False,
        graph_service=MapGraphService(graph_data),
        filters={"subsystems": ["Telemetry"]},
    )

    assert len(response.results) == 1
    assert response.results[0].chunk["artifact_path"] == "src/module.py"
    assert response.metadata["filters_applied"]["subsystems"] == ["Telemetry"]


def test_search_service_ml_model_reorders_results() -> None:
    points = [
        FakePoint(
            {
                "chunk_id": "core::0",
                "path": "src/core.py",
                "artifact_type": "code",
                "subsystem": "core",
                "text": "core handler",
            },
            0.95,
        ),
        FakePoint(
            {
                "chunk_id": "other::0",
                "path": "src/other.py",
                "artifact_type": "code",
                "subsystem": "other",
                "text": "other handler",
            },
            0.80,
        ),
    ]

    graph_data = {
        "SourceFile:src/core.py": {
            "node": {"id": "SourceFile:src/core.py", "labels": ["SourceFile"], "properties": {"subsystem": "core"}},
            "relationships": [],
            "related_artifacts": [],
        },
        "SourceFile:src/other.py": {
            "node": {"id": "SourceFile:src/other.py", "labels": ["SourceFile"], "properties": {"subsystem": "other"}},
            "relationships": [],
            "related_artifacts": [],
        },
    }

    artifact = ModelArtifact(
        model_type="linear_regression",
        created_at="",
        feature_names=["vector_score"],
        coefficients=[-1.0],
        intercept=1.0,
        metrics={"mse": 0.0, "r2": 1.0},
        training_rows=2,
    )

    service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
        options=SearchOptions(scoring_mode="ml"),
        model_artifact=artifact,
    )

    response = service.search(
        query="core telemetry",
        limit=2,
        include_graph=True,
        graph_service=MapGraphService(graph_data),
    )

    # With heuristic weights, "core" would come first (higher vector score).
    # Model inverts the ordering by penalising high vector scores.
    assert [result.chunk["subsystem"] for result in response.results] == ["other", "core"]
    assert response.metadata["scoring_mode"] == "ml"
    assert all(result.scoring["mode"] == "ml" for result in response.results)
    assert "model" in response.results[0].scoring


def test_search_service_limits_graph_results(graph_response: dict[str, Any]) -> None:
    points = [
        FakePoint(
            {
                "chunk_id": f"chunk::{index}",
                "path": f"src/file{index}.py",
                "artifact_type": "code",
                "subsystem": "core",
                "text": "body",
            },
            0.9,
        )
        for index in range(3)
    ]

    service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
        options=SearchOptions(graph_max_results=1, graph_time_budget_seconds=5.0),
    )

    response = service.search(
        query="core",
        limit=3,
        include_graph=True,
        graph_service=DummyGraphService(graph_response),
    )

    assert response.results[0].graph_context is not None
    assert all(result.graph_context is None for result in response.results[1:])
    assert any("graph context limited" in warning for warning in response.metadata["warnings"])


def test_search_service_respects_graph_time_budget(graph_response: dict[str, Any]) -> None:
    points = [
        FakePoint(
            {
                "chunk_id": f"slow::{index}",
                "path": f"src/slow{index}.py",
                "artifact_type": "code",
                "subsystem": "core",
                "text": "body",
            },
            0.9,
        )
        for index in range(3)
    ]

    service = SearchService(
        qdrant_client=FakeQdrantClient(points),
        collection_name="collection",
        embedder=FakeEmbedder(),
        options=SearchOptions(graph_time_budget_seconds=0.05, graph_max_results=5),
    )

    skipped_before = _metric_value("km_search_graph_skipped_total", {"reason": "time"})
    response = service.search(
        query="core",
        limit=3,
        include_graph=True,
        graph_service=SlowGraphService(graph_response, delay=0.06),
    )
    skipped_after = _metric_value("km_search_graph_skipped_total", {"reason": "time"})

    assert skipped_after >= skipped_before + 1
    assert response.results[0].graph_context is not None
    assert response.results[1].graph_context is None
    assert any("time budget" in warning for warning in response.metadata["warnings"])
