"""Hybrid search orchestration for Duskmantle's knowledge gateway."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import ScoredPoint

from gateway.graph.service import GraphService
from gateway.ingest.embedding import Embedder
from gateway.observability import SEARCH_SCORE_DELTA
from gateway.search.filtering import build_filter_state, parse_iso_datetime, payload_passes_filters
from gateway.search.graph_enricher import GraphEnricher
from gateway.search.ml import ModelScorer
from gateway.search.models import (
    SearchOptions,
    SearchResponse,
    SearchResult,
    SearchWeights,
)
from gateway.search.scoring import HeuristicScorer
from gateway.search.trainer import ModelArtifact
from gateway.search.vector_retriever import VectorRetrievalError, VectorRetriever

logger = logging.getLogger(__name__)


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
        failure_callback: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialise the search service with vector and scoring options."""
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.embedder = embedder
        self._failure_callback = failure_callback
        resolved_options = options or SearchOptions()
        resolved_weights = weights or SearchWeights()

        self.max_limit = resolved_options.max_limit
        self.graph_timeout_seconds = resolved_options.graph_timeout_seconds
        self.graph_time_budget_seconds = max(0.0, resolved_options.graph_time_budget_seconds)
        self.graph_max_results = max(0, resolved_options.graph_max_results)
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

        self._scorer = HeuristicScorer(
            weights=resolved_weights,
            vector_weight=self.vector_weight,
            lexical_weight=self.lexical_weight,
        )
        self._model_scorer = ModelScorer(self._model_artifact)

        self._vector_retriever = VectorRetriever(
            embedder=embedder,
            qdrant_client=qdrant_client,
            collection_name=collection_name,
            hnsw_ef_search=self.hnsw_ef_search,
            failure_callback=failure_callback,
        )

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
        try:
            hits: Iterable[ScoredPoint] = self._vector_retriever.search(
                query=query,
                limit=limit,
                request_id=request_id,
            )
        except VectorRetrievalError:
            raise

        filter_state = build_filter_state(filters or {})
        results: list[SearchResult] = []
        warnings: list[str] = []

        query_tokens = _detect_query_subsystems(query)
        graph_context_included = include_graph and graph_service is not None
        recency_required = filter_state.recency_cutoff is not None
        enricher = GraphEnricher(
            graph_service=graph_service,
            include_graph=include_graph,
            filter_state=filter_state,
            graph_max_results=self.graph_max_results,
            time_budget_seconds=self.graph_time_budget_seconds,
            slow_warn_seconds=self.slow_graph_warn_seconds,
            request_id=request_id,
        )

        for point in hits:
            payload = point.payload or {}
            if not payload_passes_filters(payload, filter_state):
                continue

            chunk = self._scorer.build_chunk(payload, point.score)
            lexical_score = self._scorer.lexical_score(query, chunk)
            scoring = self._scorer.base_scoring(
                vector_score=point.score,
                lexical_score=lexical_score,
            )

            subsystem_value = (payload.get("subsystem") or "").lower()
            subsystem_direct_match = bool(filter_state.allowed_subsystems and subsystem_value in filter_state.allowed_subsystems)

            graph_result = enricher.resolve(
                payload=payload,
                subsystem_match=subsystem_direct_match,
                warnings=warnings,
            )
            graph_context_internal = graph_result.graph_context
            path_depth_value = graph_result.path_depth

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
                scoring = self._scorer.apply_graph_scoring(
                    base_scoring=scoring,
                    vector_score=point.score,
                    lexical_score=lexical_score,
                    query_tokens=query_tokens,
                    chunk=chunk,
                    graph_context=graph_context_internal,
                )

            freshness_days_value = self._scorer.compute_freshness_days(chunk, graph_context_internal)
            scoring = self._scorer.populate_additional_signals(
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
            if self.scoring_mode == "ml" and self._model_scorer.available:
                try:
                    model_result = self._model_scorer.score(
                        scoring=scoring,
                        graph_context=graph_context_internal,
                        graph_context_included=graph_context_included,
                        warnings_count=len(warnings),
                    )
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
                        "score": model_result.score,
                        "intercept": self._model_scorer.intercept,
                        "contributions": model_result.contributions,
                    }
                    scoring["adjusted_score"] = model_result.score

            results.append(SearchResult(chunk=chunk, graph_context=graph_context_public, scoring=scoring))

        if sort_by_vector:
            results.sort(key=lambda r: r.scoring.get("vector_score", 0.0), reverse=True)
        else:
            results.sort(
                key=lambda r: r.scoring.get("adjusted_score", r.scoring.get("vector_score", 0.0)),
                reverse=True,
            )

        metadata: dict[str, Any] = {
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
        if enricher.slots_exhausted:
            metadata["warnings"].append(
                f"graph context limited to first {max(1, self.graph_max_results)} results",
            )
        if enricher.time_exhausted:
            metadata["warnings"].append("graph context skipped after exceeding time budget")
        return SearchResponse(query=query, results=results, metadata=metadata)


def _subsystems_from_context(graph_context: dict[str, Any] | None) -> set[str]:
    """Extract subsystem identifiers from cached graph context."""
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
    """Tokenise the query to detect subsystem keywords for affinity scoring."""
    tokens = {token for token in re.split(r"[^a-zA-Z0-9]+", query.lower()) if token}
    return tokens


def _normalise_hybrid_weights(vector_weight: float, lexical_weight: float) -> tuple[float, float]:
    vector = max(0.0, float(vector_weight))
    lexical = max(0.0, float(lexical_weight))
    if (vector + lexical) <= 0.0:
        vector = 1.0
    return vector, lexical










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
        parsed = parse_iso_datetime(value)
        if parsed is not None:
            return parsed
    return None
