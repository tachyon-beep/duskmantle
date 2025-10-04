"""Graph API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter

from gateway.api.auth import require_maintainer, require_reader
from gateway.api.dependencies import get_graph_service_dependency
from gateway.graph import GraphNotFoundError, GraphQueryError, GraphService


def create_router(limiter: Limiter, metrics_limit: str) -> APIRouter:
    """Create an API router exposing graph endpoints with shared rate limits."""
    router = APIRouter()

    @router.get("/graph/subsystems/{name}", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_subsystem(
        name: str,
        request: Request,
        depth: int = 1,
        include_artifacts: bool = True,
        cursor: str | None = None,
        limit: int = 25,
        service: GraphService = Depends(get_graph_service_dependency),  # noqa: B008
    ) -> JSONResponse:
        del request
        limit = max(1, min(limit, 100))
        try:
            payload = service.get_subsystem(
                name,
                depth=depth,
                limit=limit,
                cursor=cursor,
                include_artifacts=include_artifacts,
            )
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except GraphQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(payload)

    @router.get("/graph/subsystems/{name}/graph", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_subsystem_graph(
        name: str,
        request: Request,
        depth: int = 2,
        service: GraphService = Depends(get_graph_service_dependency),  # noqa: B008
    ) -> JSONResponse:
        del request
        depth = max(1, depth)
        try:
            payload = service.get_subsystem_graph(name, depth=depth)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except GraphQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(payload)

    @router.get(
        "/graph/nodes/{node_id:path}",
        dependencies=[Depends(require_reader)],
        tags=["graph"],
    )
    @limiter.limit(metrics_limit)
    def graph_node(
        node_id: str,
        request: Request,
        relationships: str = "outgoing",
        limit: int = 50,
        service: GraphService = Depends(get_graph_service_dependency),  # noqa: B008
    ) -> JSONResponse:
        del request
        relationships_normalized = relationships.lower()
        if relationships_normalized not in {"outgoing", "incoming", "all", "none"}:
            raise HTTPException(status_code=400, detail="Invalid relationships parameter")
        limit = max(1, min(limit, 200))
        try:
            payload = service.get_node(
                node_id,
                relationships=relationships_normalized,
                limit=limit,
            )
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except GraphQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(payload)

    @router.get("/graph/symbols/{symbol_id:path}/tests", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_symbol_tests(
        symbol_id: str,
        request: Request,
        service: GraphService = Depends(get_graph_service_dependency),  # noqa: B008
    ) -> JSONResponse:
        del request
        try:
            payload = service.get_symbol_tests(symbol_id)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return JSONResponse(payload)

    @router.get("/graph/search", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_search(
        request: Request,
        q: str,
        limit: int = 20,
        service: GraphService = Depends(get_graph_service_dependency),  # noqa: B008
    ) -> JSONResponse:
        del request
        limit = max(1, min(limit, 50))
        payload = service.search(q, limit=limit)
        return JSONResponse(payload)

    @router.get("/graph/orphans", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_orphans(
        request: Request,
        label: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
        service: GraphService = Depends(get_graph_service_dependency),  # noqa: B008
    ) -> JSONResponse:
        del request
        limit = max(1, min(limit, 200))
        try:
            payload = service.list_orphan_nodes(label=label, cursor=cursor, limit=limit)
        except GraphQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(payload)

    @router.post("/graph/cypher", dependencies=[Depends(require_maintainer)], tags=["graph"])
    @limiter.limit("30/minute")
    def graph_cypher(
        request: Request,
        payload: dict[str, Any] = Body(...),  # noqa: B008
        service: GraphService = Depends(get_graph_service_dependency),  # noqa: B008
    ) -> JSONResponse:
        del request
        query = payload.get("query")
        if not isinstance(query, str) or not query.strip():
            raise HTTPException(status_code=422, detail="Field 'query' is required")
        parameters = payload.get("parameters")
        if parameters is not None and not isinstance(parameters, dict):
            raise HTTPException(status_code=422, detail="Field 'parameters' must be an object")
        try:
            result = service.run_cypher(query, parameters)
        except GraphQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(result)

    return router


__all__ = ["create_router"]
