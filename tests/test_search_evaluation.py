from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from gateway.search.cli import evaluate_trained_model
from gateway.search.dataset import DatasetLoadError
from gateway.search.evaluation import evaluate_model


def test_evaluate_model(tmp_path: Path) -> None:
    fixture_dataset = Path("tests/fixtures/search/dataset.csv")
    fixture_model = Path("tests/fixtures/search/model.json")

    metrics = evaluate_model(fixture_dataset, fixture_model)
    assert metrics.mse < 1e-6
    assert math.isclose(metrics.r2, 1.0, rel_tol=1e-6)
    assert 0.0 <= metrics.ndcg_at_5 <= 1.0
    assert metrics.spearman is None or -1.0 <= metrics.spearman <= 1.0


def test_evaluate_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dataset_path = Path("tests/fixtures/search/dataset.csv")
    model_path = Path("tests/fixtures/search/model.json")

    evaluate_trained_model(dataset=dataset_path, model=model_path)
    captured = capsys.readouterr()
    assert "Evaluation metrics" in captured.out


def test_evaluate_model_with_empty_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "empty.csv"
    dataset_path.write_text("request_id,feedback_vote\n", encoding="utf-8")
    model_path = tmp_path / "model.json"
    model_path.write_text(
        json.dumps(
            {
                "model_type": "linear_regression",
                "feature_names": ["vector_score"],
                "coefficients": [1.0],
                "intercept": 0.0,
            }
        ),
        encoding="utf-8",
    )

    try:
        evaluate_model(dataset_path, model_path)
    except DatasetLoadError:
        assert True
    else:  # pragma: no cover
        assert False
