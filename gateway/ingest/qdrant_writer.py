from __future__ import annotations

import logging
import uuid
from typing import Iterable

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from gateway.ingest.artifacts import ChunkEmbedding

logger = logging.getLogger(__name__)


class QdrantWriter:
    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        self.client = client
        self.collection_name = collection_name

    def ensure_collection(self, vector_size: int) -> None:
        try:
            self.client.get_collection(self.collection_name)
            return
        except Exception:  # pragma: no cover - network call
            logger.info("Creating Qdrant collection %s", self.collection_name)
        vectors_config = qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE)
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
            optimizers_config=qmodels.OptimizersConfigDiff(default_segment_number=2),
        )

    def upsert_chunks(self, chunks: Iterable[ChunkEmbedding]) -> None:
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
