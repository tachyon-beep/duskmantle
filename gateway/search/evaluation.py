from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence

import numpy as np

from gateway.search.dataset import DatasetLoadError, build_feature_matrix, load_dataset_records
from gateway.search.trainer import load_artifact


@dataclass(slots=True)
class EvaluationMetrics:
    mse: float
    r2: float
    ndcg_at_5: float
    ndcg_at_10: float
    spearman: float | None


def evaluate_model(dataset_path: Path, model_path: Path) -> EvaluationMetrics:
    records = load_dataset_records(dataset_path)
    if not records:
        raise DatasetLoadError("Dataset is empty or lacks valid votes")

    model = load_artifact(model_path)
    if not model.feature_names:
        raise ValueError("Model artifact missing feature_names")

    feature_rows, targets, request_ids = build_feature_matrix(records, model.feature_names)
    X = np.asarray(feature_rows, dtype=float)
    y = np.asarray(targets, dtype=float)

    coeffs = np.asarray(model.coefficients, dtype=float)
    if coeffs.shape[0] != X.shape[1]:
        raise ValueError(
            f"Model expects {coeffs.shape[0]} features but dataset provides {X.shape[1]}"
        )
    predictions = X @ coeffs + model.intercept

    mse = float(np.mean((predictions - y) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    if math.isclose(ss_tot, 0.0):
        r2 = 1.0 if math.isclose(mse, 0.0) else 0.0
    else:
        r2 = float(1 - ((predictions - y) @ (predictions - y)) / ss_tot)

    ndcg5 = _mean_ndcg(request_ids, y, predictions, k=5)
    ndcg10 = _mean_ndcg(request_ids, y, predictions, k=10)
    spearman = _spearman_correlation(y, predictions)

    return EvaluationMetrics(mse=mse, r2=r2, ndcg_at_5=ndcg5, ndcg_at_10=ndcg10, spearman=spearman)


def _mean_ndcg(request_ids: Sequence[str], relevance: np.ndarray, scores: np.ndarray, *, k: int) -> float:
    groups: Dict[str, List[int]] = {}
    for idx, rid in enumerate(request_ids):
        groups.setdefault(rid, []).append(idx)

    ndcgs: List[float] = []
    for indices in groups.values():
        if not indices:
            continue
        rel = relevance[indices]
        preds = scores[indices]
        order = np.argsort(-preds)
        dcg = _dcg(rel[order], k)
        ideal = _dcg(np.sort(rel)[::-1], k)
        if ideal == 0:
            continue
        ndcgs.append(dcg / ideal)

    if not ndcgs:
        return 0.0
    return float(mean(ndcgs))


def _dcg(relevances: np.ndarray, k: int) -> float:
    k = min(k, len(relevances))
    if k <= 0:
        return 0.0
    gains = (2 ** relevances[:k] - 1) / np.log2(np.arange(2, k + 2))
    return float(np.sum(gains))


def _spearman_correlation(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    if y_true.size < 2:
        return None
    rank_true = np.argsort(np.argsort(y_true))
    rank_pred = np.argsort(np.argsort(y_pred))
    diff = rank_true - rank_pred
    numerator = 6 * np.sum(diff ** 2)
    denominator = y_true.size * (y_true.size ** 2 - 1)
    if math.isclose(denominator, 0.0):
        return None
    return float(1 - numerator / denominator)


__all__ = ["EvaluationMetrics", "evaluate_model"]
