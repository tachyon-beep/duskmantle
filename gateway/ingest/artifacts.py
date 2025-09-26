from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Artifact:
    """Represents a repository artifact prior to chunking."""

    path: Path
    artifact_type: str
    subsystem: str | None
    content: str
    git_commit: str | None
    git_timestamp: int | None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    """Represents a chunk ready for embedding and indexing."""

    artifact: Artifact
    chunk_id: str
    text: str
    sequence: int
    content_digest: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class ChunkEmbedding:
    """Chunk plus embedding vector."""

    chunk: Chunk
    vector: list[float]
