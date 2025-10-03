"""Persistent storage helpers for search feedback events."""

from __future__ import annotations

import json
import threading
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from gateway.observability.metrics import (
    SEARCH_FEEDBACK_LOG_BYTES,
    SEARCH_FEEDBACK_ROTATIONS_TOTAL,
)
from gateway.search.service import SearchResponse


class SearchFeedbackStore:
    """Append-only store for search telemetry and feedback."""

    LOG_SUFFIX_TEMPLATE: Final[str] = "events.log.{}"

    def __init__(self, root: Path, *, max_bytes: int, max_files: int) -> None:
        """Initialise the feedback store beneath the given directory."""
        self.base_dir = root
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.base_dir / "events.log"
        self._lock = threading.Lock()
        self._max_bytes = max(1, int(max_bytes))
        self._max_files = max(1, int(max_files))

    def record(
        self,
        *,
        response: SearchResponse,
        feedback: Mapping[str, object] | None,
        context: object = None,
        request_id: str | None = None,
    ) -> None:
        """Persist a feedback event for the supplied search response."""
        if not response.results:
            return

        event_request_id = request_id or str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

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

    def _append(self, rows: Sequence[Mapping[str, object]]) -> None:
        if not rows:
            return
        payload = "\n".join(
            json.dumps(dict(row), separators=(",", ":"), ensure_ascii=False) for row in rows
        ) + "\n"
        encoded = payload.encode("utf-8")
        with self._lock:
            self._rotate_if_needed(len(encoded))
            with self.events_path.open("ab") as handle:
                handle.write(encoded)
            self._update_metrics()

    def _rotate_if_needed(self, incoming_size: int) -> None:
        current_size = self._current_size()
        if current_size + incoming_size <= self._max_bytes:
            return
        self._perform_rotation()
        SEARCH_FEEDBACK_ROTATIONS_TOTAL.inc()

    def _perform_rotation(self) -> None:
        if self._max_files <= 1:
            if self.events_path.exists():
                self.events_path.unlink(missing_ok=True)
            return

        for index in range(self._max_files - 1, 0, -1):
            src = self._suffix_path(index - 1)
            dst = self._suffix_path(index)
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)

        if self.events_path.exists():
            first_archive = self._suffix_path(1)
            if first_archive.exists():
                first_archive.unlink()
            self.events_path.rename(first_archive)

    def _suffix_path(self, index: int) -> Path:
        if index <= 0:
            return self.events_path
        return self.base_dir / self.LOG_SUFFIX_TEMPLATE.format(index)

    def _current_size(self) -> int:
        try:
            return self.events_path.stat().st_size
        except FileNotFoundError:
            return 0

    def _update_metrics(self) -> None:
        try:
            size = self.events_path.stat().st_size
        except FileNotFoundError:
            size = 0
        SEARCH_FEEDBACK_LOG_BYTES.set(size)


def _serialize_results(
    *,
    response: SearchResponse,
    request_id: str,
    timestamp: str,
    vote: float | None,
    note: str | None,
    context: object,
    feedback: Mapping[str, object] | None,
) -> list[dict[str, object]]:
    metadata = dict(response.metadata)
    event_context = context if isinstance(context, (dict, list, str)) else None
    if context is not None and event_context is None:
        event_context = repr(context)

    rows: list[dict[str, object]] = []
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
