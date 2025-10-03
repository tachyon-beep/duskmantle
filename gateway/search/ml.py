"""Machine-learning scoring helpers for search results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gateway.search.trainer import ModelArtifact


@dataclass(slots=True)
class ModelScore:
    """Container for ML score and per-feature contributions."""

    score: float
    contributions: dict[str, float]


class ModelScorer:
    """Apply linear model artifacts to enrich search scoring."""

    def __init__(self, artifact: ModelArtifact | None) -> None:
        self._artifact = artifact
        if artifact is not None:
            self._feature_names = list(getattr(artifact, "feature_names", []))
            self._coefficients = list(getattr(artifact, "coefficients", []))
            self._intercept = float(getattr(artifact, "intercept", 0.0))
        else:
            self._feature_names = []
            self._coefficients = []
            self._intercept = 0.0

    @property
    def available(self) -> bool:
        return self._artifact is not None

    @property
    def intercept(self) -> float:
        return self._intercept

    def score(
        self,
        *,
        scoring: dict[str, Any],
        graph_context: dict[str, Any] | None,
        graph_context_included: bool,
        warnings_count: int,
    ) -> ModelScore:
        features = self._build_features(
            scoring=scoring,
            graph_context=graph_context,
            graph_context_included=graph_context_included,
            warnings_count=warnings_count,
        )
        model_score, contributions = self._apply(features)
        return ModelScore(score=model_score, contributions=contributions)

    def _build_features(
        self,
        *,
        scoring: dict[str, Any],
        graph_context: dict[str, Any] | None,
        graph_context_included: bool,
        warnings_count: int,
    ) -> dict[str, float]:
        signals = scoring.get("signals", {})
        return {
            "vector_score": float(scoring.get("vector_score", 0.0) or 0.0),
            "lexical_score": float(scoring.get("lexical_score", 0.0) or 0.0),
            "weighted_vector_score": float(scoring.get("weighted_vector_score", scoring.get("vector_score", 0.0) or 0.0)),
            "weighted_lexical_score": float(scoring.get("weighted_lexical_score", scoring.get("lexical_score", 0.0) or 0.0)),
            "signal_subsystem_affinity": float(signals.get("subsystem_affinity", 0.0) or 0.0),
            "signal_relationship_count": float(signals.get("relationship_count", 0.0) or 0.0),
            "signal_supporting_bonus": float(signals.get("supporting_bonus", 0.0) or 0.0),
            "signal_coverage_missing": float(signals.get("coverage_missing", 0.0) or 0.0),
            "signal_coverage_ratio": float(signals.get("coverage_ratio", 0.0) or 0.0),
            "signal_criticality_score": float(signals.get("criticality_score", 0.0) or 0.0),
            "signal_path_depth": float(signals.get("path_depth", 0.0) or 0.0),
            "graph_context_present": 1.0 if graph_context else 0.0,
            "metadata_graph_context_included": 1.0 if graph_context_included else 0.0,
            "metadata_warnings_count": float(warnings_count),
        }

    def _apply(self, features: dict[str, float]) -> tuple[float, dict[str, float]]:
        if not self._feature_names:
            raise ValueError("Model artifact missing feature names")
        missing = [name for name in self._feature_names if name not in features]
        if missing:
            raise ValueError(f"Missing features for model scoring: {missing}")
        contributions: dict[str, float] = {}
        score = self._intercept
        for coeff, name in zip(self._coefficients, self._feature_names, strict=False):
            value = features[name]
            contrib = coeff * value
            contributions[name] = contrib
            score += contrib
        return score, contributions


__all__ = ["ModelScorer", "ModelScore"]
