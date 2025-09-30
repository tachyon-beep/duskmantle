"""Core package for the Duskmantle knowledge gateway."""

from __future__ import annotations

__all__ = ["__version__", "get_version"]

__version__ = "1.1.0"


def get_version() -> str:
    """Return the current package version."""
    return __version__
