"""Handlers for MCP file uploads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gateway.mcp.config import MCPSettings
from gateway.mcp.utils.files import DocumentCopyError, copy_into_root

from .ingest import trigger_ingest


async def handle_upload(
    *,
    settings: MCPSettings,
    source_path: str,
    destination: str | None,
    overwrite: bool,
    ingest: bool,
) -> dict[str, Any]:
    """Copy ``source_path`` into the configured content root and optionally trigger ingest."""

    if not source_path or not source_path.strip():
        raise ValueError("source_path must be provided")

    source = Path(source_path).expanduser()
    if not source.exists() or not source.is_file():
        raise ValueError(f"Source file {source} does not exist or is not a regular file")

    root = settings.content_root
    docs_dir = settings.content_docs_subdir

    relative_destination = _resolve_destination(destination, docs_dir, source.name)

    try:
        result = copy_into_root(
            source=source,
            root=root,
            destination=relative_destination,
            overwrite=overwrite,
        )
    except DocumentCopyError as exc:
        raise ValueError(str(exc)) from exc

    ingest_run: dict[str, Any] | None = None
    if ingest:
        ingest_run = await trigger_ingest(
            settings=settings,
            profile=settings.ingest_profile_default,
            dry_run=False,
            use_dummy_embeddings=None,
        )
        if not ingest_run.get("success", False):
            raise RuntimeError(
                "Ingest run triggered by km-upload reported failure; check gateway logs for details"
            )

    stored_relative = result.destination.relative_to(root)
    return {
        "status": "success",
        "stored_path": str(result.destination),
        "relative_path": str(stored_relative),
        "overwritten": result.overwritten,
        "ingest_triggered": ingest,
        "ingest_run": ingest_run,
    }


def _resolve_destination(destination: str | None, default_dir: Path, filename: str) -> Path:
    if not destination:
        return default_dir / filename
    candidate = Path(destination)
    if candidate.suffix:
        return candidate
    return candidate / filename


__all__ = ["handle_upload"]
