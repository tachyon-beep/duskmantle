from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
from qdrant_client.http import models as qmodels

from gateway.ingest.qdrant_writer import QdrantWriter


@dataclass
class _FakeChunk:
    chunk_id: str
    content_digest: str
    metadata: dict[str, object]
    text: str


@dataclass
class _ChunkEmbedding:
    chunk: _FakeChunk
    vector: list[float]


class _FakeClient:
    def __init__(self) -> None:
        self.calls = deque()

    def upsert(self, *, collection_name: str, points: list[qmodels.PointStruct]) -> None:
        self.calls.append((collection_name, points))


def _embedding(idx: int) -> _ChunkEmbedding:
    chunk = _FakeChunk(
        chunk_id=f"chunk-{idx}",
        content_digest=f"{idx:032x}",
        metadata={"path": f"src/file_{idx}.py"},
        text=f"snippet {idx}",
    )
    vector = list(np.arange(3, dtype=np.float32) + idx)
    return _ChunkEmbedding(chunk=chunk, vector=vector)  # type: ignore[arg-type]


def test_upsert_chunks_batches_calls() -> None:
    client = _FakeClient()
    writer = QdrantWriter(client, "collection")
    embeddings = [_embedding(i) for i in range(5)]

    writer.upsert_chunks(embeddings, batch_size=2)

    assert len(client.calls) == 3
    sizes = [len(points) for (_, points) in client.calls]
    assert sizes == [2, 2, 1]
    # verify IDs are stable UUID derived from digest
    first_batch = client.calls[0][1]
    assert first_batch[0].id == "00000000-0000-0000-0000-000000000000"
    assert first_batch[1].id == "00000000-0000-0000-0000-000000000001"


