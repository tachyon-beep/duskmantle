from __future__ import annotations

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from gateway import get_version
from gateway.api.auth import require_maintainer
from gateway.config.settings import get_settings
from gateway.observability.logging import configure_logging
from gateway.scheduler import IngestionScheduler


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""
    configure_logging()
    settings = get_settings()

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[
            f"{settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds"
        ],
    )

    app = FastAPI(
        title="Duskmantle Knowledge Gateway",
        version=get_version(),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.state.limiter = limiter
    app.state.scheduler = None
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - exercised in integration tests
        scheduler = IngestionScheduler(settings)
        scheduler.start()
        app.state.scheduler = scheduler

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # pragma: no cover - exercised in integration tests
        scheduler = getattr(app.state, "scheduler", None)
        if scheduler:
            scheduler.shutdown()

    @app.get("/healthz", tags=["health"])
    def healthz() -> dict[str, str]:
        """Return basic health information for the gateway."""
        return {"status": "ok"}

    @app.get("/readyz", tags=["health"])
    def readyz() -> dict[str, str]:
        """Return readiness information suitable for container orchestration."""
        return {"status": "ready"}

    metrics_limit = (
        f"{settings.rate_limit_requests} per {settings.rate_limit_window_seconds} seconds"
    )

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

    return app


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:  # pragma: no cover - thin wrapper
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded", "error": str(exc)},
    )
