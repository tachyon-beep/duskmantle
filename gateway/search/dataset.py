from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from gateway.search.exporter import FIELDNAMES

TARGET_FIELD = "feedback_vote"


class DatasetLoadError(RuntimeError):
    """Raised when a dataset cannot be parsed."""


def load_dataset_records(path: Path) -> list[Mapping[str, object]]:
    if not path.exists():
        raise DatasetLoadError(f"Dataset not found: {path}")

    rows: list[Mapping[str, object]] = []
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            missing = set(FIELDNAMES) - set(reader.fieldnames or [])
            if missing:
                raise DatasetLoadError(f"Dataset missing expected columns: {sorted(missing)}")
            for record in reader:
                if _parse_float(record.get(TARGET_FIELD)) is None:
                    continue
                rows.append(record)
    elif suffix in {".jsonl", ".json"}:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:  # pragma: no cover - dataset validation
                    raise DatasetLoadError(f"Invalid JSON on line {line_number}: {exc}") from exc
                if _parse_float(record.get(TARGET_FIELD)) is None:
                    continue
                rows.append(record)
    else:
        raise DatasetLoadError(f"Unsupported dataset format: {path.suffix}")

    return rows


def build_feature_matrix(
    records: Iterable[Mapping[str, object]],
    feature_names: Sequence[str],
) -> tuple[list[list[float]], list[float], list[str]]:
    features: list[list[float]] = []
    targets: list[float] = []
    request_ids: list[str] = []

    for record in records:
        vote = _parse_float(record.get(TARGET_FIELD))
        if vote is None:
            continue
        row_features: list[float] = []
        for name in feature_names:
            value = record.get(name)
            row_features.append(_parse_float(value) or 0.0)
        features.append(row_features)
        targets.append(vote)
        request_ids.append(str(record.get("request_id")))

    if not features:
        raise DatasetLoadError("No rows contained valid features/votes")
    return features, targets, request_ids


def _parse_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "DatasetLoadError",
    "load_dataset_records",
    "build_feature_matrix",
    "TARGET_FIELD",
]
