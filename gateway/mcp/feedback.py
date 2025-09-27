"""Feedback logging utilities used by MCP tools."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import MCPSettings


async def record_feedback(
    *,
    settings: MCPSettings,
    request_id: str,
    chunk_id: str,
    vote: float | None,
    note: str | None,
    context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Append a manual feedback entry to the state directory."""

    payload = {
        "request_id": request_id,
        "chunk_id": chunk_id,
        "vote": vote,
        "note": note,
        "context": context,
        "timestamp": datetime.now(UTC).isoformat(),
        "source": "mcp.manual",
    }

    path = settings.state_path / "feedback" / "manual-events.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    await asyncio.to_thread(_append_line, path, line)
    return payload


def _append_line(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.write("\n")


__all__ = ["record_feedback"]
