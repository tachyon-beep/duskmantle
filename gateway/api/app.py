from __future__ import annotations

import json
import logging
import sqlite3
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from neo4j import GraphDatabase

from qdrant_client import QdrantClient

from gateway import get_version
from gateway.api.auth import require_maintainer, require_reader
from gateway.config.settings import AppSettings, get_settings
from gateway.graph import (
    GraphNotFoundError,
    GraphQueryError,
    GraphService,
    get_graph_service,
)
from gateway.graph.migrations import MigrationRunner
from gateway.ingest.embedding import Embedder
from gateway.ingest.lifecycle import summarize_lifecycle
from gateway.observability import (
    GRAPH_MIGRATION_LAST_STATUS,
    GRAPH_MIGRATION_LAST_TIMESTAMP,
    SEARCH_REQUESTS_TOTAL,
    configure_logging,
    configure_tracing,
)
from gateway.search import SearchService
from gateway.search.feedback import SearchFeedbackStore
from gateway.search.trainer import ModelArtifact, load_artifact
from gateway.scheduler import IngestionScheduler
from gateway.ui import get_static_path, router as ui_router

from typing import Any, Mapping
from uuid import uuid4


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""
    configure_logging()
    settings = get_settings()

    if settings.auth_enabled:
        missing: list[str] = []
        if not settings.maintainer_token:
            missing.append("KM_ADMIN_TOKEN")
        if settings.auth_mode == "secure" and settings.neo4j_password in {"neo4jadmin", "neo4j", "neo4jpass"}:
            missing.append("KM_NEO4J_PASSWORD (non-default value)")
        if missing:
            formatted = ", ".join(missing)
            raise RuntimeError(
                "Authentication is enabled but required credentials are missing: "
                f"{formatted}. Disable auth or provide the credentials before starting the gateway."
            )
        if not settings.reader_token:
            logger.warning("Auth enabled without KM_READER_TOKEN; maintainer token will service reader endpoints")

    weight_profile_name, resolved_weights = settings.resolved_search_weights()
    logger.info(
        "Gateway startup configuration initialised",
        extra={
            "event": "startup_config",
            "version": get_version(),
            "auth_enabled": settings.auth_enabled,
            "auth_mode": settings.auth_mode,
            "graph_auto_migrate": settings.graph_auto_migrate,
            "embedding_model": settings.embedding_model,
            "ingest_window": settings.ingest_window,
            "ingest_overlap": settings.ingest_overlap,
            "search_weight_profile": weight_profile_name,
            "search_weights": resolved_weights,
        },
    )

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds"],
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        scheduler = IngestionScheduler(settings)
        scheduler.start()
        app.state.scheduler = scheduler
        try:
            yield
        finally:  # pragma: no cover - exercised via integration tests
            with suppress(Exception):
                scheduler.shutdown()
            driver = getattr(app.state, "graph_driver", None)
            if driver:
                with suppress(Exception):
                    driver.close()

    app = FastAPI(
        title="Duskmantle Knowledge Gateway",
        version=get_version(),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.mount("/ui/static", StaticFiles(directory=str(get_static_path())), name="ui-static")
    app.include_router(ui_router)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        incoming = request.headers.get("x-request-id")
        request_id = incoming or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        if "X-Request-ID" not in response.headers:
            response.headers["X-Request-ID"] = request_id
        return response

    configure_tracing(app, settings)

    feedback_store: SearchFeedbackStore | None = None
    try:
        feedback_store = SearchFeedbackStore(settings.state_path / "feedback")
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning("Search feedback logging disabled: %s", exc)

    app.state.search_feedback_store = feedback_store

    model_artifact: ModelArtifact | None = None
    if settings.search_scoring_mode == "ml":
        model_path = settings.search_model_path
        if model_path is None:
            model_path = settings.state_path / "feedback" / "models" / "model.json"
        try:
            model_artifact = load_artifact(model_path)
            logger.info("Loaded search ranking model from %s", model_path)
        except FileNotFoundError:
            logger.warning(
                "Search scoring mode set to 'ml' but model file %s not found; falling back to heuristic",
                model_path,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load search ranking model: %s", exc)

    try:
        graph_driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        app.state.graph_driver = graph_driver
        if settings.graph_auto_migrate:
            runner = MigrationRunner(driver=graph_driver, database=settings.neo4j_database)
            pending: list[str] | None
            try:
                pending = runner.pending_ids()
            except Exception as exc:  # pragma: no cover - defensive preflight
                pending = None
                logger.warning(
                    "Graph auto-migration preflight failed; attempting run anyway: %s",
                    exc,
                )

            if pending is None:
                logger.info("Graph auto-migration enabled; running without pending summary")
            elif pending:
                logger.info(
                    "Graph auto-migration enabled; applying %d pending migration(s): %s",
                    len(pending),
                    ", ".join(pending),
                )
            else:
                logger.info("Graph auto-migration enabled; schema already current")

            try:
                runner.run()
            except Exception:  # pragma: no cover - defensive
                logger.exception("Graph auto-migration failed")
                GRAPH_MIGRATION_LAST_STATUS.set(0)
                GRAPH_MIGRATION_LAST_TIMESTAMP.set(time.time())
            else:
                if pending is None:
                    logger.info("Graph auto-migration completed")
                elif pending:
                    logger.info(
                        "Graph auto-migration completed; applied %d migration(s)",
                        len(pending),
                    )
                else:
                    logger.info("Graph auto-migration completed; no migrations were pending")
                GRAPH_MIGRATION_LAST_STATUS.set(1)
                GRAPH_MIGRATION_LAST_TIMESTAMP.set(time.time())
        else:
            logger.info("Graph auto-migration disabled; run `gateway-graph migrate` during deployment")
            GRAPH_MIGRATION_LAST_STATUS.set(-1)
            GRAPH_MIGRATION_LAST_TIMESTAMP.set(0)
    except Exception as exc:  # pragma: no cover - connection may fail in dev/test
        logger.warning("Neo4j driver initialization failed: %s", exc)
        app.state.graph_driver = None
        GRAPH_MIGRATION_LAST_STATUS.set(0)
        GRAPH_MIGRATION_LAST_TIMESTAMP.set(time.time())

    try:
        qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        app.state.qdrant_client = qdrant_client
    except Exception as exc:  # pragma: no cover - offline scenarios
        logger.warning("Qdrant client initialization failed: %s", exc)
        app.state.qdrant_client = None

    app.state.search_embedder = None
    app.state.search_model_artifact = model_artifact

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.state.scheduler = None

    @app.get("/healthz", tags=["health"])
    def healthz() -> dict[str, object]:
        """Return basic health information for the gateway."""

        report = _build_health_report(app, settings)
        return report

    @app.get("/readyz", tags=["health"])
    def readyz() -> dict[str, str]:
        """Return readiness information suitable for container orchestration."""
        return {"status": "ready"}

    metrics_limit = f"{settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds"

    def graph_service_dependency(request: Request) -> GraphService:
        driver = getattr(request.app.state, "graph_driver", None)
        if driver is None:
            raise HTTPException(status_code=503, detail="Graph service unavailable")
        service = getattr(request.app.state, "_graph_service_instance", None)
        if service is None or service.driver is not driver:
            cache_ttl = settings.graph_subsystem_cache_ttl_seconds
            cache_max = settings.graph_subsystem_cache_max_entries
            service = get_graph_service(
                driver,
                settings.neo4j_database,
                cache_ttl=cache_ttl,
                cache_max_entries=cache_max,
            )
            request.app.state._graph_service_instance = service
        return service

    def search_service_dependency(request: Request) -> SearchService | None:
        qclient = getattr(request.app.state, "qdrant_client", None)
        if qclient is None:
            return None
        embedder = getattr(request.app.state, "search_embedder", None)
        if embedder is None:
            try:
                embedder = Embedder(settings.embedding_model)
            except Exception as exc:  # pragma: no cover - loading errors logged
                logger.warning("Failed to initialize embedder: %s", exc)
                return None
            request.app.state.search_embedder = embedder
        weight_profile, resolved_weights = settings.resolved_search_weights()
        vector_weight = settings.search_vector_weight
        lexical_weight = settings.search_lexical_weight
        return SearchService(
            qdrant_client=qclient,
            collection_name=settings.qdrant_collection,
            embedder=embedder,
            vector_weight=vector_weight,
            lexical_weight=lexical_weight,
            hnsw_ef_search=settings.search_hnsw_ef_search,
            weight_subsystem=resolved_weights["weight_subsystem"],
            weight_relationship=resolved_weights["weight_relationship"],
            weight_support=resolved_weights["weight_support"],
            weight_coverage_penalty=resolved_weights["weight_coverage_penalty"],
            weight_criticality=resolved_weights["weight_criticality"],
            scoring_mode=settings.search_scoring_mode,
            model_artifact=getattr(request.app.state, "search_model_artifact", None),
            weight_profile=weight_profile,
            slow_graph_warn_seconds=max(settings.search_warn_slow_graph_ms, 0) / 1000.0,
        )

    app.state.graph_service_dependency = graph_service_dependency
    app.state.search_service_dependency = search_service_dependency

    @app.get("/metrics", tags=["observability"])
    @limiter.limit(metrics_limit)
    def metrics_endpoint(request: Request) -> Response:  # noqa: ARG001 - request used by limiter
        """Expose Prometheus metrics."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/audit/history", dependencies=[Depends(require_maintainer)], tags=["observability"])
    @limiter.limit("30/minute")
    def audit_history(request: Request, limit: int = 20) -> JSONResponse:  # noqa: ARG001 - request used by limiter
        from gateway.ingest.audit import AuditLogger

        audit_path = settings.state_path / "audit" / "audit.db"
        logger = AuditLogger(audit_path)
        return JSONResponse(logger.recent(limit=limit))

    @app.get("/coverage", dependencies=[Depends(require_maintainer)], tags=["observability"])
    @limiter.limit("30/minute")
    def coverage_report(request: Request) -> JSONResponse:  # noqa: ARG001 - request used by limiter
        report_path = settings.state_path / "reports" / "coverage_report.json"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Coverage report not found")

        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail="Coverage report is invalid JSON") from exc
        return JSONResponse(data)

    @app.get("/lifecycle", dependencies=[Depends(require_maintainer)], tags=["observability"])
    @limiter.limit("30/minute")
    def lifecycle_report(request: Request) -> JSONResponse:  # noqa: ARG001
        report_path = settings.state_path / "reports" / "lifecycle_report.json"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Lifecycle report not found")

        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail="Lifecycle report is invalid JSON") from exc
        return JSONResponse(data)

    @app.get("/lifecycle/history", dependencies=[Depends(require_maintainer)], tags=["observability"])
    @limiter.limit("30/minute")
    def lifecycle_history(request: Request, limit: int = 30) -> JSONResponse:  # noqa: ARG001
        history_dir = settings.state_path / "reports" / "lifecycle_history"
        if settings.lifecycle_history_limit <= 0:
            return JSONResponse({"history": []})
        try:
            requested = int(limit or 1)
        except (TypeError, ValueError):
            requested = 1
        limit_normalized = max(1, min(requested, settings.lifecycle_history_limit))
        files: list[Path] = []
        if history_dir.exists():
            files = sorted(history_dir.glob("lifecycle_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit_normalized]
        if history_dir.exists():
            files = sorted(history_dir.glob("lifecycle_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
        entries: list[dict[str, object]] = []
        for path_entry in reversed(files):
            try:
                payload = json.loads(path_entry.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            summary = summarize_lifecycle(payload)
            summary["path"] = path_entry.name
            entries.append(summary)
        return JSONResponse({"history": entries})

    @app.post("/search", dependencies=[Depends(require_reader)], tags=["search"])
    @limiter.limit(metrics_limit)
    def search_endpoint(
        request: Request,
        payload: dict[str, Any] = Body(...),
        search_service: SearchService | None = Depends(search_service_dependency),
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
            raise HTTPException(status_code=422, detail="Field 'limit' must be an integer")
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
                    raise HTTPException(status_code=422, detail="filters.max_age_days must be a positive integer")
                if max_age_value <= 0:
                    raise HTTPException(status_code=422, detail="filters.max_age_days must be a positive integer")
                filters_resolved["max_age_days"] = max_age_value

        graph_service = None
        if include_graph:
            driver = getattr(request.app.state, "graph_driver", None)
            if driver is not None:
                graph_service = graph_service_dependency(request)

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
        except Exception as exc:  # pragma: no cover
            SEARCH_REQUESTS_TOTAL.labels(status="failure").inc()
            logger.error("Search failed: %s", exc)
            raise HTTPException(status_code=500, detail="Search failed") from exc
        else:
            SEARCH_REQUESTS_TOTAL.labels(status="success").inc()

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
            "metadata": response.metadata,
        }
        payload_json["metadata"]["request_id"] = request_id
        if include_graph and graph_service is None:
            warnings = payload_json["metadata"].setdefault("warnings", [])
            warnings.append("Graph context unavailable")
            payload_json["metadata"]["graph_context_included"] = False

        if filters_resolved and "filters_applied" not in payload_json["metadata"]:
            serialisable_filters: dict[str, Any] = {}
            for key, value in filters_resolved.items():
                if isinstance(value, datetime):
                    serialisable_filters[key] = value.astimezone(timezone.utc).isoformat()
                elif isinstance(value, list):
                    serialisable_filters[key] = value
                else:
                    serialisable_filters[key] = value
            payload_json["metadata"]["filters_applied"] = serialisable_filters

        feedback_payload = payload.get("feedback")
        feedback_mapping = feedback_payload if isinstance(feedback_payload, dict) else None
        context_payload = payload.get("context")
        feedback_store = getattr(app.state, "search_feedback_store", None)

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
                else:
                    return True
            return False

        if feedback_store is not None and response.results and not _has_vote(feedback_mapping):
            payload_json["metadata"]["feedback_prompt"] = (
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
            except Exception:
                logger.warning("Failed to record search feedback", exc_info=True)
        return JSONResponse(payload_json)

    @app.get("/search/weights", dependencies=[Depends(require_maintainer)], tags=["search"])
    @limiter.limit("60/minute")
    def search_weights(request: Request) -> JSONResponse:  # noqa: ARG001 - used by limiter
        profile, weights = settings.resolved_search_weights()
        return JSONResponse(
            {
                "profile": profile,
                "weights": weights,
                "slow_graph_warn_ms": settings.search_warn_slow_graph_ms,
            }
        )

    @app.get("/graph/subsystems/{name}", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_subsystem(
        name: str,
        request: Request,  # noqa: ARG001 - required by rate limiter
        depth: int = 1,
        include_artifacts: bool = True,
        cursor: str | None = None,
        limit: int = 25,
        service: GraphService = Depends(graph_service_dependency),
    ) -> JSONResponse:
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

    @app.get("/graph/subsystems/{name}/graph", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_subsystem_graph(
        name: str,
        request: Request,  # noqa: ARG001
        depth: int = 2,
        service: GraphService = Depends(graph_service_dependency),
    ) -> JSONResponse:
        depth = max(1, depth)
        try:
            payload = service.get_subsystem_graph(name, depth=depth)
        except GraphNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except GraphQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(payload)

    @app.get(
        "/graph/nodes/{node_id:path}",
        dependencies=[Depends(require_reader)],
        tags=["graph"],
    )
    @limiter.limit(metrics_limit)
    def graph_node(
        node_id: str,
        request: Request,  # noqa: ARG001
        relationships: str = "outgoing",
        limit: int = 50,
        service: GraphService = Depends(graph_service_dependency),
    ) -> JSONResponse:
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

    @app.get("/graph/search", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_search(
        request: Request,  # noqa: ARG001
        q: str,
        limit: int = 20,
        service: GraphService = Depends(graph_service_dependency),
    ) -> JSONResponse:
        limit = max(1, min(limit, 50))
        payload = service.search(q, limit=limit)
        return JSONResponse(payload)

    @app.get("/graph/orphans", dependencies=[Depends(require_reader)], tags=["graph"])
    @limiter.limit(metrics_limit)
    def graph_orphans(
        request: Request,  # noqa: ARG001
        label: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
        service: GraphService = Depends(graph_service_dependency),
    ) -> JSONResponse:
        limit = max(1, min(limit, 200))
        try:
            payload = service.list_orphan_nodes(label=label, cursor=cursor, limit=limit)
        except GraphQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(payload)

    @app.post("/graph/cypher", dependencies=[Depends(require_maintainer)], tags=["graph"])
    @limiter.limit("30/minute")
    def graph_cypher(
        request: Request,  # noqa: ARG001
        payload: dict[str, Any] = Body(...),
        service: GraphService = Depends(graph_service_dependency),
    ) -> JSONResponse:
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

    return app


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
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:  # pragma: no cover - thin wrapper
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded", "error": str(exc)},
    )


def _build_health_report(app: FastAPI, settings: AppSettings) -> dict[str, object]:
    coverage = _coverage_health(settings)
    audit = _audit_health(settings)
    scheduler = _scheduler_health(app, settings)
    checks = {
        "coverage": coverage,
        "audit": audit,
        "scheduler": scheduler,
    }
    degraded_statuses = {"missing", "stale", "error", "stopped", "invalid"}
    overall = "ok"
    if any(check.get("status") in degraded_statuses for check in checks.values()):
        overall = "degraded"
    return {
        "status": overall,
        "checks": checks,
        "timestamp": time.time(),
    }


def _coverage_health(settings: AppSettings) -> dict[str, object]:
    report_path = settings.state_path / "reports" / "coverage_report.json"
    info: dict[str, object] = {
        "status": "disabled" if not settings.coverage_enabled else "missing",
        "path": str(report_path),
    }
    if not settings.coverage_enabled:
        return info
    if not report_path.exists():
        return info

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        info.update({"status": "invalid", "error": str(exc)})
        return info

    generated_at = data.get("generated_at")
    now = time.time()
    age = None
    if isinstance(generated_at, (int, float)):
        age = max(0.0, now - float(generated_at))

    missing_count = len(data.get("missing_artifacts") or [])
    summary = data.get("summary") or {}
    artifact_total = summary.get("artifact_total")

    status = "ok"
    if age is None:
        status = "invalid"
    else:
        if settings.scheduler_enabled:
            threshold = max(settings.scheduler_interval_minutes * 60 * 2, 3600)
        else:
            threshold = 86400
        if age > threshold:
            status = "stale"

    info.update(
        {
            "status": status,
            "age_seconds": age,
            "generated_at": generated_at,
            "missing_artifacts": missing_count,
            "artifact_total": artifact_total,
        }
    )
    return info


def _audit_health(settings: AppSettings) -> dict[str, object]:
    audit_path = settings.state_path / "audit" / "audit.db"
    info: dict[str, object] = {
        "status": "missing",
        "path": str(audit_path),
    }
    if not audit_path.exists():
        return info

    try:
        with sqlite3.connect(audit_path) as conn:
            conn.execute("SELECT 1")
    except Exception as exc:  # pragma: no cover - defensive
        info.update({"status": "error", "error": str(exc)})
        return info

    size = None
    with suppress(OSError):
        size = audit_path.stat().st_size

    info.update({"status": "ok", "size_bytes": size})
    return info


def _scheduler_health(app: FastAPI, settings: AppSettings) -> dict[str, object]:
    info: dict[str, object] = {
        "enabled": settings.scheduler_enabled,
        "interval_minutes": settings.scheduler_interval_minutes,
    }
    scheduler = getattr(app.state, "scheduler", None)
    if not settings.scheduler_enabled:
        info["status"] = "disabled"
        return info
    if scheduler is None or not getattr(scheduler, "_started", False):
        info["status"] = "stopped"
        return info

    info["status"] = "running"
    return info
