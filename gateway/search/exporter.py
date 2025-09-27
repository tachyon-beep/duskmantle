from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Literal, Sequence

logger = logging.getLogger(__name__)

FeedbackFormat = Literal["csv", "jsonl"]


@dataclass(slots=True)
class ExportOptions:
    output_path: Path
    output_format: FeedbackFormat
    require_vote: bool = False
    limit: int | None = None


@dataclass(slots=True)
class ExportStats:
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


def export_training_dataset(events_path: Path, *, options: ExportOptions) -> ExportStats:
    events = iter_feedback_events(events_path)

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


def _write_csv(events: Iterable[dict[str, Any]], options: ExportOptions) -> ExportStats:
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


def _flatten_event(event: Dict[str, Any]) -> Dict[str, Any]:
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

    row: Dict[str, Any] = {
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
    "export_training_dataset",
]
