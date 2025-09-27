"""Helpers for managing ingestion workflows via MCP."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any

from gateway.config.settings import get_settings
from gateway.ingest.service import execute_ingestion

from .config import MCPSettings


async def trigger_ingest(
    *,
    settings: MCPSettings,
    profile: str,
    dry_run: bool,
    use_dummy_embeddings: bool | None,
) -> dict[str, Any]:
    """Execute an ingestion run in a worker thread and return a serialisable summary."""

    app_settings = get_settings()
    result = await asyncio.to_thread(
        execute_ingestion,
        settings=app_settings,
        profile=profile,
        repo_override=settings.ingest_repo_override,
        dry_run=dry_run,
        use_dummy_embeddings=use_dummy_embeddings,
    )
    payload = asdict(result)
    # Normalise booleans (ensure JSON-friendly types)
    payload["success"] = bool(payload.get("success", False))
    return payload


async def latest_ingest_status(
    *,
    history: list[dict[str, Any]],
    profile: str | None,
) -> dict[str, Any] | None:
    """Return the newest ingest record optionally filtered by profile."""

    if not history:
        return None
    if profile is None:
        return history[0]
    for item in history:
        if item.get("profile") == profile:
            return item
    return None


__all__ = ["trigger_ingest", "latest_ingest_status"]
