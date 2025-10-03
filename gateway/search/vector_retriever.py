"""Utilities for running vector retrieval against Qdrant."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence

from qdrant_client import QdrantClient
from qdrant_client.http.models import ScoredPoint, SearchParams

from gateway.ingest.embedding import Embedder

logger = logging.getLogger(__name__)


class VectorRetrievalError(RuntimeError):
    """Raised when vector search fails before results are returned."""


class VectorRetriever:
    """Encode a query and execute Qdrant search with optional tuning."""

    def __init__(
        self,
        *,
        embedder: Embedder,
        qdrant_client: QdrantClient,
        collection_name: str,
        hnsw_ef_search: int | None = None,
        failure_callback: Callable[[Exception], None] | None = None,
    ) -> None:
        self._embedder = embedder
        self._qdrant_client = qdrant_client
        self._collection_name = collection_name
        self._failure_callback = failure_callback
        self._hnsw_ef_search = int(hnsw_ef_search) if hnsw_ef_search and hnsw_ef_search > 0 else None

    def search(
        self,
        *,
        query: str,
        limit: int,
        request_id: str | None = None,
    ) -> Sequence[ScoredPoint]:
        """Return scored points for a given query and limit."""

        try:
            vector = self._embedder.encode([query])[0]
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                "Failed to encode search query: %s",
                exc,
                extra={"component": "search", "event": "vector_encode_error", "request_id": request_id},
            )
            if self._failure_callback is not None:
                self._failure_callback(exc)
            raise VectorRetrievalError("Failed to encode search query") from exc

        search_params = (
            SearchParams(hnsw_ef=self._hnsw_ef_search) if self._hnsw_ef_search is not None else None
        )

        try:
            hits = self._qdrant_client.search(
                collection_name=self._collection_name,
                query_vector=vector,
                with_payload=True,
                limit=limit,
                search_params=search_params,
            )
        except Exception as exc:  # pragma: no cover - network errors handled upstream
            if self._failure_callback is not None:
                self._failure_callback(exc)
            logger.error(
                "Search query failed: %s",
                exc,
                extra={"component": "search", "event": "vector_search_error", "request_id": request_id},
            )
            raise VectorRetrievalError("Vector search failed") from exc
        return hits


__all__ = ["VectorRetriever", "VectorRetrievalError"]
