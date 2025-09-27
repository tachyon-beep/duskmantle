from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from gateway.search.service import SearchResult, SearchResponse


class SearchFeedbackStore:
    """Append-only store for search telemetry and feedback."""

    def __init__(self, root: Path) -> None:
        self.base_dir = root
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.base_dir / "events.log"
        self._lock = threading.Lock()

    def record(
        self,
        *,
        response: SearchResponse,
        feedback: Mapping[str, Any] | None,
        context: Any = None,
        request_id: str | None = None,
    ) -> None:
        if not response.results:
            return

        event_request_id = request_id or str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        vote = None
        if feedback is not None:
            raw_vote = feedback.get("vote")
            if isinstance(raw_vote, (int, float)):
                vote = float(raw_vote)
            elif isinstance(raw_vote, str):
                try:
                    vote = float(raw_vote)
                except ValueError:
                    vote = None

        note = None
        if feedback is not None:
            comment_value = feedback.get("note") or feedback.get("comment")
            if isinstance(comment_value, str):
                note = comment_value

        rows = _serialize_results(
            response=response,
            request_id=event_request_id,
            timestamp=timestamp,
            vote=vote,
            note=note,
            context=context,
            feedback=feedback,
        )
        self._append(rows)

    def _append(self, rows: Sequence[dict[str, Any]]) -> None:
        if not rows:
            return
        payload = "\n".join(json.dumps(row, separators=(",", ":"), ensure_ascii=False) for row in rows)
        with self._lock:
            with self.events_path.open("a", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")


def _serialize_results(
    *,
    response: SearchResponse,
    request_id: str,
    timestamp: str,
    vote: float | None,
    note: str | None,
    context: Any,
    feedback: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    metadata = dict(response.metadata)
    event_context = context if isinstance(context, (dict, list, str)) else None
    if context is not None and event_context is None:
        event_context = repr(context)

    rows: list[dict[str, Any]] = []
    for index, result in enumerate(response.results, start=1):
        chunk = dict(result.chunk)
        scoring = dict(result.scoring)
        signals = scoring.get("signals") or {}
        rows.append(
            {
                "request_id": request_id,
                "timestamp": timestamp,
                "rank": index,
                "query": response.query,
                "result_count": metadata.get("result_count"),
                "chunk_id": chunk.get("chunk_id"),
                "artifact_path": chunk.get("artifact_path"),
                "artifact_type": chunk.get("artifact_type"),
                "subsystem": chunk.get("subsystem"),
                "vector_score": scoring.get("vector_score"),
                "adjusted_score": scoring.get("adjusted_score"),
                "signals": signals,
                "graph_context_present": result.graph_context is not None,
                "metadata": metadata,
                "feedback_vote": vote,
                "feedback_note": note,
                "feedback_raw": dict(feedback) if feedback is not None else None,
                "context": event_context,
            }
        )
    return rows


__all__ = ["SearchFeedbackStore"]
