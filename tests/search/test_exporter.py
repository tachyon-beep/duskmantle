from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

from gateway.search.cli import export_training_data
from gateway.search.exporter import (
    ExportOptions,
    discover_feedback_logs,
    export_feedback_logs,
)


def test_discover_feedback_logs_orders_oldest_first(tmp_path: Path) -> None:
    (tmp_path / "events.log.3").write_text("{}\n", encoding="utf-8")
    (tmp_path / "events.log.1").write_text("{}\n", encoding="utf-8")
    (tmp_path / "events.log").write_text("{}\n", encoding="utf-8")

    logs = discover_feedback_logs(tmp_path, include_rotations=True)
    assert logs == [
        tmp_path / "events.log.3",
        tmp_path / "events.log.1",
        tmp_path / "events.log",
    ]


def test_export_feedback_logs_combines_rotations(tmp_path: Path) -> None:
    log_old = tmp_path / "events.log.2"
    log_new = tmp_path / "events.log"
    log_old.write_text(
        json.dumps(
            {
                "request_id": "req-old",
                "rank": 1,
                "query": "old",
                "result_count": 1,
                "chunk_id": "c1",
                "artifact_path": "old.py",
                "artifact_type": "code",
                "vector_score": 0.1,
                "adjusted_score": 0.2,
                "signals": {
                    "subsystem_affinity": 0.0,
                    "relationship_count": 0,
                    "supporting_bonus": 0.0,
                    "coverage_missing": 0.0,
                },
                "graph_context_present": False,
                "feedback_vote": 0.0,
                "feedback_note": None,
                "context": None,
                "metadata": {
                    "request_id": "req-old",
                    "graph_context_included": False,
                    "warnings": [],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    log_new.write_text(
        json.dumps(
            {
                "request_id": "req-new",
                "rank": 1,
                "query": "new",
                "result_count": 1,
                "chunk_id": "c2",
                "artifact_path": "new.py",
                "artifact_type": "code",
                "vector_score": 0.3,
                "adjusted_score": 0.4,
                "signals": {
                    "subsystem_affinity": 0.0,
                    "relationship_count": 0,
                    "supporting_bonus": 0.0,
                    "coverage_missing": 0.0,
                },
                "graph_context_present": True,
                "feedback_vote": 1.0,
                "feedback_note": "note",
                "context": None,
                "metadata": {
                    "request_id": "req-new",
                    "graph_context_included": True,
                    "warnings": [],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    output = tmp_path / "dataset.csv"
    options = ExportOptions(output_path=output, output_format="csv")
    stats = export_feedback_logs([log_old, log_new], options=options)

    assert stats.total_events == 2
    assert stats.written_rows == 2

    rows = list(csv.DictReader(output.read_text(encoding="utf-8").splitlines()))
    assert rows[0]["request_id"] == "req-old"
    assert rows[1]["request_id"] == "req-new"


def test_export_training_data_includes_rotations(tmp_path: Path) -> None:
    feedback_dir = tmp_path / "feedback"
    datasets_dir = feedback_dir / "datasets"
    feedback_dir.mkdir(parents=True)
    (feedback_dir / "events.log.1").write_text(
        json.dumps(
            {
                "request_id": "req-old",
                "rank": 1,
                "query": "old",
                "result_count": 1,
                "chunk_id": "c1",
                "artifact_path": "old.py",
                "artifact_type": "code",
                "vector_score": 0.1,
                "adjusted_score": 0.2,
                "signals": {
                    "subsystem_affinity": 0.0,
                    "relationship_count": 0,
                    "supporting_bonus": 0.0,
                    "coverage_missing": 0.0,
                },
                "graph_context_present": False,
                "feedback_vote": 0.0,
                "feedback_note": None,
                "context": None,
                "metadata": {
                    "request_id": "req-old",
                    "graph_context_included": False,
                    "warnings": [],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (feedback_dir / "events.log").write_text(
        json.dumps(
            {
                "request_id": "req-new",
                "rank": 1,
                "query": "new",
                "result_count": 1,
                "chunk_id": "c2",
                "artifact_path": "new.py",
                "artifact_type": "code",
                "vector_score": 0.3,
                "adjusted_score": 0.4,
                "signals": {
                    "subsystem_affinity": 0.0,
                    "relationship_count": 0,
                    "supporting_bonus": 0.0,
                    "coverage_missing": 0.0,
                },
                "graph_context_present": True,
                "feedback_vote": 1.0,
                "feedback_note": "note",
                "context": None,
                "metadata": {
                    "request_id": "req-new",
                    "graph_context_included": True,
                    "warnings": [],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    settings = SimpleNamespace(state_path=tmp_path)
    export_training_data(
        output=None,
        fmt="csv",
        require_vote=False,
        limit=None,
        include_rotations=True,
        settings=settings,
    )

    exports = sorted(datasets_dir.glob("training-*.csv"))
    assert exports, "expected export file"
    rows = list(csv.DictReader(exports[-1].read_text(encoding="utf-8").splitlines()))
    assert {row["request_id"] for row in rows} == {"req-old", "req-new"}
