"""Utilities for exporting feedback logs into training datasets."""

from __future__ import annotations

import csv
import json
import logging
import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

FeedbackFormat = Literal["csv", "jsonl"]


@dataclass(slots=True)
class ExportOptions:
    """User-configurable options controlling dataset export."""

    output_path: Path
    output_format: FeedbackFormat
    require_vote: bool = False
    limit: int | None = None


@dataclass(slots=True)
class ExportStats:
    """Basic statistics about the export process."""

    total_events: int
    written_rows: int
    skipped_without_vote: int


FIELDNAMES: Sequence[str] = (
    "request_id",
    "timestamp",
    "rank",
    "query",
    "result_count",
    "chunk_id",
    "artifact_path",
    "artifact_type",
    "subsystem",
    "vector_score",
    "adjusted_score",
    "signal_subsystem_affinity",
    "signal_relationship_count",
    "signal_supporting_bonus",
    "signal_coverage_missing",
    "graph_context_present",
    "feedback_vote",
    "feedback_note",
    "context_json",
    "metadata_request_id",
    "metadata_graph_context_included",
    "metadata_warnings_count",
)


LOG_SUFFIX_PATTERN = re.compile(r"events\.log(?:\.(?P<index>\d+))?$")


def export_training_dataset(events_path: Path, *, options: ExportOptions) -> ExportStats:
    """Write feedback events from a single log into the requested dataset format."""
    return export_feedback_logs([events_path], options=options)


def export_feedback_logs(log_paths: Sequence[Path], *, options: ExportOptions) -> ExportStats:
    """Write feedback events from one or more log files into the requested dataset format."""
    resolved_paths = [path for path in log_paths if path.exists()]
    if not resolved_paths:
        logger.info("No feedback logs found for export (paths=%s)", log_paths)
        return ExportStats(total_events=0, written_rows=0, skipped_without_vote=0)

    events = _iter_feedback_logs(resolved_paths)

    if options.output_format == "csv":
        options.output_path.parent.mkdir(parents=True, exist_ok=True)
        written = _write_csv(events, options)
    elif options.output_format == "jsonl":
        options.output_path.parent.mkdir(parents=True, exist_ok=True)
        written = _write_jsonl(events, options)
    else:  # pragma: no cover - guarded by typing
        raise ValueError(f"Unsupported format: {options.output_format}")

    return written


def iter_feedback_events(path: Path) -> Iterator[dict[str, Any]]:
    """Yield feedback events from a JSON lines log file."""
    if not path.exists():
        logger.info("Feedback events log not found at %s", path)
        return
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Skipping malformed feedback line %s:%d (%s)",
                    path,
                    line_number,
                    exc,
                )
                continue


def discover_feedback_logs(root: Path, *, include_rotations: bool) -> list[Path]:
    """Return feedback log files in chronological order (oldest to newest)."""
    logs: list[tuple[int, Path]] = []
    if include_rotations:
        for candidate in root.glob("events.log.*"):
            match = LOG_SUFFIX_PATTERN.match(candidate.name)
            if not match:
                continue
            index_text = match.group("index")
            if not index_text:
                continue
            try:
                index = int(index_text)
            except ValueError:
                continue
            logs.append((index, candidate))

    base = root / "events.log"
    if base.exists():
        logs.append((0, base))

    if not logs:
        return []

    # Higher suffix numbers represent older rotated logs; iterate oldest first
    logs.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in logs]


def _iter_feedback_logs(paths: Sequence[Path]) -> Iterator[dict[str, Any]]:
    """Yield events from a sequence of log files."""
    for path in paths:
        yield from iter_feedback_events(path)


def _write_csv(events: Iterable[dict[str, Any]], options: ExportOptions) -> ExportStats:
    """Write feedback events into a CSV file."""
    total = 0
    written = 0
    skipped_without_vote = 0

    with options.output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for event in events:
            total += 1
            row = _flatten_event(event)
            if options.require_vote and row["feedback_vote"] is None:
                skipped_without_vote += 1
                continue
            writer.writerow(row)
            written += 1
            if options.limit and written >= options.limit:
                break

    return ExportStats(total_events=total, written_rows=written, skipped_without_vote=skipped_without_vote)


def _write_jsonl(events: Iterable[dict[str, Any]], options: ExportOptions) -> ExportStats:
    """Write feedback events into a JSONL file."""
    total = 0
    written = 0
    skipped_without_vote = 0

    with options.output_path.open("w", encoding="utf-8") as handle:
        for event in events:
            total += 1
            row = _flatten_event(event)
            if options.require_vote and row["feedback_vote"] is None:
                skipped_without_vote += 1
                continue
            handle.write(json.dumps(row, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")
            written += 1
            if options.limit and written >= options.limit:
                break

    return ExportStats(total_events=total, written_rows=written, skipped_without_vote=skipped_without_vote)


def _flatten_event(event: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested event data into scalar fields."""
    signals = event.get("signals") or {}
    metadata = event.get("metadata") or {}

    warnings_field = metadata.get("warnings")
    if isinstance(warnings_field, list):
        warnings_count = len(warnings_field)
    elif warnings_field is None:
        warnings_count = 0
    else:
        warnings_count = 1

    context_value = event.get("context")
    if isinstance(context_value, (dict, list)):
        context_json = json.dumps(context_value, separators=(",", ":"), ensure_ascii=False)
    elif context_value is None:
        context_json = None
    else:
        context_json = str(context_value)

    row: dict[str, Any] = {
        "request_id": event.get("request_id"),
        "timestamp": event.get("timestamp"),
        "rank": event.get("rank"),
        "query": event.get("query"),
        "result_count": event.get("result_count"),
        "chunk_id": event.get("chunk_id"),
        "artifact_path": event.get("artifact_path"),
        "artifact_type": event.get("artifact_type"),
        "subsystem": event.get("subsystem"),
        "vector_score": event.get("vector_score"),
        "adjusted_score": event.get("adjusted_score"),
        "signal_subsystem_affinity": signals.get("subsystem_affinity"),
        "signal_relationship_count": signals.get("relationship_count"),
        "signal_supporting_bonus": signals.get("supporting_bonus"),
        "signal_coverage_missing": signals.get("coverage_missing"),
        "graph_context_present": event.get("graph_context_present"),
        "feedback_vote": event.get("feedback_vote"),
        "feedback_note": event.get("feedback_note"),
        "context_json": context_json,
        "metadata_request_id": metadata.get("request_id"),
        "metadata_graph_context_included": metadata.get("graph_context_included"),
        "metadata_warnings_count": warnings_count,
    }
    return row


__all__ = [
    "ExportOptions",
    "ExportStats",
    "discover_feedback_logs",
    "export_feedback_logs",
    "export_training_dataset",
]
