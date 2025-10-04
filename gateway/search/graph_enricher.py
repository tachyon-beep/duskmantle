"""Graph enrichment helpers for search results."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from neo4j.exceptions import Neo4jError

from gateway.graph.service import GraphService, GraphServiceError
from gateway.observability import (
    SEARCH_GRAPH_CACHE_EVENTS,
    SEARCH_GRAPH_LOOKUP_SECONDS,
    SEARCH_GRAPH_SKIPPED_TOTAL,
)
from gateway.search.models import FilterState

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GraphEnrichmentResult:
    """Graph enrichment output for a single search hit."""

    graph_context: dict[str, Any] | None
    path_depth: float | None


class GraphEnricher:
    """Manage graph lookups with caching, budgets, and telemetry."""

    def __init__(
        self,
        *,
        graph_service: GraphService | None,
        include_graph: bool,
        filter_state: FilterState,
        graph_max_results: int,
        time_budget_seconds: float,
        slow_warn_seconds: float,
        request_id: str | None,
    ) -> None:
        self._graph_service = graph_service
        self._include_graph = include_graph
        self._has_subsystem_filters = bool(filter_state.allowed_subsystems)
        self._recency_required = filter_state.recency_cutoff is not None
        self._graph_cache: dict[str, dict[str, Any]] = {}
        self._slots_remaining = max(0, graph_max_results)
        self._deadline = (
            time.perf_counter() + time_budget_seconds
            if include_graph and time_budget_seconds > 0 and graph_service is not None
            else None
        )
        self._time_budget_exhausted = False
        self._slot_budget_exhausted = False
        self._slow_warn_seconds = max(0.0, slow_warn_seconds)
        self._request_id = request_id

    @property
    def slots_exhausted(self) -> bool:
        return self._slot_budget_exhausted

    @property
    def time_exhausted(self) -> bool:
        return self._time_budget_exhausted

    def resolve(
        self,
        payload: dict[str, Any],
        *,
        subsystem_match: bool,
        warnings: list[str],
    ) -> GraphEnrichmentResult:
        """Return graph context for a payload, respecting budgets and cache."""

        graph_service = self._graph_service
        if graph_service is None or not payload.get("path"):
            return GraphEnrichmentResult(graph_context=None, path_depth=None)

        node_label = _label_for_artifact(payload.get("artifact_type"))
        node_id = f"{node_label}:{payload.get('path')}"
        cache_entry = self._graph_cache.get(node_id)

        needs_timestamp = self._recency_required and not payload.get("git_timestamp") and self._include_graph
        fetch_graph = self._include_graph or (self._has_subsystem_filters and not subsystem_match) or needs_timestamp

        if not fetch_graph:
            if cache_entry is not None:
                SEARCH_GRAPH_CACHE_EVENTS.labels(status="hit").inc()
                return GraphEnrichmentResult(
                    graph_context=cache_entry.get("graph_context"),
                    path_depth=cache_entry.get("path_depth"),
                )
            return GraphEnrichmentResult(graph_context=None, path_depth=None)

        if self._time_budget_exhausted:
            SEARCH_GRAPH_SKIPPED_TOTAL.labels(reason="time").inc()
            return GraphEnrichmentResult(graph_context=None, path_depth=None)

        if self._slots_remaining <= 0:
            self._slot_budget_exhausted = True
            SEARCH_GRAPH_SKIPPED_TOTAL.labels(reason="limit").inc()
            return GraphEnrichmentResult(graph_context=None, path_depth=None)

        if self._deadline is not None and time.perf_counter() >= self._deadline:
            self._time_budget_exhausted = True
            SEARCH_GRAPH_SKIPPED_TOTAL.labels(reason="time").inc()
            return GraphEnrichmentResult(graph_context=None, path_depth=None)

        lookup_started = time.perf_counter()
        graph_context_internal: dict[str, Any] | None = None
        path_depth_value: float | None = None

        fetched = False

        if cache_entry is not None:
            SEARCH_GRAPH_CACHE_EVENTS.labels(status="hit").inc()
            graph_context_internal = cache_entry.get("graph_context")
            path_depth_value = cache_entry.get("path_depth")
        else:
            fetched = True
            try:
                node_data = graph_service.get_node(
                    node_id,
                    relationships="all",
                    limit=10,
                )
                graph_context_internal = _summarize_graph_context(node_data)
                cache_entry = {"graph_context": graph_context_internal, "path_depth": None}
                self._graph_cache[node_id] = cache_entry
                SEARCH_GRAPH_CACHE_EVENTS.labels(status="miss").inc()
            except GraphServiceError as exc:
                lookup_duration = time.perf_counter() - lookup_started
                SEARCH_GRAPH_LOOKUP_SECONDS.observe(lookup_duration)
                SEARCH_GRAPH_CACHE_EVENTS.labels(status="error").inc()
                logger.warning(
                    "Graph context unavailable",
                    extra={
                        "component": "search",
                        "event": "graph_context_missing",
                        "node_id": node_id,
                        "error": str(exc),
                        "request_id": self._request_id,
                    },
                )
                warnings.append(str(exc))
                cache_entry = {"graph_context": None, "path_depth": None}
                self._graph_cache[node_id] = cache_entry
            except Neo4jError as exc:  # pragma: no cover - defensive
                lookup_duration = time.perf_counter() - lookup_started
                SEARCH_GRAPH_LOOKUP_SECONDS.observe(lookup_duration)
                SEARCH_GRAPH_CACHE_EVENTS.labels(status="error").inc()
                logger.warning(
                    "Unexpected graph error",
                    extra={
                        "component": "search",
                        "event": "graph_context_error",
                        "node_id": node_id,
                        "error": str(exc),
                        "request_id": self._request_id,
                    },
                )
                warnings.append("graph context lookup failed")
                cache_entry = {"graph_context": None, "path_depth": None}
                self._graph_cache[node_id] = cache_entry
            else:
                lookup_duration = time.perf_counter() - lookup_started
                SEARCH_GRAPH_LOOKUP_SECONDS.observe(lookup_duration)
                if lookup_duration > self._slow_warn_seconds:
                    logger.warning(
                        "Graph lookup slow",
                        extra={
                            "component": "search",
                            "event": "graph_lookup_slow",
                            "node_id": node_id,
                            "lookup_seconds": lookup_duration,
                            "request_id": self._request_id,
                        },
                    )
                try:
                    depth = graph_service.shortest_path_depth(node_id, max_depth=4)
                    if depth is not None:
                        path_depth_value = float(depth)
                        cache_entry["path_depth"] = path_depth_value
                except GraphServiceError as exc:
                    logger.warning(
                        "Graph path depth unavailable",
                        extra={
                            "component": "search",
                            "event": "graph_path_depth_missing",
                            "node_id": node_id,
                            "error": str(exc),
                            "request_id": self._request_id,
                        },
                    )
                    warnings.append("graph path depth unavailable")
                except Neo4jError as exc:  # pragma: no cover - defensive
                    logger.warning(
                        "Graph path depth error",
                        extra={
                            "component": "search",
                            "event": "graph_path_depth_error",
                            "node_id": node_id,
                            "error": str(exc),
                            "request_id": self._request_id,
                        },
                    )
                    warnings.append("graph path depth error")

        if fetched and self._slots_remaining > 0:
            self._slots_remaining -= 1
        if self._deadline is not None and time.perf_counter() > self._deadline:
            self._time_budget_exhausted = True

        if cache_entry is not None and graph_context_internal is None:
            graph_context_internal = cache_entry.get("graph_context")
            if path_depth_value is None:
                path_depth_value = cache_entry.get("path_depth")

        return GraphEnrichmentResult(graph_context=graph_context_internal, path_depth=path_depth_value)


def _label_for_artifact(artifact_type: str | None) -> str:
    mapping = {
        "doc": "DesignDoc",
        "code": "SourceFile",
        "test": "TestCase",
        "proto": "SourceFile",
        "config": "SourceFile",
    }
    return mapping.get(artifact_type or "", "SourceFile")


def _summarize_graph_context(data: dict[str, Any]) -> dict[str, Any]:
    node = data.get("node", {})
    relationships = data.get("relationships", [])

    neighbor_subsystems = sorted(
        {
            rel.get("target", {}).get("properties", {}).get("name")
            for rel in relationships
            if "Subsystem" in rel.get("target", {}).get("labels", [])
        }
        - {None}
    )

    related_artifacts = [
        {
            "id": rel.get("target", {}).get("id"),
            "relationship": rel.get("type"),
        }
        for rel in relationships
        if rel.get("type") in {"DESCRIBES", "VALIDATES"}
    ]

    return {
        "primary_node": node,
        "relationships": relationships,
        "neighbor_subsystems": neighbor_subsystems,
        "related_artifacts": related_artifacts,
    }


__all__ = ["GraphEnricher", "GraphEnrichmentResult"]
