"""Observability and reporting routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter

from gateway.api.auth import require_maintainer
from gateway.api.dependencies import get_app_settings
from gateway.config.settings import AppSettings
from gateway.ingest.audit import AuditLogger
from gateway.ingest.lifecycle import summarize_lifecycle


def create_router(limiter: Limiter) -> APIRouter:
    """Expose reporting and audit endpoints protected by maintainer auth."""
    router = APIRouter()

    @router.get("/audit/history", dependencies=[Depends(require_maintainer)], tags=["observability"])
    @limiter.limit("30/minute")
    def audit_history(
        request: Request,
        settings: AppSettings = Depends(get_app_settings),  # noqa: B008
        limit: int = 20,
    ) -> JSONResponse:
        del request
        audit_path = settings.state_path / "audit" / "audit.db"
        audit_logger = AuditLogger(audit_path)
        return JSONResponse(audit_logger.recent(limit=limit))

    @router.get("/coverage", dependencies=[Depends(require_maintainer)], tags=["observability"])
    @limiter.limit("30/minute")
    def coverage_report(
        request: Request,
        settings: AppSettings = Depends(get_app_settings),  # noqa: B008
    ) -> JSONResponse:
        del request
        report_path = settings.state_path / "reports" / "coverage_report.json"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Coverage report not found")

        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail="Coverage report is invalid JSON") from exc
        return JSONResponse(data)

    @router.get("/lifecycle", dependencies=[Depends(require_maintainer)], tags=["observability"])
    @limiter.limit("30/minute")
    def lifecycle_report(
        request: Request,
        settings: AppSettings = Depends(get_app_settings),  # noqa: B008
    ) -> JSONResponse:
        del request
        report_path = settings.state_path / "reports" / "lifecycle_report.json"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Lifecycle report not found")

        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail="Lifecycle report is invalid JSON") from exc
        return JSONResponse(data)

    @router.get("/lifecycle/history", dependencies=[Depends(require_maintainer)], tags=["observability"])
    @limiter.limit("30/minute")
    def lifecycle_history(
        request: Request,
        settings: AppSettings = Depends(get_app_settings),  # noqa: B008
        limit: int = 30,
    ) -> JSONResponse:
        del request
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
            files = sorted(
                history_dir.glob("lifecycle_*.json"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )[:limit_normalized]
        entries: list[dict[str, Any]] = []
        for path_entry in reversed(files):
            try:
                payload = json.loads(path_entry.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            summary = summarize_lifecycle(payload)
            summary["path"] = path_entry.name
            entries.append(summary)
        return JSONResponse({"history": entries})

    return router


__all__ = ["create_router"]
