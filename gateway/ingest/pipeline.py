from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from gateway.ingest.artifacts import Artifact, Chunk, ChunkEmbedding
from gateway.ingest.chunking import Chunker
from gateway.ingest.discovery import DiscoveryConfig, discover
from gateway.ingest.embedding import DummyEmbedder, Embedder
from gateway.ingest.neo4j_writer import Neo4jWriter
from gateway.ingest.qdrant_writer import QdrantWriter

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionConfig:
    repo_root: Path
    dry_run: bool = False
    chunk_window: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    use_dummy_embeddings: bool = False
    environment: str = "local"


class IngestionPipeline:
    def __init__(
        self,
        qdrant_writer: QdrantWriter | None,
        neo4j_writer: Neo4jWriter | None,
        config: IngestionConfig,
    ) -> None:
        self.qdrant_writer = qdrant_writer
        self.neo4j_writer = neo4j_writer
        self.config = config

    def run(self) -> None:
        started = time.time()
        artifacts = list(discover(DiscoveryConfig(repo_root=self.config.repo_root)))
        logger.info("Discovered %d artifacts", len(artifacts))
        chunker = Chunker(window=self.config.chunk_window, overlap=self.config.chunk_overlap)
        chunks: list[Chunk] = []
        for artifact in artifacts:
            artifact_chunks = list(chunker.split(artifact))
            for chunk in artifact_chunks:
                chunk.metadata["environment"] = self.config.environment
            chunks.extend(artifact_chunks)
            if self.neo4j_writer and not self.config.dry_run:
                self.neo4j_writer.sync_artifact(artifact)
        logger.info("Generated %d chunk(s)", len(chunks))

        embedder = self._build_embedder()
        if self.qdrant_writer and not self.config.dry_run:
            self.qdrant_writer.ensure_collection(embedder.dimension)

        embeddings = self._embed_chunks(embedder, chunks)

        if self.qdrant_writer and not self.config.dry_run:
            self.qdrant_writer.upsert_chunks(embeddings)
        if self.neo4j_writer and not self.config.dry_run:
            self.neo4j_writer.sync_chunks(embeddings)

        elapsed = time.time() - started
        logger.info("Ingestion complete in %.2fs", elapsed)

    def _build_embedder(self) -> Embedder:
        if self.config.use_dummy_embeddings:
            logger.warning("Using dummy embeddings; results are not suitable for production")
            return DummyEmbedder()
        return Embedder(self.config.embedding_model)

    def _embed_chunks(self, embedder: Embedder, chunks: Sequence[Chunk]) -> list[ChunkEmbedding]:
        if not chunks:
            return []
        vectors = embedder.encode(chunk.text for chunk in chunks)
        return [
            ChunkEmbedding(chunk=chunk, vector=vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
