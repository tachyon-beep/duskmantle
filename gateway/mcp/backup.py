"""Backup helpers for the MCP server."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from gateway.backup.service import run_backup

from .config import MCPSettings


async def trigger_backup(settings: MCPSettings) -> dict[str, Any]:
    """Invoke the km-backup helper and return the resulting archive metadata."""

    script_path = settings.backup_script or Path(__file__).resolve().parents[2] / "bin" / "km-backup"
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: run_backup(
            state_path=settings.state_path,
            script_path=script_path,
        ),
    )
    archive = Path(result["archive"]).resolve()
    return {"archive": str(archive)}


__all__ = ["trigger_backup"]
