from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Iterable

from gateway.ingest.artifacts import Artifact, Chunk

DEFAULT_WINDOW = 1000
DEFAULT_OVERLAP = 200


class Chunker:
    """Split artifacts into overlapping textual chunks."""

    def __init__(self, window: int = DEFAULT_WINDOW, overlap: int = DEFAULT_OVERLAP) -> None:
        if window <= 0:
            raise ValueError("window must be positive")
        if overlap < 0:
            raise ValueError("overlap cannot be negative")
        self.window = window
        self.overlap = overlap

    def split(self, artifact: Artifact) -> Iterable[Chunk]:
        text = artifact.content
        if not text.strip():
            return []

        step = self.window - self.overlap if self.window > self.overlap else self.window
        chunks: list[Chunk] = []
        for idx, start in enumerate(range(0, len(text), step)):
            end = start + self.window
            chunk_text = text[start:end]
            digest = hashlib.sha256(f"{artifact.path}:{idx}:{chunk_text}".encode("utf-8")).hexdigest()
            chunk_id = f"{artifact.path.as_posix()}::{idx}"
            metadata = {
                "path": artifact.path.as_posix(),
                "artifact_type": artifact.artifact_type,
                "subsystem": artifact.subsystem,
                "git_commit": artifact.git_commit,
                "git_timestamp": artifact.git_timestamp,
                "content_digest": digest,
                "chunk_index": idx,
                **artifact.extra_metadata,
            }
            chunks.append(
                Chunk(
                    artifact=artifact,
                    chunk_id=chunk_id,
                    text=chunk_text,
                    sequence=idx,
                    content_digest=digest,
                    metadata=metadata,
                )
            )
        return chunks

    @staticmethod
    def estimate_chunk_count(path: Path, text: str, *, window: int = DEFAULT_WINDOW, overlap: int = DEFAULT_OVERLAP) -> int:
        if not text:
            return 0
        step = window - overlap if window > overlap else window
        return math.ceil(max(1, len(text)) / step)
