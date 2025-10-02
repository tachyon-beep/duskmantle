"""Helpers for writing chunk embeddings into Qdrant collections."""

from __future__ import annotations

import logging
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

    def ensure_collection(self, vector_size: int) -> None:
        """Ensure the collection exists with the desired vector dimensionality."""
        collection_exists = getattr(self.client, "collection_exists", None)
        if callable(collection_exists):
            try:
                if collection_exists(self.collection_name):
                    return
            except UnexpectedResponse:
                logger.info("Collection check failed for %s; recreating", self.collection_name)
            except Exception:  # pragma: no cover - defensive
                logger.warning("Unexpected error checking Qdrant collection existence", exc_info=True)
        else:
            try:
                self.client.get_collection(self.collection_name)
                return
            except Exception:  # pragma: no cover - fallback for older clients
                logger.info("Collection lookup failed for %s; recreating", self.collection_name)

        logger.info("Creating Qdrant collection %s", self.collection_name)
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
