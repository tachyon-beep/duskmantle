"""Backup helpers for the MCP server."""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any

from .config import MCPSettings
from .exceptions import BackupExecutionError

_BACKUP_DONE_PATTERN = re.compile(r"Backup written to (?P<path>.+)$")


async def trigger_backup(settings: MCPSettings) -> dict[str, Any]:
    """Invoke the km-backup helper and return the resulting archive metadata."""

    script_path = settings.backup_script
    if script_path is None:
        script_path = _default_backup_script()

    if not script_path.exists():
        raise BackupExecutionError(f"Backup script not found: {script_path}")
    if not os.access(script_path, os.X_OK):
        raise BackupExecutionError(f"Backup script is not executable: {script_path}")

    env = os.environ.copy()
    env.setdefault("KM_BACKUP_SOURCE", str(settings.state_path))
    env.setdefault("KM_BACKUP_DEST", str(settings.state_path / "backups"))

    process = await asyncio.create_subprocess_exec(
        str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise BackupExecutionError(f"Backup helper failed with code {process.returncode}: {stderr.decode().strip()}")

    archive_path = _parse_archive_path(stdout.decode())
    if archive_path is None:
        raise BackupExecutionError("Backup helper completed but no archive path was reported")

    return {"archive": archive_path}


def _parse_archive_path(output: str) -> str | None:
    for line in output.splitlines()[::-1]:
        match = _BACKUP_DONE_PATTERN.search(line.strip())
        if match:
            return match.group("path")
    return None


def _default_backup_script() -> Path:
    return Path(__file__).resolve().parents[2] / "bin" / "km-backup"


__all__ = ["trigger_backup"]
