from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from gateway.config.settings import get_settings
from gateway.search.cli import export_training_data, train_model
from gateway.search.exporter import ExportOptions, export_training_dataset
from gateway.search.trainer import train_from_dataset


def _write_events(path: Path, events: list[dict[str, object]]) -> None:
    lines = [json.dumps(event, separators=(",", ":")) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sample_event(request_id: str, vote: float | None) -> dict[str, object]:
    return {
        "request_id": request_id,
        "timestamp": "2024-09-01T12:00:00Z",
        "rank": 1,
        "query": "telemetry",
        "result_count": 1,
        "chunk_id": "chunk::1",
        "artifact_path": "src/module.py",
        "artifact_type": "code",
        "subsystem": "core",
        "vector_score": 0.8,
        "adjusted_score": 0.95,
        "signals": {
            "subsystem_affinity": 1.0,
            "relationship_count": 3,
            "supporting_bonus": 0.3,
            "coverage_missing": 0.0,
        },
        "graph_context_present": True,
        "feedback_vote": vote,
        "feedback_note": "useful" if vote is not None else None,
        "metadata": {
            "request_id": request_id,
            "graph_context_included": True,
            "warnings": [],
        },
    }


def test_export_training_dataset_csv(tmp_path: Path) -> None:
    events_path = tmp_path / "events.log"
    _write_events(events_path, [_sample_event("req-1", 4.0), _sample_event("req-2", None)])

    output_path = tmp_path / "dataset.csv"
    stats = export_training_dataset(
        events_path,
        options=ExportOptions(output_path=output_path, output_format="csv", require_vote=False, limit=None),
    )

    assert stats.total_events == 2
    assert stats.written_rows == 2
    assert output_path.exists()

    rows = list(csv.DictReader(output_path.open("r", encoding="utf-8")))
    assert len(rows) == 2
    assert rows[0]["feedback_vote"] == "4.0"
    assert rows[0]["signal_relationship_count"] == "3"


def test_export_training_data_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    feedback_dir = tmp_path / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    events_path = feedback_dir / "events.log"
    _write_events(events_path, [_sample_event("req-3", 5.0), _sample_event("req-4", None)])

    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    get_settings.cache_clear()

    output_path = tmp_path / "out.jsonl"
    export_training_data(
        output=output_path,
        fmt="jsonl",
        require_vote=True,
        limit=None,
    )

    assert output_path.exists()
    lines = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 1
    assert lines[0]["feedback_vote"] == 5.0
    assert lines[0]["metadata_request_id"] == "req-3"


def test_train_model_from_dataset(tmp_path: Path) -> None:
    events_path = tmp_path / "events.log"
    _write_events(
        events_path,
        [
            _sample_event("req-a", 5.0),
            _sample_event("req-b", 3.0),
            _sample_event("req-c", 4.0),
        ],
    )

    dataset_path = tmp_path / "dataset.csv"
    export_training_dataset(
        events_path,
        options=ExportOptions(output_path=dataset_path, output_format="csv", require_vote=True, limit=None),
    )

    artifact = train_from_dataset(dataset_path)
    assert artifact.training_rows == 3
    assert len(artifact.coefficients) > 0
    assert artifact.metrics["mse"] >= 0


def test_train_model_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    feedback_dir = tmp_path / "feedback"
    datasets_dir = feedback_dir / "datasets"
    models_dir = feedback_dir / "models"
    datasets_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = datasets_dir / "training.csv"
    events = [_sample_event("req-cli", 4.0), _sample_event("req-cli-2", 5.0)]
    events_path = tmp_path / "events.log"
    _write_events(events_path, events)
    export_training_dataset(
        events_path,
        options=ExportOptions(output_path=dataset_path, output_format="csv", require_vote=True, limit=None),
    )

    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    get_settings.cache_clear()

    output_path = tmp_path / "model.json"
    train_model(dataset=dataset_path, output=output_path, settings=get_settings())

    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["model_type"] == "linear_regression"
    assert data["training_rows"] == 2
