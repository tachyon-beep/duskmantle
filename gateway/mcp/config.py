"""Configuration for the MCP adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class MCPSettings(BaseSettings):
    """Settings controlling the MCP server runtime."""

    gateway_url: str = Field(
        "http://localhost:8000",
        alias="KM_GATEWAY_URL",
        description="Base URL of the gateway API",
    )
    reader_token: str | None = Field(
        default=None,
        alias="KM_READER_TOKEN",
        description="Bearer token for reader-scoped operations",
    )
    admin_token: str | None = Field(
        default=None,
        alias="KM_ADMIN_TOKEN",
        description="Bearer token for maintainer-scoped operations",
    )
    request_timeout_seconds: float = Field(
        default=30.0,
        alias="KM_MCP_TIMEOUT_SECONDS",
        description="HTTP request timeout when talking to the gateway",
    )
    verify_ssl: bool = Field(
        default=True,
        alias="KM_MCP_VERIFY_SSL",
        description="Whether to verify TLS certificates when contacting the gateway",
    )
    state_path: Path = Field(
        default=Path("/opt/knowledge/var"),
        alias="KM_STATE_PATH",
        description="Path containing gateway state files (audit logs, backups, feedback)",
    )
    content_root: Path = Field(
        default=Path("/workspace/repo"),
        alias="KM_CONTENT_ROOT",
        description="Root directory where MCP upload/storetext helpers write content",
    )
    content_docs_subdir: Path = Field(
        default=Path("docs"),
        alias="KM_CONTENT_DOCS_SUBDIR",
        description="Default subdirectory under the content root for text documents",
    )
    upload_default_overwrite: bool = Field(
        default=False,
        alias="KM_UPLOAD_DEFAULT_OVERWRITE",
        description="Allow MCP uploads to overwrite existing files by default",
    )
    upload_default_ingest: bool = Field(
        default=False,
        alias="KM_UPLOAD_DEFAULT_INGEST",
        description="Trigger an ingest run immediately after MCP uploads by default",
    )
    ingest_profile_default: str = Field(
        default="manual",
        alias="KM_MCP_DEFAULT_INGEST_PROFILE",
        description="Default profile label applied to manual ingest runs",
    )
    ingest_repo_override: Path | None = Field(
        default=None,
        alias="KM_MCP_REPO_ROOT",
        description="Optional repository root override for MCP-triggered ingest runs",
    )
    backup_script: Path | None = Field(
        default=None,
        alias="KM_MCP_BACKUP_SCRIPT",
        description="Override path to the km-backup helper script",
    )
    log_requests: bool = Field(
        default=False,
        alias="KM_MCP_LOG_REQUESTS",
        description="Enable verbose logging for outbound HTTP requests",
    )
    transport: Literal["stdio", "http", "sse", "streamable-http"] = Field(
        default="stdio",
        alias="KM_MCP_TRANSPORT",
        description="Default transport used when launching the MCP server",
    )

    model_config = {
        "env_file": None,
        "case_sensitive": False,
        "extra": "ignore",
    }


__all__ = ["MCPSettings"]
