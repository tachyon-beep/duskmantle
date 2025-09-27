"""Model Context Protocol server integration for the knowledge gateway."""

from .config import MCPSettings
from .server import build_server

__all__ = ["MCPSettings", "build_server"]
