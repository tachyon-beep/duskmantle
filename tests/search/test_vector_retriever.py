from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from gateway.search.vector_retriever import VectorRetrievalError, VectorRetriever


class DummyEmbedder:
    def __init__(self, *, raise_on_encode: Exception | None = None) -> None:
        self._raise = raise_on_encode
        self.calls: Sequence[str] = []

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if self._raise is not None:
            raise self._raise
        self.calls = list(texts)
        return [[0.1, 0.2, 0.3] for _ in texts]


class DummyQdrantClient:
    def __init__(self, *, raise_on_search: Exception | None = None) -> None:
        self._raise = raise_on_search
        self.last_kwargs: dict[str, Any] | None = None
        self.points = [object()]

    def search(self, **kwargs: object) -> list[object]:
        if self._raise is not None:
            raise self._raise
        self.last_kwargs = dict(kwargs)
        return list(self.points)


def test_vector_retriever_returns_hits() -> None:
    client = DummyQdrantClient()
    retriever = VectorRetriever(
        embedder=DummyEmbedder(),
        qdrant_client=client,  # type: ignore[arg-type]
        collection_name="collection",
        hnsw_ef_search=128,
    )

    hits = retriever.search(query="foo", limit=5)

    assert hits == client.points
    assert client.last_kwargs is not None
    assert client.last_kwargs["collection_name"] == "collection"
    assert client.last_kwargs["limit"] == 5
    params = client.last_kwargs.get("search_params")
    assert getattr(params, "hnsw_ef", None) == 128


def test_vector_retriever_failure_calls_callback() -> None:
    sentinel = RuntimeError("boom")
    callback_called: dict[str, Exception] = {}

    def failure_callback(exc: Exception) -> None:
        callback_called["exc"] = exc

    retriever = VectorRetriever(
        embedder=DummyEmbedder(),
        qdrant_client=DummyQdrantClient(raise_on_search=sentinel),  # type: ignore[arg-type]
        collection_name="collection",
        failure_callback=failure_callback,
    )

    with pytest.raises(VectorRetrievalError):
        retriever.search(query="foo", limit=3, request_id="req-1")

    assert callback_called["exc"] is sentinel


def test_vector_retriever_encode_failure_propagates() -> None:
    sentinel = RuntimeError("encode-fail")
    retriever = VectorRetriever(
        embedder=DummyEmbedder(raise_on_encode=sentinel),
        qdrant_client=DummyQdrantClient(),  # type: ignore[arg-type]
        collection_name="collection",
    )

    with pytest.raises(VectorRetrievalError):
        retriever.search(query="foo", limit=1)
