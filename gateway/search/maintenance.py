"""Maintenance routines for pruning feedback logs and redacting datasets."""

from __future__ import annotations

import csv
import json
import logging
import shutil
from collections.abc import Iterable, MutableMapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gateway.search.exporter import iter_feedback_events

logger = logging.getLogger(__name__)

_FALLBACK_TIMESTAMP = datetime.fromordinal(1).replace(tzinfo=UTC)


@dataclass(slots=True)
class PruneOptions:
    """Configures retention rules for the feedback log pruning routine."""

    max_age_days: int | None = None
    max_requests: int | None = None
    output_path: Path | None = None
    current_time: datetime | None = None


@dataclass(slots=True)
class PruneStats:
    """Summary of how many feedback requests were kept versus removed."""

    total_requests: int
    retained_requests: int
    removed_requests: int


@dataclass(slots=True)
class RedactOptions:
    """Toggles that control which sensitive fields should be redacted."""

    output_path: Path | None = None
    drop_query: bool = False
    drop_context: bool = False
    drop_note: bool = False


@dataclass(slots=True)
class RedactStats:
    """Summary of how many dataset rows required redaction."""

    total_rows: int
    redacted_rows: int


def prune_feedback_log(events_path: Path, *, options: PruneOptions) -> PruneStats:
    """Prune feedback requests based on age and count thresholds."""

    if not events_path.exists():
        raise FileNotFoundError(f"Feedback log not found: {events_path}")
    if options.max_age_days is None and options.max_requests is None:
        raise ValueError("At least one of max_age_days or max_requests must be provided")

    events_by_request, request_order = _collect_events(events_path)
    total_requests = len(events_by_request)
    if total_requests == 0:
        return PruneStats(total_requests=0, retained_requests=0, removed_requests=0)

    timestamps = _build_timestamps(events_by_request)
    now = options.current_time or datetime.now(UTC)
    selected_ids = _apply_prune_filters(request_order, timestamps, options, now)
    retained_order = _preserve_original_order(request_order, selected_ids)

    if not retained_order:
        logger.warning("Prune operation would remove all feedback events; skipping")
        return PruneStats(
            total_requests=total_requests,
            retained_requests=total_requests,
            removed_requests=0,
        )

    destination = options.output_path or events_path
    _write_retained_events(destination, retained_order, events_by_request)

    retained_count = len(retained_order)
    removed_count = total_requests - retained_count
    return PruneStats(
        total_requests=total_requests,
        retained_requests=retained_count,
        removed_requests=removed_count,
    )


def redact_dataset(dataset_path: Path, *, options: RedactOptions) -> RedactStats:
    """Redact sensitive fields from datasets stored as CSV or JSON Lines."""

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    suffix = dataset_path.suffix.lower()
    output_path = options.output_path or dataset_path
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")

    if suffix == ".csv":
        stats = _redact_csv(dataset_path, tmp_path, options)
    elif suffix in {".jsonl", ".json"}:
        stats = _redact_jsonl(dataset_path, tmp_path, options)
    else:
        raise ValueError(f"Unsupported dataset format: {dataset_path.suffix}")

    tmp_path.replace(output_path)
    if options.output_path is not None and dataset_path != output_path:
        shutil.copystat(dataset_path, output_path, follow_symlinks=False)
    return stats


def _parse_timestamp(value: object) -> datetime | None:
    """Parse timestamps stored as numbers or ISO 8601 strings."""

    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=UTC)
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _collect_events(
    events_path: Path,
) -> tuple[MutableMapping[str, list[dict[str, object]]], list[str]]:
    events_by_request: MutableMapping[str, list[dict[str, object]]] = {}
    order: list[str] = []
    for event in iter_feedback_events(events_path):
        request_id = str(event.get("request_id"))
        if request_id == "None":  # pragma: no cover - defensive guard
            continue
        bucket = events_by_request.get(request_id)
        if bucket is None:
            bucket = []
            events_by_request[request_id] = bucket
            order.append(request_id)
        bucket.append(event)
    return events_by_request, order


def _build_timestamps(events_by_request: MutableMapping[str, list[dict[str, object]]]) -> dict[str, datetime]:
    timestamps: dict[str, datetime] = {}
    for request_id, entries in events_by_request.items():
        first_event = entries[0]
        ts = _parse_timestamp(first_event.get("timestamp")) or _FALLBACK_TIMESTAMP
        timestamps[request_id] = ts
    return timestamps


def _apply_prune_filters(
    request_order: list[str],
    timestamps: dict[str, datetime],
    options: PruneOptions,
    now: datetime,
) -> list[str]:
    selected_ids = list(request_order)

    if options.max_age_days is not None:
        threshold = now - timedelta(days=options.max_age_days)
        selected_ids = [rid for rid in selected_ids if timestamps[rid] >= threshold]

    if options.max_requests is not None and len(selected_ids) > options.max_requests:
        newest_first = sorted(selected_ids, key=timestamps.__getitem__, reverse=True)
        selected_ids = newest_first[: options.max_requests]

    return selected_ids


def _preserve_original_order(order: list[str], selected_ids: Iterable[str]) -> list[str]:
    retained_ids = set(selected_ids)
    return [rid for rid in order if rid in retained_ids]


def _write_retained_events(
    destination: Path,
    retained_order: Iterable[str],
    events_by_request: MutableMapping[str, list[dict[str, object]]],
) -> None:
    tmp_path = destination.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for request_id in retained_order:
            for entry in events_by_request[request_id]:
                handle.write(json.dumps(entry, separators=(",", ":"), ensure_ascii=False))
                handle.write("\n")
    tmp_path.replace(destination)


def _redact_csv(source: Path, destination: Path, options: RedactOptions) -> RedactStats:
    """Redact sensitive columns from a CSV dataset."""

    with source.open("r", encoding="utf-8") as infile, destination.open("w", encoding="utf-8", newline="") as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        total = 0
        redacted = 0
        for row in reader:
            total += 1
            if _redact_csv_row(row, options):
                redacted += 1
            writer.writerow(row)
    return RedactStats(total_rows=total, redacted_rows=redacted)


def _redact_csv_row(row: MutableMapping[str, str], options: RedactOptions) -> bool:
    changed = False
    if options.drop_query and _clear_field(row, "query", ""):
        changed = True
    if options.drop_context and _clear_field(row, "context_json", ""):
        changed = True
    if options.drop_note and _clear_field(row, "feedback_note", ""):
        changed = True
    return changed


def _clear_field(row: MutableMapping[str, str], field: str, replacement: str) -> bool:
    if field not in row:
        return False
    if not row[field]:
        return False
    row[field] = replacement
    return True


def _redact_jsonl(source: Path, destination: Path, options: RedactOptions) -> RedactStats:
    """Redact sensitive fields from JSON lines datasets."""

    total = 0
    redacted = 0
    with source.open("r", encoding="utf-8") as infile, destination.open("w", encoding="utf-8") as outfile:
        for raw in infile:
            line = raw.strip()
            if not line:
                outfile.write("\n")
                continue
            record = json.loads(line)
            if _redact_json_record(record, options):
                redacted += 1
            outfile.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False))
            outfile.write("\n")
            total += 1
    return RedactStats(total_rows=total, redacted_rows=redacted)


def _redact_json_record(record: MutableMapping[str, object], options: RedactOptions) -> bool:
    changed = False
    if options.drop_query and _null_field(record, "query"):
        changed = True
    if options.drop_context and _null_field(record, "context"):
        changed = True
    if options.drop_note and _null_field(record, "feedback_note"):
        changed = True
    return changed


def _null_field(record: MutableMapping[str, object], field: str) -> bool:
    if field not in record:
        return False
    if not record[field]:
        return False
    record[field] = None
    return True


__all__ = [
    "PruneOptions",
    "PruneStats",
    "RedactOptions",
    "RedactStats",
    "prune_feedback_log",
    "redact_dataset",
]
