from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gateway.search.maintenance import PruneOptions, RedactOptions, prune_feedback_log, redact_dataset


def _write_events(path: Path, requests: list[tuple[str, datetime, list[dict[str, object]]]]) -> None:
    lines = []
    for request_id, timestamp, rows in requests:
        ts = timestamp.isoformat()
        for row in rows:
            record = {
                "request_id": request_id,
                "timestamp": ts,
                "rank": row.get("rank", 1),
                "query": row.get("query", "test"),
            }
            record.update(row)
            lines.append(json.dumps(record, separators=(",", ":")))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_prune_feedback_log_by_age(tmp_path):
    now = datetime(2024, 9, 1, 12, 0, tzinfo=timezone.utc)
    older = now - timedelta(days=40)
    recent = now - timedelta(days=5)

    events_path = tmp_path / "events.log"
    _write_events(
        events_path,
        [
            ("req-old", older, [{"rank": 1, "query": "old"}]),
            ("req-new", recent, [{"rank": 1, "query": "new"}]),
        ],
    )

    stats = prune_feedback_log(
        events_path,
        options=PruneOptions(max_age_days=30, current_time=now),
    )

    assert stats.total_requests == 2
    assert stats.retained_requests == 1
    contents = events_path.read_text(encoding="utf-8")
    assert "req-old" not in contents
    assert "req-new" in contents


def test_redact_dataset_csv(tmp_path):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        'request_id,query,context_json,feedback_note\nreq-1,search term,{"task":"deep dive"},useful\n',
        encoding="utf-8",
    )

    stats = redact_dataset(
        dataset,
        options=RedactOptions(drop_query=True, drop_context=True, drop_note=True),
    )

    assert stats.redacted_rows == 1
    text = dataset.read_text(encoding="utf-8")
    assert "search term" not in text
    assert "deep dive" not in text
    assert "useful" not in text


def test_redact_dataset_jsonl(tmp_path):
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "request_id": "r1",
                "query": "search term",
                "context": {"task": "deep dive"},
                "feedback_note": "helpful",
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    stats = redact_dataset(
        dataset,
        options=RedactOptions(drop_query=True, drop_context=True),
    )

    assert stats.redacted_rows == 1
    data = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line]
    assert data[0]["query"] is None
    assert data[0]["context"] is None
    assert data[0]["feedback_note"] == "helpful"
