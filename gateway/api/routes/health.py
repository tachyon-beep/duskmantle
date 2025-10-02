"""Health and observability endpoints."""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter

from gateway.api.connections import (
    DependencyStatus,
    Neo4jConnectionManager,
    QdrantConnectionManager,
)
from gateway.api.dependencies import get_app_settings
from gateway.config.settings import AppSettings


def create_router(limiter: Limiter, metrics_limit: str) -> APIRouter:
    """Wire up health, readiness, and metrics endpoints."""
    router = APIRouter()

    @router.get("/healthz", tags=["health"])
    def healthz(
        request: Request,
        settings: AppSettings = Depends(get_app_settings),  # noqa: B008
    ) -> dict[str, object]:
        return build_health_report(request.app, settings)

    @router.get("/readyz", tags=["health"])
    def readyz() -> dict[str, str]:
        return {"status": "ready"}

    @router.get("/metrics", tags=["observability"])
    @limiter.limit(metrics_limit)
    def metrics_endpoint(request: Request) -> Response:
        del request
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return router


def build_health_report(app: FastAPI, settings: AppSettings) -> dict[str, object]:
    """Assemble the health payload consumed by `/healthz`."""
    coverage = _coverage_health(settings)
    audit = _audit_health(settings)
    scheduler = _scheduler_health(app, settings)
    graph = _graph_health(app, settings)
    qdrant = _qdrant_health(app, settings)
    checks = {
        "coverage": coverage,
        "audit": audit,
        "scheduler": scheduler,
        "graph": graph,
        "qdrant": qdrant,
    }
    degraded_statuses = {"missing", "stale", "error", "stopped", "invalid"}
    degraded_statuses.update({"degraded"})
    overall = "ok"
    if any(check.get("status") in degraded_statuses for check in checks.values()):
        overall = "degraded"
    return {
        "status": overall,
        "checks": checks,
        "timestamp": time.time(),
    }


def _coverage_health(settings: AppSettings) -> dict[str, Any]:
    report_path = settings.state_path / "reports" / "coverage_report.json"
    info: dict[str, Any] = {
        "status": "disabled" if not settings.coverage_enabled else "missing",
        "path": str(report_path),
    }
    if not settings.coverage_enabled:
        return info
    if not report_path.exists():
        return info

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - defensive
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


def _audit_health(settings: AppSettings) -> dict[str, Any]:
    audit_path = settings.state_path / "audit" / "audit.db"
    info: dict[str, Any] = {
        "status": "missing",
        "path": str(audit_path),
    }
    if not audit_path.exists():
        return info

    try:
        with sqlite3.connect(audit_path) as conn:
            conn.execute("SELECT 1")
    except sqlite3.Error as exc:  # pragma: no cover - defensive
        info.update({"status": "error", "error": str(exc)})
        return info

    size = None
    with suppress(OSError):
        size = audit_path.stat().st_size

    info.update({"status": "ok", "size_bytes": size})
    return info


def _scheduler_health(app: FastAPI, settings: AppSettings) -> dict[str, Any]:
    info: dict[str, Any] = {
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


def _graph_health(app: FastAPI, settings: AppSettings) -> dict[str, Any]:
    manager = getattr(app.state, "graph_manager", None)
    info = _dependency_health(manager)
    info["database"] = settings.neo4j_database
    return info


def _qdrant_health(app: FastAPI, settings: AppSettings) -> dict[str, Any]:
    manager = getattr(app.state, "qdrant_manager", None)
    info = _dependency_health(manager)
    info["collection"] = settings.qdrant_collection
    info["url"] = settings.qdrant_url
    return info


def _dependency_health(
    manager: Neo4jConnectionManager | QdrantConnectionManager | None,
) -> dict[str, Any]:
    if manager is None:
        return {"status": "missing"}
    snapshot: DependencyStatus = manager.describe()
    payload: dict[str, Any] = {
        "status": snapshot.status,
        "revision": snapshot.revision,
        "last_success": snapshot.last_success,
    }
    if snapshot.last_failure is not None:
        payload["last_failure"] = snapshot.last_failure
    if snapshot.last_error:
        payload["error"] = snapshot.last_error
    return payload


__all__ = ["create_router", "build_health_report"]
