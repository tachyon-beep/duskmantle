"""Helper functions for orchestrating state backups."""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path

from .exceptions import BackupExecutionError

_BACKUP_DONE_PATTERN = re.compile(r"Backup written to (?P<path>.+)$")

ARCHIVE_FILENAME_PREFIX = "km-backup-"
ARCHIVE_ALLOWED_SUFFIXES = (".tgz", ".tar.gz")
DEFAULT_BACKUP_DIRNAME = "backups"
DEFAULT_BACKUP_ARCHIVE_DIRNAME = "archives"


class BackupResult(dict):
    """Simple mapping describing the archive produced by a backup run."""

    archive: Path


def default_backup_destination(state_path: Path) -> Path:
    """Return the default directory for storing backup archives."""

    return (state_path / DEFAULT_BACKUP_DIRNAME / DEFAULT_BACKUP_ARCHIVE_DIRNAME).resolve()


def is_backup_archive(path: Path) -> bool:
    """Return ``True`` when ``path`` matches the managed backup filename pattern."""

    if not path.is_file() or not path.name.startswith(ARCHIVE_FILENAME_PREFIX):
        return False
    name_lower = path.name.lower()
    return any(name_lower.endswith(suffix) for suffix in ARCHIVE_ALLOWED_SUFFIXES)


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

    destination = (destination_path or default_backup_destination(state_path)).resolve()
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

    size_bytes: int | None = None
    with suppress(OSError):
        size_bytes = resolved_archive.stat().st_size

    return BackupResult({"archive": resolved_archive, "size_bytes": size_bytes})


def _parse_archive_path(output: str) -> str | None:
    for line in output.splitlines()[::-1]:
        match = _BACKUP_DONE_PATTERN.search(line.strip())
        if match:
            return match.group("path").strip()
    return None


def _default_backup_script() -> Path:
    return Path(__file__).resolve().parents[2] / "bin" / "km-backup"


__all__ = [
    "ARCHIVE_ALLOWED_SUFFIXES",
    "ARCHIVE_FILENAME_PREFIX",
    "BackupResult",
    "default_backup_destination",
    "is_backup_archive",
    "run_backup",
]
