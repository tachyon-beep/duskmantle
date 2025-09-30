from __future__ import annotations

import json
import logging
import shutil
from collections.abc import MutableMapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gateway.search.exporter import iter_feedback_events

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PruneOptions:
    max_age_days: int | None = None
    max_requests: int | None = None
    output_path: Path | None = None
    current_time: datetime | None = None


@dataclass(slots=True)
class PruneStats:
    total_requests: int
    retained_requests: int
    removed_requests: int


@dataclass(slots=True)
class RedactOptions:
    output_path: Path | None = None
    drop_query: bool = False
    drop_context: bool = False
    drop_note: bool = False


@dataclass(slots=True)
class RedactStats:
    total_rows: int
    redacted_rows: int


def prune_feedback_log(events_path: Path, *, options: PruneOptions) -> PruneStats:
    if not events_path.exists():
        raise FileNotFoundError(f"Feedback log not found: {events_path}")
    if options.max_age_days is None and options.max_requests is None:
        raise ValueError("At least one of max_age_days or max_requests must be provided")

    events_by_request: MutableMapping[str, list[dict[str, object]]] = {}
    order: list[str] = []
    for event in iter_feedback_events(events_path):
        rid = str(event.get("request_id"))
        if rid == "None":  # pragma: no cover - defensive guard
            continue
        if rid not in events_by_request:
            events_by_request[rid] = []
            order.append(rid)
        events_by_request[rid].append(event)

    timestamps: dict[str, datetime] = {}
    for rid, entries in events_by_request.items():
        first = entries[0]
        ts = _parse_timestamp(first.get("timestamp"))
        if ts is None:
            ts = datetime.fromordinal(1).replace(tzinfo=UTC)
        timestamps[rid] = ts

    total_requests = len(events_by_request)
    if total_requests == 0:
        return PruneStats(total_requests=0, retained_requests=0, removed_requests=0)

    now = options.current_time or datetime.now(UTC)
    selected_ids = list(order)

    if options.max_age_days is not None:
        threshold = now - timedelta(days=options.max_age_days)
        selected_ids = [rid for rid in selected_ids if timestamps[rid] >= threshold]

    if options.max_requests is not None and len(selected_ids) > options.max_requests:
        # Keep newest requests by timestamp
        sorted_ids = sorted(selected_ids, key=lambda rid: timestamps[rid], reverse=True)
        selected_ids = sorted_ids[: options.max_requests]

    # Preserve original ordering for retained entries
    retained_set = set(selected_ids)
    retained_order = [rid for rid in order if rid in retained_set]

    if not retained_order and total_requests > 0:
        logger.warning("Prune operation would remove all feedback events; skipping")
        return PruneStats(total_requests=total_requests, retained_requests=total_requests, removed_requests=0)

    destination = options.output_path or events_path
    tmp_path = destination.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for rid in retained_order:
            request_entries: list[dict[str, object]] = events_by_request[rid]
            for entry in request_entries:
                handle.write(json.dumps(entry, separators=(",", ":"), ensure_ascii=False))
                handle.write("\n")
    tmp_path.replace(destination)

    removed = total_requests - len(retained_order)
    return PruneStats(total_requests=total_requests, retained_requests=len(retained_order), removed_requests=removed)


def redact_dataset(dataset_path: Path, *, options: RedactOptions) -> RedactStats:
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


def _redact_csv(source: Path, destination: Path, options: RedactOptions) -> RedactStats:
    import csv

    with source.open("r", encoding="utf-8") as infile, destination.open("w", encoding="utf-8", newline="") as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        total = 0
        redacted = 0
        for row in reader:
            total += 1
            changed = False
            if options.drop_query and "query" in row:
                if row["query"]:
                    row["query"] = ""
                    changed = True
            if options.drop_context and "context_json" in row:
                if row["context_json"]:
                    row["context_json"] = ""
                    changed = True
            if options.drop_note and "feedback_note" in row:
                if row["feedback_note"]:
                    row["feedback_note"] = ""
                    changed = True
            if changed:
                redacted += 1
            writer.writerow(row)
    return RedactStats(total_rows=total, redacted_rows=redacted)


def _redact_jsonl(source: Path, destination: Path, options: RedactOptions) -> RedactStats:
    total = 0
    redacted = 0
    with source.open("r", encoding="utf-8") as infile, destination.open("w", encoding="utf-8") as outfile:
        for raw in infile:
            line = raw.strip()
            if not line:
                outfile.write("\n")
                continue
            record = json.loads(line)
            changed = False
            if options.drop_query and "query" in record and record["query"]:
                record["query"] = None
                changed = True
            if options.drop_context and "context" in record and record["context"]:
                record["context"] = None
                changed = True
            if options.drop_note and "feedback_note" in record and record["feedback_note"]:
                record["feedback_note"] = None
                changed = True
            outfile.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False))
            outfile.write("\n")
            total += 1
            if changed:
                redacted += 1
    return RedactStats(total_rows=total, redacted_rows=redacted)


__all__ = [
    "PruneOptions",
    "PruneStats",
    "RedactOptions",
    "RedactStats",
    "prune_feedback_log",
    "redact_dataset",
]
