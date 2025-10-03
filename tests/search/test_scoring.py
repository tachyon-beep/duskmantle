from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from gateway.search.models import SearchWeights
from gateway.search.scoring import HeuristicScorer


def test_heuristic_scorer_applies_graph_signals() -> None:
    scorer = HeuristicScorer(
        weights=SearchWeights(),
        vector_weight=0.8,
        lexical_weight=0.2,
    )

    payload = {
        "chunk_id": "foo::0",
        "path": "src/foo.py",
        "artifact_type": "code",
        "subsystem": "core",
        "text": "Core handler implementation",
        "coverage_missing": False,
        "coverage_ratio": 0.9,
        "subsystem_criticality": "high",
        "git_timestamp": int(datetime.now(UTC).timestamp()),
    }
    chunk = scorer.build_chunk(payload, 0.85)
    lexical = scorer.lexical_score("core handler", chunk)
    scoring = scorer.base_scoring(vector_score=0.85, lexical_score=lexical)

    graph_context = {
        "relationships": [
            {"type": "BELONGS_TO", "target": {"properties": {"name": "core"}}},
            {"type": "DESCRIBES", "target": {"id": "DesignDoc:docs/core.md"}},
        ],
        "related_artifacts": [{"id": "DesignDoc:docs/core.md"}],
        "primary_node": {"properties": {"criticality": "high"}},
    }

    scoring = scorer.apply_graph_scoring(
        base_scoring=scoring,
        vector_score=0.85,
        lexical_score=lexical,
        query_tokens={"core", "handler"},
        chunk=chunk,
        graph_context=graph_context,
    )

    assert scoring["adjusted_score"] > scoring["weighted_vector_score"]
    signals = scoring["signals"]
    assert signals["subsystem_affinity"] > 0
    assert signals["relationship_count"] >= 1
    assert signals["supporting_bonus"] > 0

    scoring = scorer.populate_additional_signals(
        scoring=scoring,
        chunk=chunk,
        graph_context=graph_context,
        path_depth=2.0,
        freshness_days=1.0,
    )
    assert "path_depth" in scoring["signals"]
    assert "criticality_score" in scoring["signals"]


def test_compute_freshness_days_prefers_chunk_timestamp() -> None:
    scorer = HeuristicScorer(
        weights=SearchWeights(),
        vector_weight=1.0,
        lexical_weight=0.0,
    )
    now = datetime.now(UTC)
    chunk = {
        "git_timestamp": int((now - timedelta(days=3)).timestamp()),
        "updated_at": None,
    }
    freshness = scorer.compute_freshness_days(chunk, graph_context=None)
    assert freshness is not None
    assert freshness == pytest.approx(3.0, rel=0.1)
