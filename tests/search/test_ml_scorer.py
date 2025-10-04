from __future__ import annotations

import pytest

from gateway.search.ml import ModelScorer
from gateway.search.trainer import ModelArtifact


def _artifact() -> ModelArtifact:
    return ModelArtifact(
        model_type="linear_regression",
        created_at="",
        feature_names=[
            "vector_score",
            "lexical_score",
            "weighted_vector_score",
            "weighted_lexical_score",
        ],
        coefficients=[0.5, 0.1, 0.0, 0.0],
        intercept=0.2,
        metrics={},
        training_rows=10,
    )


def test_model_scorer_produces_contributions() -> None:
    scorer = ModelScorer(_artifact())
    scoring = {
        "vector_score": 0.8,
        "lexical_score": 0.3,
        "weighted_vector_score": 0.8,
        "weighted_lexical_score": 0.3,
        "signals": {},
    }

    result = scorer.score(
        scoring=scoring,
        graph_context=None,
        graph_context_included=False,
        warnings_count=0,
    )

    assert pytest.approx(result.score) == 0.2 + 0.5 * 0.8 + 0.1 * 0.3
    assert "vector_score" in result.contributions
    assert "lexical_score" in result.contributions


def test_model_scorer_handles_missing_features_with_defaults() -> None:
    scorer = ModelScorer(_artifact())
    scoring = {"vector_score": 0.5}

    result = scorer.score(
        scoring=scoring,
        graph_context=None,
        graph_context_included=False,
        warnings_count=0,
    )

    assert result.score == pytest.approx(0.2 + 0.5 * 0.5)
