"""Primary FastAPI application wiring for the knowledge gateway."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager, suppress
from typing import cast
from uuid import uuid4

from apscheduler.schedulers.base import SchedulerNotRunningError  # type: ignore[import-untyped]
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from qdrant_client import QdrantClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from gateway import get_version
from gateway.api import connections as connection_utils
from gateway.api.connections import Neo4jConnectionManager, QdrantConnectionManager
from gateway.api.routes import graph as graph_routes
from gateway.api.routes import health as health_routes
from gateway.api.routes import reporting as reporting_routes
from gateway.api.routes import search as search_routes
from gateway.config.settings import AppSettings, get_settings
from gateway.graph import get_graph_service
from gateway.graph.migrations import MigrationRunner
from gateway.observability import (
    GRAPH_MIGRATION_LAST_STATUS,
    GRAPH_MIGRATION_LAST_TIMESTAMP,
    configure_logging,
    configure_tracing,
)
from gateway.scheduler import IngestionScheduler
from gateway.search.feedback import SearchFeedbackStore
from gateway.search.trainer import ModelArtifact, load_artifact
from gateway.ui import get_static_path
from gateway.ui import router as ui_router

logger = logging.getLogger(__name__)

DEPENDENCY_HEARTBEAT_INTERVAL_SECONDS = 30.0


def _validate_auth_settings(settings: AppSettings) -> None:
    if not settings.neo4j_auth_enabled:
        logger.warning(
            "Neo4j authentication disabled via KM_NEO4J_AUTH_ENABLED=false; Bolt endpoints accept anonymous connections",
        )
    if not settings.auth_enabled:
        return
    missing: list[str] = []
    if not settings.maintainer_token:
        missing.append("KM_ADMIN_TOKEN")
    sanitized_password = settings.neo4j_password.strip()
    if settings.neo4j_auth_enabled:
        if not sanitized_password:
            missing.append("KM_NEO4J_PASSWORD (non-empty value)")
        elif settings.auth_mode == "secure" and sanitized_password in {"neo4jadmin", "neo4j", "neo4jpass"}:
            missing.append("KM_NEO4J_PASSWORD (non-default value)")
    if missing:
        formatted = ", ".join(missing)
        raise RuntimeError(
            "Authentication is enabled but required credentials are missing: "
            f"{formatted}. Disable auth or provide the credentials before starting the gateway."
        )
    if not settings.reader_token:
        logger.warning("Auth enabled without KM_READER_TOKEN; maintainer token will service reader endpoints")


def _log_startup_configuration(settings: AppSettings) -> None:
    weight_profile_name, resolved_weights = settings.resolved_search_weights()
    logger.info(
        "Gateway startup configuration initialised",
        extra={
            "event": "startup_config",
            "version": get_version(),
            "auth_enabled": settings.auth_enabled,
            "auth_mode": settings.auth_mode,
            "neo4j_auth_enabled": settings.neo4j_auth_enabled,
            "graph_auto_migrate": settings.graph_auto_migrate,
            "embedding_model": settings.embedding_model,
            "ingest_window": settings.ingest_window,
            "ingest_overlap": settings.ingest_overlap,
            "search_weight_profile": weight_profile_name,
            "search_weights": resolved_weights,
        },
    )


def _build_lifespan(settings: AppSettings) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        scheduler = IngestionScheduler(
            settings,
            graph_manager=getattr(app.state, "graph_manager", None),
            qdrant_manager=getattr(app.state, "qdrant_manager", None),
        )
        scheduler.start()
        app.state.scheduler = scheduler
        heartbeat_task: asyncio.Task[None] | None = None
        try:
            graph_manager = getattr(app.state, "graph_manager", None)
            qdrant_manager = getattr(app.state, "qdrant_manager", None)
            if graph_manager or qdrant_manager:
                heartbeat_task = asyncio.create_task(
                    _dependency_heartbeat_loop(app, DEPENDENCY_HEARTBEAT_INTERVAL_SECONDS),
                )
                app.state.dependency_heartbeat_task = heartbeat_task
            yield
        finally:  # pragma: no cover - exercised via integration tests
            if heartbeat_task is not None:
                heartbeat_task.cancel()
                with suppress(asyncio.CancelledError):
                    await heartbeat_task
            try:
                scheduler.shutdown()
            except SchedulerNotRunningError:
                pass
            for manager_name in ("graph_manager", "qdrant_manager"):
                manager = getattr(app.state, manager_name, None)
                if manager is None:
                    continue
                with suppress(Exception):
                    manager.mark_failure(None)

    return cast(Callable[[FastAPI], AbstractAsyncContextManager[None]], lifespan)


def _configure_rate_limits(app: FastAPI, settings: AppSettings) -> Limiter:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds"],
    )
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    return limiter


def _init_feedback_store(settings: AppSettings) -> SearchFeedbackStore | None:
    try:
        return SearchFeedbackStore(settings.state_path / "feedback")
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:  # pragma: no cover - defensive guard
        logger.warning("Search feedback logging disabled: %s", exc)
        return None


def _load_search_model(settings: AppSettings) -> ModelArtifact | None:
    if settings.search_scoring_mode != "ml":
        return None
    model_path = settings.search_model_path or settings.state_path / "feedback" / "models" / "model.json"
    try:
        model_artifact = load_artifact(model_path)
        logger.info("Loaded search ranking model from %s", model_path)
        return model_artifact
    except FileNotFoundError:
        logger.warning(
            "Search scoring mode set to 'ml' but model file %s not found; falling back to heuristic",
            model_path,
        )
    except (json.JSONDecodeError, OSError, ValueError) as exc:  # pragma: no cover - defensive
        logger.warning("Failed to load search ranking model: %s", exc)
    return None



def _initialise_graph_manager(manager: Neo4jConnectionManager, settings: AppSettings) -> None:
    try:
        driver = manager.get_write_driver()
    except Exception as exc:
        logger.warning("Neo4j unavailable during startup: %s", exc)
        _set_migration_metrics(0, timestamp=time.time())
        return

    if not _verify_graph_database(driver, settings.neo4j_database):
        logger.warning("Neo4j database validation failed during startup")
        manager.mark_failure(RuntimeError("database validation failed"))
        _set_migration_metrics(0, timestamp=time.time())
        return

    if settings.graph_auto_migrate:
        _run_graph_auto_migration(driver, settings.neo4j_database)
    else:
        logger.info("Graph auto-migration disabled; run `gateway-graph migrate` during deployment")
        _set_migration_metrics(-1, timestamp=None)


def _initialise_qdrant_manager(manager: QdrantConnectionManager) -> None:
    manager.heartbeat()


async def _dependency_heartbeat_loop(app: FastAPI, interval: float) -> None:
    while True:  # pragma: no branch - cancellation exits loop
        graph_manager = getattr(app.state, "graph_manager", None)
        if graph_manager is not None:
            graph_manager.heartbeat()
        qdrant_manager = getattr(app.state, "qdrant_manager", None)
        if qdrant_manager is not None:
            qdrant_manager.heartbeat()
        await asyncio.sleep(interval)


def _verify_graph_database(driver: Driver, database: str) -> bool:
    try:
        with driver.session(database=database) as session:
            session.run("RETURN 1 AS ok").consume()
    except Neo4jError as exc:
        code = getattr(exc, "code", "") or ""
        if "DatabaseNotFound" in code:
            logger.error(
                "Neo4j database '%s' not found; update KM_NEO4J_DATABASE or create the database before starting",
                database,
            )
        else:
            logger.warning("Neo4j database '%s' validation query failed: %s", database, exc)
        return False
    except ServiceUnavailable as exc:
        logger.warning("Neo4j database '%s' unavailable during validation: %s", database, exc)
        return False
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning("Unexpected error validating Neo4j database '%s': %s", database, exc)
        return False
    return True


def _run_graph_auto_migration(driver: Driver, database: str) -> None:
    runner = MigrationRunner(driver=driver, database=database)
    pending = _fetch_pending_migrations(runner)
    _log_migration_plan(pending)

    try:
        runner.run()
    except (Neo4jError, RuntimeError) as exc:  # pragma: no cover - defensive
        logger.exception("Graph auto-migration failed: %s", exc)
        _set_migration_metrics(0, timestamp=time.time())
        return

    _log_migration_completion(pending)
    _set_migration_metrics(1, timestamp=time.time())


def _fetch_pending_migrations(runner: MigrationRunner) -> list[str] | None:
    try:
        return runner.pending_ids()
    except (Neo4jError, RuntimeError) as exc:  # pragma: no cover - defensive preflight
        logger.warning(
            "Graph auto-migration preflight failed; attempting run anyway: %s",
            exc,
        )
        return None


def _log_migration_plan(pending: list[str] | None) -> None:
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


def _log_migration_completion(pending: list[str] | None) -> None:
    if pending is None:
        logger.info("Graph auto-migration completed")
    elif pending:
        logger.info(
            "Graph auto-migration completed; applied %d migration(s)",
            len(pending),
        )
    else:
        logger.info("Graph auto-migration completed; no migrations were pending")


def _set_migration_metrics(status: int, *, timestamp: float | None) -> None:
    GRAPH_MIGRATION_LAST_STATUS.set(status)
    GRAPH_MIGRATION_LAST_TIMESTAMP.set(timestamp if timestamp is not None else 0)


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""
    configure_logging()
    settings = get_settings()
    _validate_auth_settings(settings)
    _log_startup_configuration(settings)

    app = FastAPI(
        title="Duskmantle Knowledge Gateway",
        version=get_version(),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_build_lifespan(settings),
    )
    app.state.settings = settings
    app.mount("/ui/static", StaticFiles(directory=str(get_static_path())), name="ui-static")
    app.include_router(ui_router)

    @app.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get("x-request-id")
        request_id = incoming or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        if "X-Request-ID" not in response.headers:
            response.headers["X-Request-ID"] = request_id
        return response

    configure_tracing(app, settings)

    app.state.search_feedback_store = _init_feedback_store(settings)
    app.state.search_model_artifact = _load_search_model(settings)
    connection_utils.GRAPH_DRIVER_FACTORY = getattr(GraphDatabase, "driver")
    connection_utils.QDRANT_CLIENT_FACTORY = QdrantClient

    graph_manager = Neo4jConnectionManager(settings, logger)
    qdrant_manager = QdrantConnectionManager(settings, logger)
    app.state.graph_manager = graph_manager
    app.state.qdrant_manager = qdrant_manager
    app.state.graph_service_revision = None
    app.state.graph_service_instance = None
    app.state.qdrant_revision = None
    app.state.dependency_heartbeat_task = None
    app.state.graph_service_factory = get_graph_service

    _initialise_graph_manager(graph_manager, settings)
    _initialise_qdrant_manager(qdrant_manager)
    app.state.graph_service_revision = graph_manager.revision
    app.state.qdrant_revision = qdrant_manager.revision
    app.state.search_embedder = None
    app.state.scheduler = None

    limiter = _configure_rate_limits(app, settings)
    metrics_limit = f"{settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds"

    from gateway.api.dependencies import (
        get_graph_service_dependency,
        get_search_service_dependency,
    )

    app.state.graph_service_dependency = get_graph_service_dependency
    app.state.search_service_dependency = get_search_service_dependency

    app.include_router(health_routes.create_router(limiter, metrics_limit))
    app.include_router(reporting_routes.create_router(limiter))
    app.include_router(search_routes.create_router(limiter, metrics_limit))
    app.include_router(graph_routes.create_router(limiter, metrics_limit))

    return app


def _rate_limit_handler(_request: Request, exc: Exception) -> JSONResponse:  # pragma: no cover - thin wrapper
    if not isinstance(exc, RateLimitExceeded):
        raise exc
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded", "error": str(exc)},
    )
