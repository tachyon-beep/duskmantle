from __future__ import annotations

from fastapi import FastAPI

from gateway import get_version


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""
    app = FastAPI(
        title="Duskmantle Knowledge Gateway",
        version=get_version(),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get("/healthz", tags=["health"])
    def healthz() -> dict[str, str]:
        """Return basic health information for the gateway."""
        return {"status": "ok"}

    return app
