from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from qdrant_client import QdrantClient
from qdrant_client.http.models import ScoredPoint, SearchParams

from gateway.graph.service import GraphService, GraphServiceError
from gateway.ingest.embedding import Embedder
from gateway.observability import SEARCH_GRAPH_CACHE_EVENTS, SEARCH_GRAPH_LOOKUP_SECONDS, SEARCH_SCORE_DELTA
from gateway.search.trainer import ModelArtifact

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chunk: dict[str, Any]
    graph_context: dict[str, Any] | None
    scoring: dict[str, Any]


@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    metadata: dict[str, Any]


class SearchService:
    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        embedder: Embedder,
        *,
        max_limit: int = 25,
        graph_timeout_seconds: float = 0.25,
        weight_subsystem: float = 0.30,
        weight_relationship: float = 0.05,
        weight_support: float = 0.10,
        weight_coverage_penalty: float = 0.15,
        weight_criticality: float = 0.12,
        vector_weight: float = 1.0,
        lexical_weight: float = 0.25,
        hnsw_ef_search: int | None = None,
        scoring_mode: Literal["heuristic", "ml"] = "heuristic",
        model_artifact: ModelArtifact | None = None,
        weight_profile: str = "custom",
        slow_graph_warn_seconds: float = 0.25,
    ) -> None:
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.embedder = embedder
        self.max_limit = max_limit
        self.graph_timeout_seconds = graph_timeout_seconds
        self.weight_subsystem = weight_subsystem
        self.weight_relationship = weight_relationship
        self.weight_support = weight_support
        self.weight_coverage_penalty = weight_coverage_penalty
        self.weight_criticality = weight_criticality
        self.vector_weight, self.lexical_weight = _normalise_hybrid_weights(
            vector_weight,
            lexical_weight,
        )
        self.hnsw_ef_search = int(hnsw_ef_search) if hnsw_ef_search and hnsw_ef_search > 0 else None
        self.weight_profile = weight_profile
        self.slow_graph_warn_seconds = max(0.0, slow_graph_warn_seconds)
        self.scoring_mode = scoring_mode if model_artifact is not None else "heuristic"
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

        results: list[SearchResult] = []
        warnings: list[str] = []
        graph_cache: dict[str, dict[str, Any]] = {}

        filters = filters or {}
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

        query_tokens = _detect_query_subsystems(query)
        graph_context_included = include_graph and graph_service is not None
        recency_required = recency_cutoff is not None
        recency_warning_emitted = False

        for point in hits:
            payload = point.payload or {}
            chunk = {
                "chunk_id": payload.get("chunk_id"),
                "artifact_path": payload.get("path"),
                "artifact_type": payload.get("artifact_type"),
                "subsystem": payload.get("subsystem"),
                "namespace": payload.get("namespace"),
                "tags": payload.get("tags"),
                "text": payload.get("text"),
                "coverage_missing": bool(payload.get("coverage_missing")),
                "score": point.score,
                "subsystem_criticality": payload.get("subsystem_criticality"),
                "coverage_ratio": payload.get("coverage_ratio"),
                "git_timestamp": payload.get("git_timestamp"),
            }

            lexical_score = _lexical_score(query, chunk)
            scoring = _base_scoring(
                vector_score=point.score,
                lexical_score=lexical_score,
                vector_weight=self.vector_weight,
                lexical_weight=self.lexical_weight,
            )

            artifact_type = (payload.get("artifact_type") or "").lower()
            if allowed_types and artifact_type not in allowed_types:
                continue

            namespace_value = (payload.get("namespace") or "").strip().lower()
            if allowed_namespaces and namespace_value not in allowed_namespaces:
                continue

            payload_tags_raw = payload.get("tags") or []
            if isinstance(payload_tags_raw, (list, tuple)):
                payload_tag_set = {str(tag).strip().lower() for tag in payload_tags_raw if str(tag).strip()}
            else:
                payload_tag_set = set()
            if allowed_tags and not payload_tag_set.intersection(allowed_tags):
                continue

            subsystem_value = (payload.get("subsystem") or "").lower()
            subsystem_match = not allowed_subsystems or (subsystem_value and subsystem_value in allowed_subsystems)

            graph_context_internal: dict[str, Any] | None = None
            path_depth_value: float | None = None
            cache_entry: dict[str, Any] | None = None
            node_id: str | None = None

            if graph_service and payload.get("path"):
                node_label = _label_for_artifact(payload.get("artifact_type"))
                node_id = f"{node_label}:{payload.get('path')}"
                cache_entry = graph_cache.get(node_id)
                needs_timestamp = recency_required and not payload.get("git_timestamp") and include_graph
                fetch_graph = include_graph or (allowed_subsystems and not subsystem_match) or needs_timestamp

                if fetch_graph and cache_entry is None:
                    lookup_started = time.perf_counter()
                    try:
                        node_data = graph_service.get_node(
                            node_id,
                            relationships="all",
                            limit=10,
                        )
                        graph_context_internal = _summarize_graph_context(node_data)
                        cache_entry = {
                            "graph_context": graph_context_internal,
                            "path_depth": None,
                        }
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
                    except Exception as exc:  # pragma: no cover - defensive
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
                        except Exception as exc:  # pragma: no cover - defensive
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

            if allowed_subsystems:
                if subsystem_match:
                    pass
                else:
                    subs_from_context = _subsystems_from_context(graph_context_internal)
                    if not subs_from_context.intersection(allowed_subsystems):
                        continue

            if recency_required:
                chunk_datetime = _resolve_chunk_datetime(chunk, graph_context_internal)
                if chunk_datetime is None:
                    if not recency_warning_emitted:
                        warnings.append("recency filter skipped results lacking timestamps")
                        recency_warning_emitted = True
                    continue
                if recency_cutoff and chunk_datetime < recency_cutoff:
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

            results.append(
                SearchResult(
                    chunk=chunk,
                    graph_context=graph_context_public,
                    scoring=scoring,
                )
            )

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
        if filters_applied:
            metadata["filters_applied"] = filters_applied
        if request_id:
            metadata["request_id"] = request_id
        return SearchResponse(query=query, results=results, metadata=metadata)

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
    if vector == 0.0 and lexical == 0.0:
        vector = 1.0
    return vector, lexical


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


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
    if "weighted_vector_component" not in signals:
        signals["weighted_vector_component"] = vector_weight * vector_score
    if "weighted_lexical_component" not in signals:
        signals["weighted_lexical_component"] = lexical_weight * lexical_score

    subsystem = (chunk.get("subsystem") or "").lower()
    subsystem_affinity = 0.0
    if subsystem:
        if subsystem in query_tokens:
            subsystem_affinity = 1.0
        else:
            for token in query_tokens:
                if subsystem in token or token in subsystem:
                    subsystem_affinity = max(subsystem_affinity, 0.5)

    relationships = graph_context.get("relationships", [])
    relationship_count = len(relationships)

    related_artifacts = graph_context.get("related_artifacts", [])
    design_docs = sum(1 for item in related_artifacts if item.get("id", "").startswith("DesignDoc:"))
    test_cases = sum(1 for item in related_artifacts if item.get("id", "").startswith("TestCase:"))
    supporting_bonus = min(design_docs, 2) * 0.2 + min(test_cases, 2) * 0.1

    coverage_missing = 1.0 if chunk.get("coverage_missing") else 0.0
    coverage_ratio_raw = chunk.get("coverage_ratio")
    try:
        coverage_ratio = max(0.0, min(1.0, float(coverage_ratio_raw)))
    except (TypeError, ValueError):
        coverage_ratio = 0.0 if coverage_missing else 1.0
    coverage_penalty = weight_coverage_penalty * (1.0 - coverage_ratio)

    criticality_value = chunk.get("subsystem_criticality")
    if criticality_value is None:
        criticality_value = _extract_subsystem_criticality(graph_context)
    criticality_score = _normalise_criticality(criticality_value)

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
        - coverage_penalty
    )

    signals = scoring.setdefault("signals", {})
    signals.update(
        {
            "subsystem_affinity": subsystem_affinity,
            "relationship_count": relationship_count,
            "supporting_bonus": supporting_bonus,
            "coverage_missing": coverage_missing,
            "coverage_ratio": coverage_ratio,
            "criticality_score": criticality_score,
            "coverage_penalty": coverage_penalty,
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

    # Path depth (fallback to heuristic when graph data missing)
    if path_depth is None:
        path_depth = _estimate_path_depth(graph_context)
    try:
        signals["path_depth"] = float(path_depth)
    except (TypeError, ValueError):
        signals["path_depth"] = None

    # Subsystem criticality (retain previously computed score if present)
    if "criticality_score" not in signals:
        criticality = chunk.get("subsystem_criticality")
        if criticality is None:
            criticality = _extract_subsystem_criticality(graph_context)
        signals["criticality_score"] = _normalise_criticality(criticality)
    signals.setdefault("subsystem_criticality", signals.get("criticality_score"))

    # Freshness (days)
    if freshness_days is None:
        freshness_days = _compute_freshness_days(chunk, graph_context)
    signals["freshness_days"] = freshness_days

    # Coverage ratio (0-1)
    if "coverage_ratio" not in signals:
        coverage_ratio = chunk.get("coverage_ratio")
        if coverage_ratio is None:
            coverage_ratio = 0.0 if signals.get("coverage_missing") else 1.0
        try:
            signals["coverage_ratio"] = float(coverage_ratio)
        except (TypeError, ValueError):
            signals["coverage_ratio"] = None

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
