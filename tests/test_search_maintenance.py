"""Tests for the search maintenance helpers."""

from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from gateway.search.maintenance import PruneOptions, RedactOptions, prune_feedback_log, redact_dataset


def _write_events(path: Path, requests: list[tuple[str, datetime, list[dict[str, object]]]]) -> None:
    """Write JSON lines representing feedback events for the supplied requests."""

    lines: list[str] = []
    for request_id, timestamp, rows in requests:
        default_ts = timestamp.isoformat()
        for row in rows:
            record = {
                "request_id": request_id,
                "timestamp": default_ts,
                "rank": row.get("rank", 1),
                "query": row.get("query", "test"),
            }
            record.update(row)
            lines.append(json.dumps(record, separators=(",", ":")))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_prune_feedback_log_parses_various_timestamp_formats(tmp_path: Path) -> None:
    """Ensure prune handles numeric, Z-suffixed, and missing timestamps."""

    now = datetime(2024, 9, 1, 12, 0, tzinfo=UTC)
    events_path = tmp_path / "events.log"
    _write_events(
        events_path,
        [
            (
                "req-int",
                now,
                [
                    {
                        "rank": 1,
                        "query": "numeric",
                        "timestamp": 1_700_000_000,
                    }
                ],
            ),
            (
                "req-z",
                now,
                [
                    {
                        "rank": 1,
                        "query": "zulu",
                        "timestamp": "2024-08-01T00:00:00Z",
                    }
                ],
            ),
            (
                "req-none",
                now,
                [
                    {
                        "rank": 1,
                        "query": "none",
                        "timestamp": None,
                    }
                ],
            ),
        ],
    )

    stats = prune_feedback_log(
        events_path,
        options=PruneOptions(max_requests=5, current_time=now),
    )

    assert stats.total_requests == 3
    ids = [json.loads(line)["request_id"] for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    assert ids == ["req-int", "req-z", "req-none"]


def test_prune_feedback_log_by_age(tmp_path: Path) -> None:
    """Retains only entries newer than the configured age threshold."""

    now = datetime(2024, 9, 1, 12, 0, tzinfo=UTC)
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


def test_prune_feedback_log_missing_file(tmp_path: Path) -> None:
    """Raises if the feedback log file is absent."""

    missing = tmp_path / "events.log"
    with pytest.raises(FileNotFoundError):
        prune_feedback_log(missing, options=PruneOptions(max_age_days=1))


def test_prune_feedback_log_requires_limit(tmp_path: Path) -> None:
    """Rejects calls without an age or request limit configured."""

    events_path = tmp_path / "events.log"
    events_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="At least one of max_age_days or max_requests"):
        prune_feedback_log(events_path, options=PruneOptions())


def test_prune_feedback_log_empty_file(tmp_path: Path) -> None:
    """Returns zeroed stats when the log contains no events."""

    events_path = tmp_path / "events.log"
    events_path.write_text("\n\n", encoding="utf-8")

    stats = prune_feedback_log(events_path, options=PruneOptions(max_age_days=30))

    assert stats.total_requests == 0
    assert stats.retained_requests == 0
    assert stats.removed_requests == 0


def test_prune_feedback_log_guard_when_pruning_everything(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Leaves the log intact when filters would drop every request."""

    caplog.set_level("WARNING")
    now = datetime(2024, 9, 1, 12, 0, tzinfo=UTC)
    events_path = tmp_path / "events.log"
    _write_events(
        events_path,
        [
            (
                "req-old",
                now - timedelta(days=40),
                [{"rank": 1, "query": "old", "timestamp": "2024-07-01T00:00:00Z"}],
            )
        ],
    )

    stats = prune_feedback_log(
        events_path,
        options=PruneOptions(max_age_days=1, current_time=now),
    )

    assert stats.total_requests == 1
    assert stats.retained_requests == 1
    assert stats.removed_requests == 0
    assert "would remove all feedback events" in caplog.text
    assert "req-old" in events_path.read_text(encoding="utf-8")


def test_prune_feedback_log_max_requests_prefers_newest(tmp_path: Path) -> None:
    """Keeps only the newest requests when enforcing a max count."""

    now = datetime(2024, 9, 1, 12, 0, tzinfo=UTC)
    older = now - timedelta(days=10)
    middle = now - timedelta(days=5)
    newest = now - timedelta(days=1)

    events_path = tmp_path / "events.log"
    _write_events(
        events_path,
        [
            (
                "req-older",
                older,
                [
                    {
                        "rank": 1,
                        "query": "older",
                        "timestamp": "not-a-timestamp",
                    }
                ],
            ),
            ("req-middle", middle, [{"rank": 1, "query": "middle"}]),
            ("req-newest", newest, [{"rank": 1, "query": "newest"}]),
        ],
    )

    stats = prune_feedback_log(
        events_path,
        options=PruneOptions(max_requests=2, current_time=now),
    )

    assert stats.total_requests == 3
    assert stats.retained_requests == 2
    contents = [json.loads(line)["request_id"] for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    assert contents == ["req-middle", "req-newest"]


def test_redact_dataset_csv(tmp_path: Path) -> None:
    """Redacts populated CSV fields for queries, contexts, and notes."""

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


def test_redact_dataset_csv_handles_missing_and_blank_fields(tmp_path: Path) -> None:
    """Leaves missing or blank CSV fields untouched while redacting non-empty ones."""

    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        "request_id,context_json\n" "req-keep,\n" 'req-redact,{"task":"deep dive"}\n',
        encoding="utf-8",
    )

    stats = redact_dataset(
        dataset,
        options=RedactOptions(drop_query=True, drop_context=True, drop_note=True),
    )

    assert stats.redacted_rows == 1
    rows = dataset.read_text(encoding="utf-8").splitlines()
    assert rows[1].endswith(",")
    assert rows[2].endswith(",")


def test_redact_dataset_jsonl(tmp_path: Path) -> None:
    """Redacts JSONL query and context fields when toggled."""

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


def test_redact_dataset_jsonl_handles_missing_and_blank_fields(tmp_path: Path) -> None:
    """Leaves absent or empty JSONL fields untouched while redacting populated ones."""

    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        json.dumps({"request_id": "r1"}, separators=(",", ":"))
        + "\n"
        + json.dumps({"request_id": "r2", "feedback_note": ""}, separators=(",", ":"))
        + "\n"
        + json.dumps({"request_id": "r3", "feedback_note": "note"}, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )

    stats = redact_dataset(
        dataset,
        options=RedactOptions(drop_note=True),
    )

    assert stats.redacted_rows == 1
    records = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line]
    assert "feedback_note" not in records[0]
    assert records[1]["feedback_note"] == ""
    assert records[2]["feedback_note"] is None


def test_redact_dataset_missing_file(tmp_path: Path) -> None:
    """Raises if the target dataset file is absent."""

    dataset = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError):
        redact_dataset(dataset, options=RedactOptions())


def test_redact_dataset_unsupported_suffix(tmp_path: Path) -> None:
    """Rejects unsupported dataset extensions."""

    dataset = tmp_path / "dataset.txt"
    dataset.write_text("data", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported dataset format"):
        redact_dataset(dataset, options=RedactOptions())


def test_redact_dataset_output_path_copies_metadata(tmp_path: Path) -> None:
    """Preserves metadata when writing to an alternate output path."""

    dataset = tmp_path / "dataset.csv"
    dataset.write_text("request_id,query\nreq-1,secret\n", encoding="utf-8")
    os.utime(dataset, (1_700_000_000, 1_700_000_100))
    os.chmod(dataset, stat.S_IRUSR | stat.S_IWUSR)

    destination = tmp_path / "redacted.csv"
    stats = redact_dataset(
        dataset,
        options=RedactOptions(output_path=destination, drop_query=True),
    )

    assert stats.redacted_rows == 1
    assert dataset.read_text(encoding="utf-8").strip().endswith("secret")
    assert "secret" not in destination.read_text(encoding="utf-8")
    src_stat = dataset.stat()
    dst_stat = destination.stat()
    assert int(dst_stat.st_mtime) == int(src_stat.st_mtime)
    assert stat.S_IMODE(dst_stat.st_mode) == stat.S_IMODE(src_stat.st_mode)


def test_redact_dataset_jsonl_handles_blank_lines(tmp_path: Path) -> None:
    """Preserves blank lines in JSONL datasets while redacting content."""

    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        "\n" + json.dumps({"request_id": "r1", "query": "search", "feedback_note": "note"}) + "\n",
        encoding="utf-8",
    )

    stats = redact_dataset(
        dataset,
        options=RedactOptions(drop_query=True, drop_note=True),
    )

    assert stats.total_rows == 1
    data = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line]
    assert data[0]["query"] is None
    assert data[0]["feedback_note"] is None
