"""Handlers for storing text via MCP."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from gateway.mcp.config import MCPSettings
from gateway.mcp.utils.files import DocumentCopyError, slugify, write_text_document

from .ingest import trigger_ingest


def _build_filename(title: str | None) -> str:
    if title:
        slug = slugify(title, fallback="note")
    else:
        slug = datetime.utcnow().strftime("note-%Y%m%d-%H%M%S")
    return f"{slug}.md"


def _normalise_destination(destination: str | None, default_dir: Path, filename: str) -> Path:
    if not destination:
        return default_dir / filename
    candidate = Path(destination)
    if candidate.suffix:
        return candidate
    return candidate / filename


def _compose_content(
    *,
    title: str | None,
    subsystem: str | None,
    tags: list[str] | None,
    metadata: dict[str, Any] | None,
    body: str,
) -> str:
    front_matter: dict[str, Any] = {}
    if title:
        front_matter["title"] = title
    if subsystem:
        front_matter["subsystem"] = subsystem
    if tags:
        cleaned = [tag for tag in (tag.strip() for tag in tags) if tag]
        if cleaned:
            front_matter["tags"] = cleaned
    if metadata:
        for key, value in metadata.items():
            if value is not None:
                front_matter[key] = value

    if not front_matter:
        return body

    lines = ["---"]
    for key, value in front_matter.items():
        if isinstance(value, list):
            rendered = "[" + ", ".join(str(item) for item in value) + "]"
            lines.append(f"{key}: {rendered}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---\n")
    lines.append(body)
    return "\n".join(lines)


async def handle_storetext(
    *,
    settings: MCPSettings,
    content: str,
    title: str | None,
    destination: str | None,
    subsystem: str | None,
    tags: list[str] | None,
    metadata: dict[str, Any] | None,
    overwrite: bool,
    ingest: bool,
) -> dict[str, Any]:
    if not content or not content.strip():
        raise ValueError("content must be a non-empty string")

    filename = _build_filename(title)
    relative_path = _normalise_destination(destination, settings.content_docs_subdir, filename)

    document_body = _compose_content(
        title=title,
        subsystem=subsystem,
        tags=tags,
        metadata=metadata,
        body=content if content.endswith("\n") else content + "\n",
    )

    try:
        destination_path = write_text_document(
            document_body,
            root=settings.content_root,
            relative_path=relative_path,
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
            raise RuntimeError("Ingest run triggered by km-storetext reported failure")

    return {
        "status": "success",
        "stored_path": str(destination_path),
        "relative_path": str(destination_path.relative_to(settings.content_root)),
        "ingest_triggered": ingest,
        "ingest_run": ingest_run,
    }


__all__ = ["handle_storetext"]
