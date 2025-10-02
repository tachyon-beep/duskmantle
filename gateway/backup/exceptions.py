"""Custom exceptions for gateway backup operations."""

from __future__ import annotations


class BackupExecutionError(RuntimeError):
    """Raised when the backup helper fails to produce an archive."""


__all__ = ["BackupExecutionError"]
