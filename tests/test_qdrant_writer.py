from __future__ import annotations

from unittest import mock

from gateway.ingest.artifacts import Artifact, Chunk, ChunkEmbedding
from gateway.ingest.qdrant_writer import QdrantWriter


class RecordingClient:
    def __init__(self) -> None:
        self._collections = set()
        self.recreate_calls: list[dict[str, object]] = []
        self.upserts: list[dict[str, object]] = []

    def get_collection(self, name: str) -> None:
        if name not in self._collections:
            raise RuntimeError("missing")

    def recreate_collection(
        self,
        collection_name: str,
        vectors_config: object,
        optimizers_config: object,
    ) -> None:
        self._collections.add(collection_name)
        self.recreate_calls.append(
            {
                "name": collection_name,
                "size": vectors_config.size,
                "distance": vectors_config.distance,
                "segments": optimizers_config.default_segment_number,
            }
        )

    def upsert(self, collection_name: str, points: object) -> None:
        self.upserts.append({"collection": collection_name, "points": points})


def build_chunk(path: str, text: str, metadata: dict[str, object]) -> ChunkEmbedding:
    artifact = Artifact(
        path=mock.Mock(as_posix=lambda: path),
        artifact_type=metadata.get("artifact_type", "code"),
        subsystem=metadata.get("subsystem"),
        content=text,
        git_commit=metadata.get("git_commit"),
        git_timestamp=metadata.get("git_timestamp"),
        extra_metadata={},
    )
    chunk = Chunk(
        artifact=artifact,
        chunk_id=f"{path}::0",
        text=text,
        sequence=0,
        content_digest="0123456789abcdef0123456789abcdef",
        metadata=metadata,
    )
    return ChunkEmbedding(chunk=chunk, vector=[0.1, 0.2])


def test_ensure_collection_creates_when_missing() -> None:
    client = RecordingClient()
    writer = QdrantWriter(client, "km_test")

    writer.ensure_collection(vector_size=384)

    assert client.recreate_calls
    call = client.recreate_calls[0]
    assert call["name"] == "km_test"
    assert call["size"] == 384
    assert call["segments"] == 2


def test_ensure_collection_noop_when_exists() -> None:
    client = RecordingClient()
    client._collections.add("km_test")
    writer = QdrantWriter(client, "km_test")

    writer.ensure_collection(vector_size=256)

    assert not client.recreate_calls


def test_upsert_chunks_builds_points() -> None:
    client = RecordingClient()
    writer = QdrantWriter(client, "km_test")

    chunk = build_chunk(
        "docs/readme.md",
        "hello world",
        {"artifact_type": "doc", "subsystem": "Kasmina", "tags": ["intro"]},
    )

    writer.upsert_chunks([chunk])

    assert client.upserts
    payload = client.upserts[0]["points"][0]
    assert payload.payload["chunk_id"] == "docs/readme.md::0"
    assert payload.payload["text"] == "hello world"
    assert payload.payload["tags"] == ["intro"]


def test_upsert_chunks_noop_on_empty() -> None:
    client = RecordingClient()
    writer = QdrantWriter(client, "km_test")
    writer.upsert_chunks([])
    assert not client.upserts
