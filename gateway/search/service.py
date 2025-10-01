"""Hybrid search orchestration for Duskmantle's knowledge gateway."""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from neo4j.exceptions import Neo4jError
from qdrant_client import QdrantClient
from qdrant_client.http.models import ScoredPoint, SearchParams

from gateway.graph.service import GraphService, GraphServiceError
from gateway.ingest.embedding import Embedder
from gateway.observability import SEARCH_GRAPH_CACHE_EVENTS, SEARCH_GRAPH_LOOKUP_SECONDS, SEARCH_SCORE_DELTA
from gateway.search.trainer import ModelArtifact

logger = logging.getLogger(__name__)


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


class SearchService:
    """Execute hybrid vector/graph search with heuristic or ML scoring."""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        embedder: Embedder,
        *,
        options: SearchOptions | None = None,
        weights: SearchWeights | None = None,
        model_artifact: ModelArtifact | None = None,
    ) -> None:
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.embedder = embedder
        resolved_options = options or SearchOptions()
        resolved_weights = weights or SearchWeights()

        self.max_limit = resolved_options.max_limit
        self.graph_timeout_seconds = resolved_options.graph_timeout_seconds
        self.weight_subsystem = resolved_weights.subsystem
        self.weight_relationship = resolved_weights.relationship
        self.weight_support = resolved_weights.support
        self.weight_coverage_penalty = resolved_weights.coverage_penalty
        self.weight_criticality = resolved_weights.criticality
        self.vector_weight, self.lexical_weight = _normalise_hybrid_weights(
            resolved_weights.vector,
            resolved_weights.lexical,
        )
        hnsw_value = resolved_options.hnsw_ef_search
        self.hnsw_ef_search = int(hnsw_value) if hnsw_value and hnsw_value > 0 else None
        self.weight_profile = resolved_options.weight_profile
        self.slow_graph_warn_seconds = max(0.0, resolved_options.slow_graph_warn_seconds)
        self.scoring_mode = resolved_options.scoring_mode if model_artifact is not None else "heuristic"
        self._model_artifact = model_artifact if model_artifact and self.scoring_mode == "ml" else None
        if self.scoring_mode == "ml" and self._model_artifact is None:
            logger.warning(
                "Search scoring mode set to 'ml' but no model artifact provided; falling back to heuristic mode",
                extra={"component": "search", "event": "ml_model_missing"},
            )
            self.scoring_mode = "heuristic"

        self._weight_snapshot = {
            "weight_subsystem": self.weight_subsystem,
            "weight_relationship": self.weight_relationship,
            "weight_support": self.weight_support,
            "weight_coverage_penalty": self.weight_coverage_penalty,
            "weight_criticality": self.weight_criticality,
            "vector_weight": self.vector_weight,
            "lexical_weight": self.lexical_weight,
        }

        if self._model_artifact is not None:
            self._model_feature_names = list(getattr(model_artifact, "feature_names", []))
            self._model_coefficients = list(getattr(model_artifact, "coefficients", []))
            self._model_intercept = float(getattr(model_artifact, "intercept", 0.0))
        else:
            self._model_feature_names = []
            self._model_coefficients = []
            self._model_intercept = 0.0

    def search(
        self,
        *,
        query: str,
        limit: int,
        include_graph: bool,
        graph_service: GraphService | None,
        sort_by_vector: bool = False,
        request_id: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> SearchResponse:
        """Execute a hybrid search request and return ranked results."""

        limit = max(1, min(limit, self.max_limit))
        vector = self.embedder.encode([query])[0]
        search_params = SearchParams(hnsw_ef=self.hnsw_ef_search) if self.hnsw_ef_search is not None else None
        try:
            hits: Iterable[ScoredPoint] = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                with_payload=True,
                limit=limit,
                search_params=search_params,
            )
        except Exception as exc:  # pragma: no cover - network errors handled upstream
            logger.error(
                "Search query failed: %s",
                exc,
                extra={"component": "search", "event": "vector_search_error", "request_id": request_id},
            )
            raise

        filter_state = _prepare_filter_state(filters or {})
        results: list[SearchResult] = []
        warnings: list[str] = []
        graph_cache: dict[str, dict[str, Any]] = {}

        query_tokens = _detect_query_subsystems(query)
        graph_context_included = include_graph and graph_service is not None
        recency_required = filter_state.recency_cutoff is not None

        for point in hits:
            payload = point.payload or {}
            if not _passes_payload_filters(payload, filter_state):
                continue

            chunk = _build_chunk(payload, point.score)
            lexical_score = _lexical_score(query, chunk)
            scoring = _base_scoring(
                vector_score=point.score,
                lexical_score=lexical_score,
                vector_weight=self.vector_weight,
                lexical_weight=self.lexical_weight,
            )

            subsystem_value = (payload.get("subsystem") or "").lower()
            subsystem_direct_match = bool(filter_state.allowed_subsystems and subsystem_value in filter_state.allowed_subsystems)

            graph_context_internal, path_depth_value = self._resolve_graph_context(
                payload=payload,
                graph_service=graph_service,
                include_graph=include_graph,
                graph_cache=graph_cache,
                recency_required=recency_required,
                allowed_subsystems=filter_state.allowed_subsystems,
                subsystem_match=subsystem_direct_match,
                request_id=request_id,
                warnings=warnings,
            )

            if filter_state.allowed_subsystems:
                if not subsystem_direct_match:
                    subs_from_context = _subsystems_from_context(graph_context_internal)
                    if not subs_from_context.intersection(filter_state.allowed_subsystems):
                        continue

            if recency_required:
                chunk_datetime = _resolve_chunk_datetime(chunk, graph_context_internal)
                if chunk_datetime is None:
                    if not filter_state.recency_warning_emitted:
                        warnings.append("recency filter skipped results lacking timestamps")
                        filter_state.recency_warning_emitted = True
                    continue
                if filter_state.recency_cutoff and chunk_datetime < filter_state.recency_cutoff:
                    continue

            graph_context_public = graph_context_internal if include_graph else None

            if include_graph and graph_context_internal is not None:
                scoring = _compute_scoring(
                    base_scoring=scoring,
                    vector_score=point.score,
                    lexical_score=lexical_score,
                    vector_weight=self.vector_weight,
                    lexical_weight=self.lexical_weight,
                    query_tokens=query_tokens,
                    chunk=chunk,
                    graph_context=graph_context_internal,
                    weight_subsystem=self.weight_subsystem,
                    weight_relationship=self.weight_relationship,
                    weight_support=self.weight_support,
                    weight_coverage_penalty=self.weight_coverage_penalty,
                    weight_criticality=self.weight_criticality,
                )

            freshness_days_value = _compute_freshness_days(chunk, graph_context_internal)
            scoring = _populate_additional_signals(
                scoring=scoring,
                chunk=chunk,
                graph_context=graph_context_internal,
                path_depth=path_depth_value,
                freshness_days=freshness_days_value,
            )

            try:
                base_components = float(scoring.get("weighted_vector_score", scoring.get("vector_score", 0.0) or 0.0)) + float(
                    scoring.get("weighted_lexical_score", scoring.get("lexical_score", 0.0) or 0.0)
                )
                delta = float(scoring.get("adjusted_score", 0.0)) - base_components
                SEARCH_SCORE_DELTA.observe(delta)
            except (TypeError, ValueError):  # pragma: no cover - defensive guard
                pass

            scoring["mode"] = self.scoring_mode
            if self.scoring_mode == "ml" and self._model_artifact is not None:
                features = self._build_model_features(
                    scoring=scoring,
                    graph_context=graph_context_internal,
                    graph_context_included=graph_context_included,
                    warnings_count=len(warnings),
                )
                try:
                    model_score, contributions = self._apply_model(features)
                except ValueError as exc:  # pragma: no cover - defensive
                    logger.warning(
                        "Model scoring failed; falling back to heuristic",
                        extra={
                            "component": "search",
                            "event": "ml_model_error",
                            "error": str(exc),
                            "request_id": request_id,
                        },
                    )
                    warnings.append("ml scoring unavailable")
                else:
                    scoring["model"] = {
                        "score": model_score,
                        "intercept": self._model_intercept,
                        "contributions": contributions,
                    }
                    scoring["adjusted_score"] = model_score

            results.append(SearchResult(chunk=chunk, graph_context=graph_context_public, scoring=scoring))

        if sort_by_vector:
            results.sort(key=lambda r: r.scoring.get("vector_score", 0.0), reverse=True)
        else:
            results.sort(
                key=lambda r: r.scoring.get("adjusted_score", r.scoring.get("vector_score", 0.0)),
                reverse=True,
            )

        metadata = {
            "result_count": len(results),
            "graph_context_included": include_graph and graph_service is not None,
            "warnings": warnings,
            "scoring_mode": self.scoring_mode,
            "weight_profile": self.weight_profile,
            "weights": self._weight_snapshot,
            "hybrid_weights": {
                "vector": self.vector_weight,
                "lexical": self.lexical_weight,
            },
        }
        if self.hnsw_ef_search is not None:
            metadata["hnsw_ef_search"] = self.hnsw_ef_search
        if filter_state.filters_applied:
            metadata["filters_applied"] = filter_state.filters_applied
        if request_id:
            metadata["request_id"] = request_id
        return SearchResponse(query=query, results=results, metadata=metadata)

    def _resolve_graph_context(
        self,
        *,
        payload: dict[str, Any],
        graph_service: GraphService | None,
        include_graph: bool,
        graph_cache: dict[str, dict[str, Any]],
        recency_required: bool,
        allowed_subsystems: set[str],
        subsystem_match: bool,
        request_id: str | None,
        warnings: list[str],
    ) -> tuple[dict[str, Any] | None, float | None]:
        """Fetch and cache graph context for a search result chunk."""

        if not graph_service or not payload.get("path"):
            return None, None

        node_label = _label_for_artifact(payload.get("artifact_type"))
        node_id = f"{node_label}:{payload.get('path')}"
        cache_entry = graph_cache.get(node_id)
        needs_timestamp = recency_required and not payload.get("git_timestamp") and include_graph
        fetch_graph = include_graph or (allowed_subsystems and not subsystem_match) or needs_timestamp

        graph_context_internal: dict[str, Any] | None = None
        path_depth_value: float | None = None

        if fetch_graph and cache_entry is None:
            lookup_started = time.perf_counter()
            try:
                node_data = graph_service.get_node(
                    node_id,
                    relationships="all",
                    limit=10,
                )
                graph_context_internal = _summarize_graph_context(node_data)
                cache_entry = {"graph_context": graph_context_internal, "path_depth": None}
                graph_cache[node_id] = cache_entry
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
                        "request_id": request_id,
                    },
                )
                warnings.append(str(exc))
                cache_entry = {"graph_context": None, "path_depth": None}
                graph_cache[node_id] = cache_entry
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
                        "request_id": request_id,
                    },
                )
                warnings.append("graph context lookup failed")
                cache_entry = {"graph_context": None, "path_depth": None}
                graph_cache[node_id] = cache_entry
            else:
                lookup_duration = time.perf_counter() - lookup_started
                SEARCH_GRAPH_LOOKUP_SECONDS.observe(lookup_duration)
                if lookup_duration > self.slow_graph_warn_seconds:
                    logger.warning(
                        "Graph lookup slow",
                        extra={
                            "component": "search",
                            "event": "graph_lookup_slow",
                            "node_id": node_id,
                            "lookup_seconds": lookup_duration,
                            "request_id": request_id,
                        },
                    )
                path_depth_lookup: float | None = None
                try:
                    depth = graph_service.shortest_path_depth(node_id, max_depth=4)
                    if depth is not None:
                        path_depth_lookup = float(depth)
                except GraphServiceError as exc:
                    logger.warning(
                        "Graph path depth unavailable",
                        extra={
                            "component": "search",
                            "event": "graph_path_depth_missing",
                            "node_id": node_id,
                            "error": str(exc),
                            "request_id": request_id,
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
                            "request_id": request_id,
                        },
                    )
                    warnings.append("graph path depth error")
                cache_entry["path_depth"] = path_depth_lookup
                path_depth_value = path_depth_lookup
        elif cache_entry is not None:
            SEARCH_GRAPH_CACHE_EVENTS.labels(status="hit").inc()
            graph_context_internal = cache_entry.get("graph_context")
            path_depth_value = cache_entry.get("path_depth")

        if graph_context_internal is None and cache_entry is not None:
            graph_context_internal = cache_entry.get("graph_context")
            if path_depth_value is None:
                path_depth_value = cache_entry.get("path_depth")

        return graph_context_internal, path_depth_value

    def _build_model_features(
        self,
        *,
        scoring: dict[str, Any],
        graph_context: dict[str, Any] | None,
        graph_context_included: bool,
        warnings_count: int,
    ) -> dict[str, float]:
        signals = scoring.get("signals", {})
        features: dict[str, float] = {
            "vector_score": float(scoring.get("vector_score", 0.0) or 0.0),
            "lexical_score": float(scoring.get("lexical_score", 0.0) or 0.0),
            "weighted_vector_score": float(scoring.get("weighted_vector_score", scoring.get("vector_score", 0.0) or 0.0)),
            "weighted_lexical_score": float(scoring.get("weighted_lexical_score", scoring.get("lexical_score", 0.0) or 0.0)),
            "signal_subsystem_affinity": float(signals.get("subsystem_affinity", 0.0) or 0.0),
            "signal_relationship_count": float(signals.get("relationship_count", 0.0) or 0.0),
            "signal_supporting_bonus": float(signals.get("supporting_bonus", 0.0) or 0.0),
            "signal_coverage_missing": float(signals.get("coverage_missing", 0.0) or 0.0),
            "signal_coverage_ratio": float(signals.get("coverage_ratio", 0.0) or 0.0),
            "signal_criticality_score": float(signals.get("criticality_score", 0.0) or 0.0),
            "signal_path_depth": float(signals.get("path_depth", 0.0) or 0.0),
            "graph_context_present": 1.0 if graph_context else 0.0,
            "metadata_graph_context_included": 1.0 if graph_context_included else 0.0,
            "metadata_warnings_count": float(warnings_count),
        }
        return features

    def _apply_model(self, features: dict[str, float]) -> tuple[float, dict[str, float]]:
        missing = [name for name in self._model_feature_names if name not in features]
        if missing:
            raise ValueError(f"Missing features for model scoring: {missing}")
        contributions: dict[str, float] = {}
        score = self._model_intercept
        for coeff, name in zip(self._model_coefficients, self._model_feature_names, strict=False):
            value = features[name]
            contrib = coeff * value
            contributions[name] = contrib
            score += contrib
        return score, contributions


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


def _subsystems_from_context(graph_context: dict[str, Any] | None) -> set[str]:
    if not graph_context:
        return set()
    subsystems: set[str] = set()
    primary = graph_context.get("primary_node", {})
    props = primary.get("properties") or {}
    for key in ("subsystem", "name"):
        value = props.get(key)
        if isinstance(value, str) and value.strip():
            subsystems.add(value.strip().lower())
            break
    neighbor = graph_context.get("neighbor_subsystems") or []
    for value in neighbor:
        if isinstance(value, str) and value.strip():
            subsystems.add(value.strip().lower())
    return subsystems


def _detect_query_subsystems(query: str) -> set[str]:
    tokens = {token for token in re.split(r"[^a-zA-Z0-9]+", query.lower()) if token}
    return tokens


def _normalise_hybrid_weights(vector_weight: float, lexical_weight: float) -> tuple[float, float]:
    vector = max(0.0, float(vector_weight))
    lexical = max(0.0, float(lexical_weight))
    if (vector + lexical) <= 0.0:
        vector = 1.0
    return vector, lexical


def _prepare_filter_state(filters: dict[str, Any]) -> FilterState:
    if not isinstance(filters, dict):
        filters = dict(filters) if hasattr(filters, "items") else {}

    raw_subsystems = filters.get("subsystems") or []
    raw_types = filters.get("artifact_types") or []
    raw_namespaces = filters.get("namespaces") or []
    raw_tags = filters.get("tags") or []
    updated_after_filter = filters.get("updated_after")
    max_age_filter = filters.get("max_age_days")

    allowed_subsystems = {str(value).strip().lower() for value in raw_subsystems if isinstance(value, str)}
    allowed_types = {str(value).strip().lower() for value in raw_types if isinstance(value, str)}
    allowed_namespaces = {str(value).strip().lower() for value in raw_namespaces if isinstance(value, str)}
    allowed_tags = {str(value).strip().lower() for value in raw_tags if isinstance(value, str)}

    parsed_updated_after: datetime | None = None
    if isinstance(updated_after_filter, datetime):
        parsed_updated_after = updated_after_filter.astimezone(UTC)
    elif isinstance(updated_after_filter, str):
        parsed_updated_after = _parse_iso_datetime(updated_after_filter)

    recency_cutoff: datetime | None = parsed_updated_after
    recency_max_age_days: float | None = None
    if max_age_filter is not None:
        try:
            recency_max_age_days = float(max_age_filter)
        except (TypeError, ValueError):
            recency_max_age_days = None
    if recency_max_age_days is not None:
        now = datetime.now(UTC)
        age_cutoff = now - timedelta(days=recency_max_age_days)
        if recency_cutoff is None or age_cutoff > recency_cutoff:
            recency_cutoff = age_cutoff

    filters_applied: dict[str, Any] = {}
    if allowed_subsystems:
        filters_applied["subsystems"] = sorted(
            {str(value).strip() for value in raw_subsystems if isinstance(value, str) and value.strip()},
        )
    if allowed_types:
        filters_applied["artifact_types"] = sorted(
            {str(value).strip().lower() for value in raw_types if isinstance(value, str) and value.strip()},
        )
    if allowed_namespaces:
        filters_applied["namespaces"] = sorted(
            {str(value).strip() for value in raw_namespaces if isinstance(value, str) and value.strip()},
        )
    if allowed_tags:
        filters_applied["tags"] = sorted(
            {str(value).strip() for value in raw_tags if isinstance(value, str) and value.strip()},
        )
    if parsed_updated_after is not None:
        filters_applied["updated_after"] = parsed_updated_after.astimezone(UTC).isoformat()
    if max_age_filter is not None:
        try:
            filters_applied["max_age_days"] = int(max_age_filter)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            pass

    return FilterState(
        allowed_subsystems=allowed_subsystems,
        allowed_types=allowed_types,
        allowed_namespaces=allowed_namespaces,
        allowed_tags=allowed_tags,
        filters_applied=filters_applied,
        recency_cutoff=recency_cutoff,
    )


def _passes_payload_filters(payload: dict[str, Any], state: FilterState) -> bool:
    artifact_type = (payload.get("artifact_type") or "").lower()
    if state.allowed_types and artifact_type not in state.allowed_types:
        return False

    namespace_value = (payload.get("namespace") or "").strip().lower()
    if state.allowed_namespaces and namespace_value not in state.allowed_namespaces:
        return False

    if state.allowed_tags:
        payload_tags = _normalise_payload_tags(payload.get("tags"))
        if not payload_tags.intersection(state.allowed_tags):
            return False

    return True


def _normalise_payload_tags(raw_tags: Sequence[object] | set[object] | None) -> set[str]:
    if isinstance(raw_tags, (list, tuple, set)):
        return {str(tag).strip().lower() for tag in raw_tags if str(tag).strip()}
    return set()


def _build_chunk(payload: dict[str, Any], score: float) -> dict[str, Any]:
    return {
        "chunk_id": payload.get("chunk_id"),
        "artifact_path": payload.get("path"),
        "artifact_type": payload.get("artifact_type"),
        "subsystem": payload.get("subsystem"),
        "namespace": payload.get("namespace"),
        "tags": payload.get("tags"),
        "text": payload.get("text"),
        "coverage_missing": bool(payload.get("coverage_missing")),
        "score": score,
        "subsystem_criticality": payload.get("subsystem_criticality"),
        "coverage_ratio": payload.get("coverage_ratio"),
        "git_timestamp": payload.get("git_timestamp"),
    }


def _calculate_subsystem_affinity(subsystem: str, query_tokens: set[str]) -> float:
    if not subsystem:
        return 0.0
    if subsystem in query_tokens:
        return 1.0
    if any(subsystem in token or token in subsystem for token in query_tokens):
        return 0.5
    return 0.0


def _calculate_supporting_bonus(related_artifacts: Iterable[dict[str, Any]]) -> float:
    design_docs = 0
    test_cases = 0
    for item in related_artifacts:
        identifier = item.get("id", "")
        if isinstance(identifier, str) and identifier.startswith("DesignDoc:"):
            design_docs += 1
        elif isinstance(identifier, str) and identifier.startswith("TestCase:"):
            test_cases += 1
    return min(design_docs, 2) * 0.2 + min(test_cases, 2) * 0.1


def _calculate_coverage_info(chunk: dict[str, Any], weight_coverage_penalty: float) -> CoverageInfo:
    coverage_missing_flag = 1.0 if chunk.get("coverage_missing") else 0.0
    coverage_ratio_raw = chunk.get("coverage_ratio")
    coverage_ratio = _coerce_ratio_value(coverage_ratio_raw)
    if coverage_ratio is None:
        coverage_ratio = 0.0 if coverage_missing_flag else 1.0
    penalty = weight_coverage_penalty * (1.0 - coverage_ratio)
    return CoverageInfo(ratio=coverage_ratio, penalty=penalty, missing_flag=coverage_missing_flag)


def _coerce_ratio_value(value: object) -> float | None:
    if isinstance(value, bool):
        # Prevent bools masquerading as integers
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            numeric = float(text)
        except ValueError:
            return None
        return max(0.0, min(1.0, numeric))
    return None


def _calculate_criticality_score(chunk: dict[str, Any], graph_context: dict[str, Any] | None) -> float:
    criticality_value = chunk.get("subsystem_criticality")
    if criticality_value is None:
        criticality_value = _extract_subsystem_criticality(graph_context)
    return _normalise_criticality(criticality_value)


def _update_path_depth_signal(
    signals: dict[str, Any],
    path_depth: float | None,
    graph_context: dict[str, Any] | None,
) -> None:
    value = path_depth if path_depth is not None else _estimate_path_depth(graph_context)
    if value is not None:
        try:
            signals["path_depth"] = float(value)
        except (TypeError, ValueError):
            signals["path_depth"] = None
    else:
        signals["path_depth"] = None


def _ensure_criticality_signal(
    signals: dict[str, Any],
    chunk: dict[str, Any],
    graph_context: dict[str, Any] | None,
) -> None:
    if "criticality_score" not in signals:
        signals["criticality_score"] = _calculate_criticality_score(chunk, graph_context)
    signals.setdefault("subsystem_criticality", signals.get("criticality_score"))


def _ensure_freshness_signal(
    signals: dict[str, Any],
    chunk: dict[str, Any],
    graph_context: dict[str, Any] | None,
    freshness_days: float | None,
) -> None:
    if freshness_days is None:
        freshness_days = _compute_freshness_days(chunk, graph_context)
    signals["freshness_days"] = freshness_days


def _ensure_coverage_ratio_signal(signals: dict[str, Any], chunk: dict[str, Any]) -> None:
    if "coverage_ratio" in signals:
        return
    coverage_ratio = chunk.get("coverage_ratio")
    if coverage_ratio is None:
        coverage_ratio = 0.0 if signals.get("coverage_missing") else 1.0
    try:
        signals["coverage_ratio"] = float(coverage_ratio)
    except (TypeError, ValueError):
        signals["coverage_ratio"] = None


_TOKEN_PATTERN = re.compile(r"\w+", flags=re.ASCII)


def _lexical_score(query: str, chunk: dict[str, Any]) -> float:
    query_terms = {_token for _token in _TOKEN_PATTERN.findall(query.lower()) if _token}
    if not query_terms:
        return 0.0

    doc_tokens: set[str] = set()
    text = chunk.get("text") or ""
    doc_tokens.update(_TOKEN_PATTERN.findall(text.lower()))
    artifact_path = chunk.get("artifact_path") or ""
    doc_tokens.update(_TOKEN_PATTERN.findall(str(artifact_path).lower()))
    tags = chunk.get("tags")
    if isinstance(tags, (list, tuple)):
        doc_tokens.update(_TOKEN_PATTERN.findall(" ".join(str(tag).lower() for tag in tags)))
    elif isinstance(tags, str):
        doc_tokens.update(_TOKEN_PATTERN.findall(tags.lower()))

    doc_tokens = {token for token in doc_tokens if token}
    if not doc_tokens:
        return 0.0

    matches = 0.0
    for term in query_terms:
        if term in doc_tokens:
            matches += 1.0
        else:
            # Partial overlap bonus
            if any(term in token or token in term for token in doc_tokens):
                matches += 0.5

    score = matches / len(query_terms)
    return max(0.0, min(1.0, score))


def _base_scoring(
    vector_score: float,
    lexical_score: float,
    vector_weight: float,
    lexical_weight: float,
) -> dict[str, Any]:
    weighted_vector = vector_weight * vector_score
    weighted_lexical = lexical_weight * lexical_score
    base_adjusted = weighted_vector + weighted_lexical
    return {
        "vector_score": vector_score,
        "lexical_score": lexical_score,
        "weighted_vector_score": weighted_vector,
        "weighted_lexical_score": weighted_lexical,
        "adjusted_score": base_adjusted,
        "signals": {
            "lexical_score": lexical_score,
            "weighted_vector_component": weighted_vector,
            "weighted_lexical_component": weighted_lexical,
        },
    }


def _compute_scoring(
    *,
    base_scoring: dict[str, Any],
    vector_score: float,
    lexical_score: float,
    vector_weight: float,
    lexical_weight: float,
    query_tokens: set[str],
    chunk: dict[str, Any],
    graph_context: dict[str, Any],
    weight_subsystem: float,
    weight_relationship: float,
    weight_support: float,
    weight_coverage_penalty: float,
    weight_criticality: float,
) -> dict[str, Any]:
    scoring = base_scoring
    signals = scoring.setdefault("signals", {})
    signals.setdefault("lexical_score", lexical_score)
    signals.setdefault("weighted_vector_component", vector_weight * vector_score)
    signals.setdefault("weighted_lexical_component", lexical_weight * lexical_score)

    subsystem = (chunk.get("subsystem") or "").lower()
    subsystem_affinity = _calculate_subsystem_affinity(subsystem, query_tokens)
    relationship_count = len(graph_context.get("relationships", []))
    supporting_bonus = _calculate_supporting_bonus(graph_context.get("related_artifacts", []))
    coverage_info = _calculate_coverage_info(chunk, weight_coverage_penalty)
    criticality_score = _calculate_criticality_score(chunk, graph_context)

    base_adjusted_score = scoring.get(
        "adjusted_score",
        (vector_weight * vector_score) + (lexical_weight * lexical_score),
    )

    adjusted_score = (
        base_adjusted_score
        + weight_subsystem * subsystem_affinity
        + weight_relationship * min(relationship_count, 5)
        + weight_support * supporting_bonus
        + weight_criticality * criticality_score
        - coverage_info.penalty
    )

    signals.update(
        {
            "subsystem_affinity": subsystem_affinity,
            "relationship_count": relationship_count,
            "supporting_bonus": supporting_bonus,
            "coverage_missing": coverage_info.missing_flag,
            "coverage_ratio": coverage_info.ratio,
            "criticality_score": criticality_score,
            "coverage_penalty": coverage_info.penalty,
        }
    )
    scoring["adjusted_score"] = adjusted_score
    return scoring


def _populate_additional_signals(
    *,
    scoring: dict[str, Any],
    chunk: dict[str, Any],
    graph_context: dict[str, Any] | None,
    path_depth: float | None,
    freshness_days: float | None,
) -> dict[str, Any]:
    signals = scoring.setdefault("signals", {})

    _update_path_depth_signal(signals, path_depth, graph_context)
    _ensure_criticality_signal(signals, chunk, graph_context)
    _ensure_freshness_signal(signals, chunk, graph_context, freshness_days)
    _ensure_coverage_ratio_signal(signals, chunk)

    return scoring


def _estimate_path_depth(graph_context: dict[str, Any] | None) -> float:
    if not graph_context:
        return 0.0
    relationships = graph_context.get("relationships") or []
    if any(rel.get("type") == "BELONGS_TO" for rel in relationships):
        return 1.0
    return 0.0


def _extract_subsystem_criticality(graph_context: dict[str, Any] | None) -> str | None:
    if not graph_context:
        return None
    primary = graph_context.get("primary_node", {})
    props = primary.get("properties") or {}
    if props.get("criticality"):
        return props.get("criticality")
    relationships = graph_context.get("relationships") or []
    for rel in relationships:
        target_props = rel.get("target", {}).get("properties") or {}
        if target_props.get("criticality"):
            return target_props.get("criticality")
    return None


def _normalise_criticality(value: str | float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    lookup = {
        "low": 0.2,
        "medium": 0.5,
        "high": 0.8,
        "critical": 1.0,
    }
    return lookup.get(str(value).lower(), 0.0)


def _compute_freshness_days(
    chunk: dict[str, Any],
    graph_context: dict[str, Any] | None,
) -> float | None:
    timestamp = chunk.get("git_timestamp") or chunk.get("last_modified") or chunk.get("last_modified_at") or chunk.get("updated_at")
    if timestamp is None and graph_context:
        primary = graph_context.get("primary_node", {})
        props = primary.get("properties") or {}
        timestamp = props.get("git_timestamp") or props.get("last_modified") or props.get("updated_at")
    parsed = _parse_iso_datetime(timestamp)
    if parsed is None:
        return None
    delta = datetime.now(UTC) - parsed
    return max(delta.total_seconds() / 86400.0, 0.0)


def _resolve_chunk_datetime(
    chunk: dict[str, Any],
    graph_context: dict[str, Any] | None,
) -> datetime | None:
    candidates = [
        chunk.get("git_timestamp"),
        chunk.get("last_modified"),
        chunk.get("last_modified_at"),
        chunk.get("updated_at"),
    ]
    if graph_context:
        primary = graph_context.get("primary_node", {})
        props = primary.get("properties") or {}
        candidates.extend(
            [
                props.get("git_timestamp"),
                props.get("last_modified"),
                props.get("updated_at"),
            ]
        )
    for value in candidates:
        parsed = _parse_iso_datetime(value)
        if parsed is not None:
            return parsed
    return None


def _parse_iso_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
