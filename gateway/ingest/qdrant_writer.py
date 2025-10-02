"""Helpers for writing chunk embeddings into Qdrant collections."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Iterable

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from gateway.ingest.artifacts import ChunkEmbedding

logger = logging.getLogger(__name__)


class QdrantWriter:
    """Lightweight adapter around the Qdrant client."""

    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        """Initialise the writer with a target collection."""
        self.client = client
        self.collection_name = collection_name

    def ensure_collection(
        self,
        vector_size: int,
        *,
        retries: int = 3,
        retry_backoff: float = 0.5,
    ) -> None:
        """Ensure the collection exists without destructive recreation.

        The method prefers non-destructive `create_collection` calls. Transient
        errors trigger bounded retries with exponential backoff; conflicts are
        treated as success. Destructive resets are exposed separately via
        :meth:`reset_collection` to make data loss an explicit operator choice.
        """

        attempts = max(1, retries)
        for attempt in range(1, attempts + 1):
            if self._collection_exists():
                return

            try:
                self._create_collection(vector_size)
                return
            except UnexpectedResponse as exc:
                status_code = getattr(exc, "status_code", None)
                if status_code == 409:  # collection already exists
                    logger.info("Qdrant collection %s already exists", self.collection_name)
                    return
                logger.warning(
                    "Qdrant create_collection failed for %s (attempt %d/%d): %s",
                    self.collection_name,
                    attempt,
                    attempts,
                    exc,
                )
                if attempt == attempts:
                    raise
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.warning(
                    "Qdrant collection ensure attempt %d/%d failed for %s: %s",
                    attempt,
                    attempts,
                    self.collection_name,
                    exc,
                )
                if attempt == attempts:
                    raise

            sleep_seconds = max(0.0, min(retry_backoff * attempt, 2.0))
            if sleep_seconds:
                time.sleep(sleep_seconds)

    def reset_collection(self, vector_size: int) -> None:
        """Destructively recreate the collection, wiping all stored vectors."""

        logger.warning(
            "Recreating Qdrant collection %s – existing embeddings will be deleted",
            self.collection_name,
        )
        vectors_config = qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE)
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
            optimizers_config=qmodels.OptimizersConfigDiff(default_segment_number=2),
        )

    def upsert_chunks(self, chunks: Iterable[ChunkEmbedding]) -> None:
        """Upsert chunk embeddings into the configured collection."""
        points = []
        for item in chunks:
            payload = {**item.chunk.metadata, "chunk_id": item.chunk.chunk_id, "text": item.chunk.text}
            point_id = str(uuid.UUID(item.chunk.content_digest[:32]))
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=item.vector,
                    payload=payload,
                )
            )
        if not points:
            return
        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info("Upserted %d chunk(s) into Qdrant", len(points))

    def delete_artifact(self, artifact_path: str) -> None:
        """Delete all points belonging to an artifact path."""
        filter_ = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="path",
                    match=qmodels.MatchValue(value=artifact_path),
                )
            ]
        )
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.FilterSelector(filter=filter_),
            wait=True,
        )
        logger.info("Deleted chunks for artifact %s", artifact_path)

    def _collection_exists(self) -> bool:
        """Return True when the collection already exists in Qdrant."""

        collection_exists = getattr(self.client, "collection_exists", None)
        if callable(collection_exists):
            try:
                return bool(collection_exists(self.collection_name))
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("collection_exists check failed for %s: %s", self.collection_name, exc)

        get_collection = getattr(self.client, "get_collection", None)
        if callable(get_collection):
            try:
                get_collection(self.collection_name)
                return True
            except Exception as exc:  # pragma: no cover - treat as missing / transient
                logger.debug("get_collection check failed for %s: %s", self.collection_name, exc)
                return False

        return False

    def _create_collection(self, vector_size: int) -> None:
        create_fn = getattr(self.client, "create_collection", None)
        if not callable(create_fn):
            raise RuntimeError(
                "Qdrant client does not expose create_collection; upgrade the client or use reset_collection explicitly",
            )

        vectors_config = qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE)
        create_fn(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
            optimizers_config=qmodels.OptimizersConfigDiff(default_segment_number=2),
        )
        logger.info("Created Qdrant collection %s", self.collection_name)
