"""Shared dataclasses and type helpers for search components."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal


@dataclass(slots=True)
class SearchResult:
    """Single ranked chunk returned from the search pipeline."""

    chunk: dict[str, Any]
    graph_context: dict[str, Any] | None
    scoring: dict[str, Any]


@dataclass(slots=True)
class SearchResponse:
    """API-friendly container for search results and metadata."""

    query: str
    results: list[SearchResult]
    metadata: dict[str, Any]


@dataclass(slots=True)
class SearchOptions:
    """Runtime options controlling the search service behaviour."""

    max_limit: int = 25
    graph_timeout_seconds: float = 0.25
    graph_time_budget_seconds: float = 0.75
    graph_max_results: int = 20
    hnsw_ef_search: int | None = None
    scoring_mode: Literal["heuristic", "ml"] = "heuristic"
    weight_profile: str = "custom"
    slow_graph_warn_seconds: float = 0.25


@dataclass(slots=True)
class SearchWeights:
    """Weighting configuration for hybrid scoring."""

    subsystem: float = 0.30
    relationship: float = 0.05
    support: float = 0.10
    coverage_penalty: float = 0.15
    criticality: float = 0.12
    vector: float = 1.0
    lexical: float = 0.25


@dataclass(slots=True)
class FilterState:
    """Preprocessed filter collections derived from request parameters."""

    allowed_subsystems: set[str]
    allowed_types: set[str]
    allowed_namespaces: set[str]
    allowed_tags: set[str]
    filters_applied: dict[str, Any]
    recency_cutoff: datetime | None
    recency_warning_emitted: bool = False


@dataclass(slots=True)
class CoverageInfo:
    """Coverage characteristics used during scoring."""

    ratio: float
    penalty: float
    missing_flag: float


def ensure_utc(dt: datetime) -> datetime:
    """Normalise datetimes to UTC for serialisation."""

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


__all__ = [
    "SearchResult",
    "SearchResponse",
    "SearchOptions",
    "SearchWeights",
    "FilterState",
    "CoverageInfo",
    "ensure_utc",
]
