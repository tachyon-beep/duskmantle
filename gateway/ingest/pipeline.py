from __future__ import annotations

import logging
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from gateway.ingest.artifacts import Artifact, Chunk, ChunkEmbedding
from gateway.ingest.chunking import Chunker
from gateway.ingest.discovery import DiscoveryConfig, discover
from gateway.ingest.embedding import DummyEmbedder, Embedder
from gateway.ingest.neo4j_writer import Neo4jWriter
from gateway.ingest.qdrant_writer import QdrantWriter
from gateway.observability.metrics import (
    INGEST_ARTIFACTS_TOTAL,
    INGEST_CHUNKS_TOTAL,
    INGEST_DURATION_SECONDS,
    INGEST_LAST_RUN_STATUS,
    INGEST_LAST_RUN_TIMESTAMP,
)

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
    audit_path: Path | None = None
    coverage_path: Path | None = None


@dataclass(slots=True)
class IngestionResult:
    run_id: str
    profile: str
    started_at: float
    duration_seconds: float
    artifact_counts: dict[str, int] = field(default_factory=dict)
    chunk_count: int = 0
    repo_head: str | None = None
    success: bool = True


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

    def run(self) -> IngestionResult:
        run_id = uuid.uuid4().hex
        profile = self.config.environment
        started = time.time()
        artifact_counts: dict[str, int] = {}
        chunk_count = 0
        success = False
        repo_head = _current_repo_head(self.config.repo_root)

        logger.info(
            "Starting ingestion",
            extra={"ingest_run_id": run_id, "profile": profile, "repo_head": repo_head},
        )

        try:
            artifacts = list(discover(DiscoveryConfig(repo_root=self.config.repo_root)))
            logger.info(
                "Discovered artifacts",
                extra={
                    "ingest_run_id": run_id,
                    "profile": profile,
                    "artifact_count": len(artifacts),
                },
            )

            chunker = Chunker(window=self.config.chunk_window, overlap=self.config.chunk_overlap)
            chunks: list[Chunk] = []
            for artifact in artifacts:
                artifact_counts[artifact.artifact_type] = artifact_counts.get(artifact.artifact_type, 0) + 1
                artifact_chunks = list(chunker.split(artifact))
                for chunk in artifact_chunks:
                    chunk.metadata["environment"] = profile
                chunks.extend(artifact_chunks)
                if self.neo4j_writer and not self.config.dry_run:
                    self.neo4j_writer.sync_artifact(artifact)

            chunk_count = len(chunks)
            logger.info(
                "Generated chunks",
                extra={
                    "ingest_run_id": run_id,
                    "profile": profile,
                    "chunk_count": chunk_count,
                },
            )

            embedder = self._build_embedder()
            if self.qdrant_writer and not self.config.dry_run:
                self.qdrant_writer.ensure_collection(embedder.dimension)

            embeddings = self._embed_chunks(embedder, chunks)

            if self.qdrant_writer and not self.config.dry_run:
                self.qdrant_writer.upsert_chunks(embeddings)
            if self.neo4j_writer and not self.config.dry_run:
                self.neo4j_writer.sync_chunks(embeddings)

            success = True
            return IngestionResult(
                run_id=run_id,
                profile=profile,
                started_at=started,
                duration_seconds=time.time() - started,
                artifact_counts=artifact_counts,
                chunk_count=chunk_count,
                repo_head=repo_head,
                success=True,
            )
        finally:
            duration = time.time() - started
            status_label = "success" if success else "failure"
            INGEST_DURATION_SECONDS.labels(profile, status_label).observe(duration)
            if success:
                for artifact_type, count in artifact_counts.items():
                    INGEST_ARTIFACTS_TOTAL.labels(profile, artifact_type).inc(count)
                INGEST_CHUNKS_TOTAL.labels(profile).inc(chunk_count)
                INGEST_LAST_RUN_STATUS.labels(profile).set(1)
            else:
                INGEST_LAST_RUN_STATUS.labels(profile).set(0)
            INGEST_LAST_RUN_TIMESTAMP.labels(profile).set(time.time())
            logger.info(
                "Ingestion completed",
                extra={
                    "ingest_run_id": run_id,
                    "profile": profile,
                    "duration_seconds": duration,
                    "success": success,
                },
            )

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


def _current_repo_head(repo_root: Path) -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            .strip()
            or None
        )
    except Exception:
        return None
