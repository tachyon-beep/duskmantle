"""Helper functions for orchestrating state backups."""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path

from .exceptions import BackupExecutionError

_BACKUP_DONE_PATTERN = re.compile(r"Backup written to (?P<path>.+)$")


class BackupResult(dict):
    """Simple mapping describing the archive produced by a backup run."""

    archive: Path


def run_backup(
    *,
    state_path: Path,
    script_path: Path | None,
    destination_path: Path | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> BackupResult:
    """Execute the backup helper synchronously and return archive metadata."""

    resolved_script = script_path or _default_backup_script()
    if not resolved_script.exists():
        raise BackupExecutionError(f"Backup script not found: {resolved_script}")
    if not os.access(resolved_script, os.X_OK):
        raise BackupExecutionError(f"Backup script is not executable: {resolved_script}")

    destination = destination_path or state_path / "backups"
    destination.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("KM_BACKUP_SOURCE", str(state_path))
    env.setdefault("KM_BACKUP_DEST", str(destination))
    if extra_env:
        env.update(extra_env)

    process = subprocess.run(
        [str(resolved_script)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    if process.returncode != 0:
        stderr = process.stderr.strip()
        raise BackupExecutionError(
            f"Backup helper failed with code {process.returncode}: {stderr}",
        )

    archive_path = _parse_archive_path(process.stdout)
    if archive_path is None:
        raise BackupExecutionError("Backup helper completed but no archive path was reported")

    resolved_archive = Path(archive_path)
    if not resolved_archive.is_absolute():
        resolved_archive = (destination / resolved_archive).resolve()

    return BackupResult({"archive": resolved_archive})


def _parse_archive_path(output: str) -> str | None:
    for line in output.splitlines()[::-1]:
        match = _BACKUP_DONE_PATTERN.search(line.strip())
        if match:
            return match.group("path").strip()
    return None


def _default_backup_script() -> Path:
    return Path(__file__).resolve().parents[2] / "bin" / "km-backup"


__all__ = ["BackupResult", "run_backup"]
