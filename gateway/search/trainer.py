from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence

import numpy as np

from gateway.search.dataset import DatasetLoadError, build_feature_matrix, load_dataset_records

FEATURE_FIELDS: Sequence[str] = (
    "vector_score",
    "signal_subsystem_affinity",
    "signal_relationship_count",
    "signal_supporting_bonus",
    "signal_coverage_missing",
    "graph_context_present",
    "metadata_graph_context_included",
    "metadata_warnings_count",
)


@dataclass(slots=True)
class TrainingResult:
    weights: list[float]
    intercept: float
    mse: float
    r2: float
    rows: int


@dataclass(slots=True)
class ModelArtifact:
    model_type: str
    created_at: str
    feature_names: list[str]
    coefficients: list[float]
    intercept: float
    metrics: dict[str, float]
    training_rows: int


def train_from_dataset(path: Path) -> ModelArtifact:
    records = load_dataset_records(path)
    if not records:
        raise DatasetLoadError("Dataset is empty or lacks valid votes")

    feature_rows, targets, _ = build_feature_matrix(records, FEATURE_FIELDS)
    X = np.asarray(feature_rows, dtype=float)
    y = np.asarray(targets, dtype=float)
    result = _linear_regression(X, y)

    artifact = ModelArtifact(
        model_type="linear_regression",
        created_at=datetime.now(timezone.utc).isoformat(),
        feature_names=list(FEATURE_FIELDS),
        coefficients=result.weights,
        intercept=result.intercept,
        metrics={"mse": result.mse, "r2": result.r2},
        training_rows=result.rows,
    )
    return artifact


def save_artifact(artifact: ModelArtifact, path: Path) -> None:
    payload = {
        "model_type": artifact.model_type,
        "created_at": artifact.created_at,
        "feature_names": artifact.feature_names,
        "coefficients": artifact.coefficients,
        "intercept": artifact.intercept,
        "metrics": artifact.metrics,
        "training_rows": artifact.training_rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_artifact(path: Path) -> ModelArtifact:
    data = json.loads(path.read_text(encoding="utf-8"))
    return ModelArtifact(
        model_type=data.get("model_type", "linear_regression"),
        created_at=data.get("created_at", ""),
        feature_names=list(data.get("feature_names", [])),
        coefficients=list(data.get("coefficients", [])),
        intercept=float(data.get("intercept", 0.0)),
        metrics=dict(data.get("metrics", {})),
        training_rows=int(data.get("training_rows", 0)),
    )


def _linear_regression(X: np.ndarray, y: np.ndarray) -> TrainingResult:
    n_samples = X.shape[0]
    ones = np.ones((n_samples, 1))
    design = np.hstack([X, ones])
    coeffs, resid, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    weights = coeffs[:-1].tolist()
    intercept = float(coeffs[-1])
    predictions = design @ coeffs
    mse = float(np.mean((predictions - y) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    if math.isclose(ss_tot, 0.0):
        r2 = 1.0 if math.isclose(mse, 0.0) else 0.0
    else:
        r2 = float(1 - ((predictions - y) @ (predictions - y)) / ss_tot)
    return TrainingResult(weights=weights, intercept=intercept, mse=mse, r2=r2, rows=n_samples)


__all__ = [
    "ModelArtifact",
    "TrainingResult",
    "train_from_dataset",
    "save_artifact",
    "load_artifact",
    "DatasetLoadError",
]
