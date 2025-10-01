"""Tests for the search maintenance helpers."""

# pylint: disable=protected-access, wrong-import-position, missing-function-docstring

from __future__ import annotations

import json
import os
import stat
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.modules["sentence_transformers"] = SimpleNamespace(
    SentenceTransformer=type(
        "_StubSentenceTransformer",
        (),
        {
            "__init__": lambda self, model_name, *args, **kwargs: setattr(self, "model_name", model_name),
            "get_sentence_embedding_dimension": lambda self: 8,
            "encode": lambda self, texts, convert_to_tensor=False: [[float(index) for index in range(1, 9)] for _ in texts],
        },
    )
)

from gateway.search import maintenance  # noqa: E402
from gateway.search.maintenance import (  # noqa: E402
    PruneOptions,
    RedactOptions,
    prune_feedback_log,
    redact_dataset,
)


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


def test_prune_feedback_log_by_age(tmp_path: Path) -> None:
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
    missing = tmp_path / "events.log"
    with pytest.raises(FileNotFoundError):
        prune_feedback_log(missing, options=PruneOptions(max_age_days=1))


def test_prune_feedback_log_requires_limit(tmp_path: Path) -> None:
    events_path = tmp_path / "events.log"
    events_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="At least one of max_age_days or max_requests"):
        prune_feedback_log(events_path, options=PruneOptions())


def test_prune_feedback_log_empty_file(tmp_path: Path) -> None:
    events_path = tmp_path / "events.log"
    events_path.write_text("\n\n", encoding="utf-8")

    stats = prune_feedback_log(events_path, options=PruneOptions(max_age_days=30))

    assert stats.total_requests == 0
    assert stats.retained_requests == 0
    assert stats.removed_requests == 0


def test_prune_feedback_log_guard_when_pruning_everything(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
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


def test_redact_dataset_jsonl(tmp_path: Path) -> None:
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


def test_redact_dataset_missing_file(tmp_path: Path) -> None:
    dataset = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError):
        redact_dataset(dataset, options=RedactOptions())


def test_redact_dataset_unsupported_suffix(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.txt"
    dataset.write_text("data", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported dataset format"):
        redact_dataset(dataset, options=RedactOptions())


def test_redact_dataset_output_path_copies_metadata(tmp_path: Path) -> None:
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


def test_clear_and_null_field_helpers() -> None:
    row: dict[str, str] = {}
    assert maintenance._clear_field(row, "query", "") is False
    row["query"] = ""
    assert maintenance._clear_field(row, "query", "") is False
    row["query"] = "secret"
    assert maintenance._clear_field(row, "query", "") is True
    assert row["query"] == ""

    record: dict[str, object] = {}
    assert maintenance._null_field(record, "feedback_note") is False
    record["feedback_note"] = ""
    assert maintenance._null_field(record, "feedback_note") is False
    record["feedback_note"] = "note"
    assert maintenance._null_field(record, "feedback_note") is True
    assert record["feedback_note"] is None


def test_parse_timestamp_numeric_and_empty() -> None:
    assert maintenance._parse_timestamp(None) is None
    timestamp = maintenance._parse_timestamp(1_700_000_000)
    assert timestamp == datetime.fromtimestamp(1_700_000_000, tz=UTC)
