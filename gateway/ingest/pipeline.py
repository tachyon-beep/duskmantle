from __future__ import annotations

import logging
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

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
    include_patterns: tuple[str, ...] = (
        "docs",
        "src/esper",
        "tests",
        "src/esper/leyline/_generated",
        ".codacy",
    )
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
    artifacts: list[dict[str, object]] = field(default_factory=list)


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

        tracer = trace.get_tracer(__name__)
        ingest_span = tracer.start_span(
            "ingestion.run",
            attributes={
                "km.profile": profile,
                "km.repo_head": repo_head or "",
                "km.dry_run": self.config.dry_run,
                "km.embedding_model": self.config.embedding_model,
            },
        )

        with trace.use_span(ingest_span, end_on_exit=True):
            logger.info(
                "Starting ingestion",
                extra={
                    "ingest_run_id": run_id,
                    "profile": profile,
                    "repo_head": repo_head,
                },
            )

            try:
                with tracer.start_as_current_span("ingestion.discover") as discover_span:
                    artifacts = list(
                        discover(
                            DiscoveryConfig(
                                repo_root=self.config.repo_root,
                                include_patterns=self.config.include_patterns,
                            )
                        )
                    )
                    discover_span.set_attribute("km.ingest.artifact_total", len(artifacts))

                logger.info(
                    "Discovered artifacts",
                    extra={
                        "ingest_run_id": run_id,
                        "profile": profile,
                        "artifact_count": len(artifacts),
                    },
                )

                chunks: list[Chunk] = []
                artifact_details: list[dict[str, object]] = []
                chunker = Chunker(window=self.config.chunk_window, overlap=self.config.chunk_overlap)

                with tracer.start_as_current_span("ingestion.chunk") as chunk_span:
                    for artifact in artifacts:
                        artifact_counts[artifact.artifact_type] = artifact_counts.get(artifact.artifact_type, 0) + 1
                        artifact_chunks = list(chunker.split(artifact))
                        coverage_ratio = 1.0 if artifact_chunks else 0.0
                        subsystem_criticality = artifact.extra_metadata.get("subsystem_criticality")
                        coverage_missing = 1.0 - coverage_ratio
                        for chunk in artifact_chunks:
                            chunk.metadata["environment"] = profile
                            if subsystem_criticality is not None:
                                chunk.metadata["subsystem_criticality"] = subsystem_criticality
                            chunk.metadata["coverage_ratio"] = coverage_ratio
                            chunk.metadata["coverage_missing"] = coverage_missing
                        chunks.extend(artifact_chunks)
                        if self.neo4j_writer and not self.config.dry_run:
                            self.neo4j_writer.sync_artifact(artifact)
                        artifact_details.append(
                            {
                                "path": artifact.path.as_posix(),
                                "artifact_type": artifact.artifact_type,
                                "subsystem": artifact.subsystem,
                                "chunk_count": len(artifact_chunks),
                                "git_commit": artifact.git_commit,
                                "git_timestamp": artifact.git_timestamp,
                                "subsystem_criticality": subsystem_criticality,
                                "coverage_ratio": coverage_ratio,
                            }
                        )

                    chunk_count = len(chunks)
                    chunk_span.set_attribute("km.ingest.chunk_total", chunk_count)
                    chunk_span.set_attribute(
                        "km.ingest.artifact_kinds",
                        ",".join(sorted(artifact_counts.keys())) or "",
                    )

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

                with tracer.start_as_current_span("ingestion.embed") as embed_span:
                    embeddings = self._embed_chunks(embedder, chunks)
                    embed_span.set_attribute("km.ingest.embedding_total", len(embeddings))

                with tracer.start_as_current_span("ingestion.persist") as persist_span:
                    wrote_qdrant = False
                    wrote_neo4j = False
                    if self.qdrant_writer and not self.config.dry_run:
                        self.qdrant_writer.upsert_chunks(embeddings)
                        wrote_qdrant = True
                    if self.neo4j_writer and not self.config.dry_run:
                        self.neo4j_writer.sync_chunks(embeddings)
                        wrote_neo4j = True
                    persist_span.set_attribute("km.ingest.persist.qdrant", wrote_qdrant)
                    persist_span.set_attribute("km.ingest.persist.neo4j", wrote_neo4j)

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
                    artifacts=artifact_details,
                )
            except Exception as exc:  # pragma: no cover - exercised via failure scenarios
                ingest_span.record_exception(exc)
                raise
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
                ingest_span.set_attribute("km.ingest.duration_seconds", duration)
                ingest_span.set_attribute("km.ingest.chunk_total", chunk_count)
                ingest_span.set_attribute("km.ingest.success", success)
                if not success:
                    ingest_span.set_status(Status(StatusCode.ERROR, description="ingestion failed"))

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
