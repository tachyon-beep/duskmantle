"""FastAPI dependency helpers for the gateway application."""

from __future__ import annotations

import logging

from fastapi import HTTPException, Request
from slowapi import Limiter

from gateway.config.settings import AppSettings
from gateway.graph import GraphService, get_graph_service
from gateway.ingest.embedding import Embedder
from gateway.search import SearchOptions, SearchService, SearchWeights
from gateway.search.feedback import SearchFeedbackStore
from gateway.search.trainer import ModelArtifact

logger = logging.getLogger(__name__)


def get_app_settings(request: Request) -> AppSettings:
    """Return the application settings attached to the FastAPI app."""

    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise RuntimeError("App settings not initialised on application state")
    return settings


def get_limiter(request: Request) -> Limiter:
    """Return the rate limiter configured on the FastAPI app."""

    limiter = getattr(request.app.state, "limiter", None)
    if limiter is None:
        raise RuntimeError("Rate limiter not configured on application state")
    return limiter


def get_search_model(request: Request) -> ModelArtifact | None:
    """Return the cached search ranking model from application state."""
    return getattr(request.app.state, "search_model_artifact", None)


def get_graph_service_dependency(
    request: Request,
) -> GraphService:
    """Return a memoised graph service bound to the current FastAPI app."""
    settings = get_app_settings(request)
    graph_manager = getattr(request.app.state, "graph_manager", None)
    if graph_manager is None:
        raise HTTPException(status_code=503, detail="Graph service unavailable")
    status = graph_manager.describe()
    if status.status != "ok" or status.last_success is None:
        raise HTTPException(status_code=503, detail="Graph service unavailable")
    service = getattr(request.app.state, "graph_service_instance", None)
    cached_revision = getattr(request.app.state, "graph_service_revision", None)
    current_revision = graph_manager.revision
    if service is None or cached_revision != current_revision:
        cache_ttl = settings.graph_subsystem_cache_ttl_seconds
        cache_max = settings.graph_subsystem_cache_max_entries
        factory = getattr(request.app.state, "graph_service_factory", get_graph_service)
        service = factory(
            graph_manager.get_write_driver,
            settings.neo4j_database,
            cache_ttl=cache_ttl,
            cache_max_entries=cache_max,
            readonly_driver=graph_manager.get_readonly_driver,
            failure_callback=graph_manager.mark_failure,
        )
        request.app.state.graph_service_instance = service
        request.app.state.graph_service_revision = current_revision
    return service


def get_search_service_dependency(
    request: Request,
) -> SearchService | None:
    """Construct (and cache) the hybrid search service for the application."""
    settings = get_app_settings(request)
    qdrant_manager = getattr(request.app.state, "qdrant_manager", None)
    if qdrant_manager is None:
        return None

    try:
        qclient = qdrant_manager.get_client()
    except Exception as exc:  # pragma: no cover - defensive guard
        qdrant_manager.mark_failure(exc)
        logger.warning("Qdrant client unavailable: %s", exc)
        return None

    request.app.state.qdrant_revision = qdrant_manager.revision

    embedder = getattr(request.app.state, "search_embedder", None)
    if embedder is None:
        try:
            embedder = Embedder(settings.embedding_model)
        except (RuntimeError, ValueError, OSError) as exc:  # pragma: no cover - loading errors logged
            logger.warning("Failed to initialize embedder: %s", exc)
            return None
        request.app.state.search_embedder = embedder

    weight_profile, resolved_weights = settings.resolved_search_weights()
    vector_weight = settings.search_vector_weight
    lexical_weight = settings.search_lexical_weight
    search_weights = SearchWeights(
        subsystem=resolved_weights["weight_subsystem"],
        relationship=resolved_weights["weight_relationship"],
        support=resolved_weights["weight_support"],
        coverage_penalty=resolved_weights["weight_coverage_penalty"],
        criticality=resolved_weights["weight_criticality"],
        vector=vector_weight,
        lexical=lexical_weight,
    )
    search_options = SearchOptions(
        hnsw_ef_search=settings.search_hnsw_ef_search,
        scoring_mode=settings.search_scoring_mode,
        weight_profile=weight_profile,
        slow_graph_warn_seconds=max(settings.search_warn_slow_graph_ms, 0) / 1000.0,
    )

    model_artifact = getattr(request.app.state, "search_model_artifact", None)
    return SearchService(
        qdrant_client=qclient,
        collection_name=settings.qdrant_collection,
        embedder=embedder,
        options=search_options,
        weights=search_weights,
        model_artifact=model_artifact,
        failure_callback=qdrant_manager.mark_failure,
    )


def get_feedback_store(request: Request) -> SearchFeedbackStore | None:
    """Return the configured search feedback store, if any."""
    return getattr(request.app.state, "search_feedback_store", None)


__all__ = [
    "get_app_settings",
    "get_feedback_store",
    "get_graph_service_dependency",
    "get_limiter",
    "get_search_model",
    "get_search_service_dependency",
]
