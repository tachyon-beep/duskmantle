"""Custom exceptions for the MCP adapter."""

from __future__ import annotations

from typing import Any


class MCPAdapterError(Exception):
    """Base error raised by the MCP bridge."""


class GatewayRequestError(MCPAdapterError):
    """Raised when the gateway API returns an error response."""

    def __init__(self, *, status_code: int, detail: str, payload: Any | None = None) -> None:
        self.status_code = status_code
        self.detail = detail
        self.payload = payload
        message = f"Gateway request failed with status {status_code}: {detail}"
        super().__init__(message)


class MissingTokenError(MCPAdapterError):
    """Raised when a privileged operation lacks an authentication token."""

    def __init__(self, scope: str) -> None:
        super().__init__(f"{scope} token is required for this operation")
        self.scope = scope


class BackupExecutionError(MCPAdapterError):
    """Raised when the backup helper fails to produce an archive."""


__all__ = [
    "MCPAdapterError",
    "GatewayRequestError",
    "MissingTokenError",
    "BackupExecutionError",
]
