"""Search API routes."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from qdrant_client.http.exceptions import UnexpectedResponse
from slowapi import Limiter

from gateway.api.auth import require_maintainer, require_reader
from gateway.api.dependencies import (
    get_app_settings,
    get_feedback_store,
    get_graph_service_dependency,
    get_search_service_dependency,
)
from gateway.config.settings import AppSettings
from gateway.graph import GraphService
from gateway.observability import SEARCH_REQUESTS_TOTAL
from gateway.search import SearchService
from gateway.search.feedback import SearchFeedbackStore

logger = logging.getLogger(__name__)


_SYMBOL_KIND_ALLOWLIST = {"class", "function", "method", "interface", "type", "module"}
_SYMBOL_LANGUAGE_ALLOWLIST = {"python", "typescript", "tsx", "javascript", "go"}


def create_router(limiter: Limiter, metrics_limit: str) -> APIRouter:
    """Return an API router for the search endpoints with shared rate limits."""
    router = APIRouter()

    @router.post("/search", dependencies=[Depends(require_reader)], tags=["search"])
    @limiter.limit(metrics_limit)
    def search_endpoint(
        request: Request,
        payload: dict[str, Any] = Body(...),  # noqa: B008
        search_service: SearchService | None = Depends(get_search_service_dependency),  # noqa: B008
        settings: AppSettings = Depends(get_app_settings),  # noqa: B008
        feedback_store: SearchFeedbackStore | None = Depends(get_feedback_store),  # noqa: B008
    ) -> JSONResponse:
        if search_service is None:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        query = payload.get("query")
        if not isinstance(query, str) or not query.strip():
            raise HTTPException(status_code=422, detail="Field 'query' is required")

        limit_value = payload.get("limit", 10)
        try:
            limit = int(limit_value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="Field 'limit' must be an integer") from None
        include_graph = bool(payload.get("include_graph", True))

        filters_payload = payload.get("filters")
        filters_resolved: dict[str, Any] = {}
        if filters_payload is not None:
            if not isinstance(filters_payload, dict):
                raise HTTPException(status_code=422, detail="Field 'filters' must be an object")

            subsystems = filters_payload.get("subsystems")
            if subsystems is not None:
                if not isinstance(subsystems, list) or not all(isinstance(item, str) for item in subsystems):
                    raise HTTPException(status_code=422, detail="filters.subsystems must be an array of strings")
                cleaned = [value.strip() for value in subsystems if isinstance(value, str) and value.strip()]
                if cleaned:
                    filters_resolved["subsystems"] = cleaned

            artifact_types = filters_payload.get("artifact_types")
            if artifact_types is not None:
                if not isinstance(artifact_types, list) or not all(isinstance(item, str) for item in artifact_types):
                    raise HTTPException(status_code=422, detail="filters.artifact_types must be an array of strings")
                allowed_types = {"code", "doc", "test", "proto", "config"}
                cleaned_types: list[str] = []
                for value in artifact_types:
                    key = value.strip().lower()
                    if not key:
                        continue
                    if key not in allowed_types:
                        raise HTTPException(status_code=422, detail=f"Unsupported artifact type '{value}'")
                    cleaned_types.append(key)
                if cleaned_types:
                    filters_resolved["artifact_types"] = cleaned_types

            namespaces = filters_payload.get("namespaces")
            if namespaces is not None:
                if not isinstance(namespaces, list) or not all(isinstance(item, str) for item in namespaces):
                    raise HTTPException(status_code=422, detail="filters.namespaces must be an array of strings")
                cleaned_namespaces = [value.strip() for value in namespaces if isinstance(value, str) and value.strip()]
                if cleaned_namespaces:
                    filters_resolved["namespaces"] = cleaned_namespaces

            tags = filters_payload.get("tags")
            if tags is not None:
                if not isinstance(tags, list) or not all(isinstance(item, str) for item in tags):
                    raise HTTPException(status_code=422, detail="filters.tags must be an array of strings")
                cleaned_tags = [value.strip() for value in tags if isinstance(value, str) and value.strip()]
                if cleaned_tags:
                    filters_resolved["tags"] = cleaned_tags

            symbols = filters_payload.get("symbols")
            if symbols is not None:
                if not isinstance(symbols, list) or not all(isinstance(item, str) for item in symbols):
                    raise HTTPException(status_code=422, detail="filters.symbols must be an array of strings")
                cleaned_symbols = [value.strip() for value in symbols if isinstance(value, str) and value.strip()]
                if cleaned_symbols:
                    filters_resolved["symbols"] = cleaned_symbols

            symbol_kinds = filters_payload.get("symbol_kinds")
            if symbol_kinds is not None:
                if not isinstance(symbol_kinds, list) or not all(isinstance(item, str) for item in symbol_kinds):
                    raise HTTPException(status_code=422, detail="filters.symbol_kinds must be an array of strings")
                cleaned_kinds = []
                for kind in symbol_kinds:
                    key = kind.strip().lower() if isinstance(kind, str) else ""
                    if not key:
                        continue
                    if key not in _SYMBOL_KIND_ALLOWLIST:
                        raise HTTPException(status_code=422, detail=f"Unsupported symbol kind '{kind}'")
                    cleaned_kinds.append(key)
                if cleaned_kinds:
                    filters_resolved["symbol_kinds"] = cleaned_kinds

            symbol_languages = filters_payload.get("symbol_languages")
            if symbol_languages is not None:
                if not isinstance(symbol_languages, list) or not all(isinstance(item, str) for item in symbol_languages):
                    raise HTTPException(status_code=422, detail="filters.symbol_languages must be an array of strings")
                cleaned_languages = []
                for lang in symbol_languages:
                    key = lang.strip().lower() if isinstance(lang, str) else ""
                    if not key:
                        continue
                    if key not in _SYMBOL_LANGUAGE_ALLOWLIST:
                        raise HTTPException(status_code=422, detail=f"Unsupported symbol language '{lang}'")
                    cleaned_languages.append(key)
                if cleaned_languages:
                    filters_resolved["symbol_languages"] = cleaned_languages

            updated_after = filters_payload.get("updated_after")
            if updated_after is not None:
                if not isinstance(updated_after, str) or not updated_after.strip():
                    raise HTTPException(status_code=422, detail="filters.updated_after must be an ISO-8601 string")
                parsed_updated_after = _parse_iso8601_to_utc(updated_after)
                if parsed_updated_after is None:
                    raise HTTPException(status_code=422, detail="filters.updated_after must be an ISO-8601 string")
                filters_resolved["updated_after"] = parsed_updated_after

            max_age_days = filters_payload.get("max_age_days")
            if max_age_days is not None:
                try:
                    max_age_value = int(max_age_days)
                except (TypeError, ValueError):
                    raise HTTPException(status_code=422, detail="filters.max_age_days must be a positive integer") from None
                if max_age_value <= 0:
                    raise HTTPException(status_code=422, detail="filters.max_age_days must be a positive integer")
                filters_resolved["max_age_days"] = max_age_value

        graph_service: GraphService | None = None
        if include_graph:
            graph_manager = getattr(request.app.state, "graph_manager", None)
            if graph_manager is not None:
                try:
                    graph_service = get_graph_service_dependency(request)
                except HTTPException:
                    graph_service = None

        request_id = getattr(request.state, "request_id", None) or str(uuid4())

        try:
            response = search_service.search(
                query=query,
                limit=limit,
                include_graph=include_graph,
                graph_service=graph_service,
                sort_by_vector=settings.search_sort_by_vector,
                request_id=request_id,
                filters=filters_resolved,
            )
        except HTTPException:
            SEARCH_REQUESTS_TOTAL.labels(status="failure").inc()
            raise
        except (UnexpectedResponse, RuntimeError, ValueError, TimeoutError) as exc:  # pragma: no cover
            SEARCH_REQUESTS_TOTAL.labels(status="failure").inc()
            logger.error("Search failed: %s", exc)
            raise HTTPException(status_code=500, detail="Search failed") from exc
        SEARCH_REQUESTS_TOTAL.labels(status="success").inc()

        metadata: dict[str, Any] = dict(response.metadata)
        payload_json = {
            "query": response.query,
            "results": [
                {
                    "chunk": result.chunk,
                    "graph_context": result.graph_context,
                    "scoring": result.scoring,
                }
                for result in response.results
            ],
            "metadata": metadata,
        }
        metadata["request_id"] = request_id
        if include_graph and graph_service is None:
            warnings = metadata.setdefault("warnings", [])
            warnings.append("Graph context unavailable")
            metadata["graph_context_included"] = False

        if filters_resolved and "filters_applied" not in metadata:
            serialisable_filters: dict[str, Any] = {}
            for key, value in filters_resolved.items():
                if isinstance(value, datetime):
                    serialisable_filters[key] = value.astimezone(UTC).isoformat()
                elif isinstance(value, list):
                    serialisable_filters[key] = value
                else:
                    serialisable_filters[key] = value
            metadata["filters_applied"] = serialisable_filters

        feedback_payload = payload.get("feedback")
        feedback_mapping = feedback_payload if isinstance(feedback_payload, dict) else None
        context_payload = payload.get("context")

        if feedback_store is not None and response.results and not _has_vote(feedback_mapping):
            metadata["feedback_prompt"] = (
                "Optional: call `km-feedback-submit` with the provided `request_id` "
                "and a vote in the range [-1, 1] to help tune search ranking."
            )

        if feedback_store is not None:
            try:
                feedback_store.record(
                    response=response,
                    feedback=feedback_mapping,
                    context=context_payload,
                    request_id=request_id,
                )
            except (OSError, RuntimeError, TypeError, ValueError):
                logger.warning("Failed to record search feedback", exc_info=True)
        return JSONResponse(payload_json)

    @router.get("/search/weights", dependencies=[Depends(require_maintainer)], tags=["search"])
    @limiter.limit("60/minute")
    def search_weights(
        request: Request,
        settings: AppSettings = Depends(get_app_settings),  # noqa: B008
    ) -> JSONResponse:
        del request
        profile, weights = settings.resolved_search_weights()
        return JSONResponse(
            {
                "profile": profile,
                "weights": weights,
                "slow_graph_warn_ms": settings.search_warn_slow_graph_ms,
            }
        )

    return router


def _parse_iso8601_to_utc(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _has_vote(mapping: Mapping[str, Any] | None) -> bool:
    if not mapping:
        return False
    vote_value = mapping.get("vote")
    if isinstance(vote_value, (int, float)):
        return True
    if isinstance(vote_value, str):
        try:
            float(vote_value)
        except ValueError:
            return False
        return True
    return False


__all__ = ["create_router"]
