from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from gateway.search.feedback import SearchFeedbackStore
from gateway.search.service import SearchResponse, SearchResult
from gateway.observability.metrics import (
    SEARCH_FEEDBACK_LOG_BYTES,
    SEARCH_FEEDBACK_ROTATIONS_TOTAL,
)


def _make_response(query: str, note: str) -> SearchResponse:
    result = SearchResult(
        chunk={
            "chunk_id": "doc::0",
            "artifact_path": "docs/example.md",
            "artifact_type": "doc",
            "subsystem": "knowledge",
            "text": note,
            "score": 0.9,
        },
        graph_context=None,
        scoring={
            "vector_score": 0.9,
            "adjusted_score": 0.95,
            "signals": {},
        },
    )
    return SearchResponse(
        query=query,
        results=[result],
        metadata={
            "result_count": 1,
            "graph_context_included": False,
            "warnings": [],
        },
    )


def test_feedback_store_writes_entries(tmp_path: Path) -> None:
    store = SearchFeedbackStore(tmp_path, max_bytes=1024 * 1024, max_files=3)
    response = _make_response("deployment", "note")

    store.record(response=response, feedback=None, context=None, request_id="req-1")

    payload = (tmp_path / "events.log").read_text(encoding="utf-8")
    assert "deployment" in payload
    assert SEARCH_FEEDBACK_LOG_BYTES._value.get() == pytest.approx((tmp_path / "events.log").stat().st_size)


def test_feedback_store_rotates_when_threshold_exceeded(tmp_path: Path) -> None:
    max_bytes = 600
    store = SearchFeedbackStore(tmp_path, max_bytes=max_bytes, max_files=2)
    response = _make_response("first", "a" * 400)

    rotations_before = SEARCH_FEEDBACK_ROTATIONS_TOTAL._value.get()

    store.record(response=response, feedback=None, context=None, request_id="req-1")
    store.record(response=response, feedback=None, context=None, request_id="req-2")

    rotated_path = tmp_path / "events.log.1"
    assert rotated_path.exists()
    assert SEARCH_FEEDBACK_ROTATIONS_TOTAL._value.get() >= rotations_before + 1
    assert (tmp_path / "events.log").stat().st_size <= max_bytes
