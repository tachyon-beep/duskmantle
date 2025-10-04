"""Pipeline orchestrations for ingestion, chunking, and persistence."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

from filelock import FileLock, Timeout
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
    INGEST_SKIPS_TOTAL,
    INGEST_STALE_RESOLVED_TOTAL,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionConfig:
    """Configuration options controlling ingestion behaviour."""

    repo_root: Path
    dry_run: bool = False
    chunk_window: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "BAAI/bge-m3"
    text_embedding_model: str | None = None
    image_embedding_model: str | None = "sentence-transformers/clip-ViT-L-14"
    use_dummy_embeddings: bool = False
    environment: str = "local"
    include_patterns: tuple[str, ...] = (
        "docs",
        "src",
        "tests",
        ".codacy",
    )
    audit_path: Path | None = None
    coverage_path: Path | None = None
    coverage_history_limit: int = 5
    ledger_path: Path | None = None
    incremental: bool = True
    embed_parallel_workers: int = 2
    max_pending_batches: int = 4
    symbols_enabled: bool = False

    def __post_init__(self) -> None:
        if self.text_embedding_model is None:
            self.text_embedding_model = self.embedding_model


@dataclass(slots=True)
class IngestionResult:
    """Summary of outputs emitted by an ingestion run."""

    run_id: str
    profile: str
    started_at: float
    duration_seconds: float
    artifact_counts: dict[str, int] = field(default_factory=dict)
    chunk_count: int = 0
    repo_head: str | None = None
    success: bool = True
    artifacts: list[dict[str, object]] = field(default_factory=list)
    removed_artifacts: list[dict[str, object]] = field(default_factory=list)


class IngestionPipeline:
    """Execute the ingestion workflow end-to-end."""

    def __init__(
        self,
        qdrant_writer: QdrantWriter | None,
        neo4j_writer: Neo4jWriter | None,
        config: IngestionConfig,
        image_qdrant_writer: QdrantWriter | None = None,
    ) -> None:
        """Initialise the pipeline with writer backends and configuration."""
        self.qdrant_writer = qdrant_writer
        self.image_qdrant_writer = image_qdrant_writer
        self.neo4j_writer = neo4j_writer
        self.config = config
        self._ledger_lock: FileLock | None = None
        if self.config.ledger_path is not None:
            lock_path = self.config.ledger_path.with_suffix(self.config.ledger_path.suffix + ".lock")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            self._ledger_lock = FileLock(str(lock_path))

    def run(self) -> IngestionResult:
        """Execute discovery, chunking, embedding, and persistence for a repo."""
        run_id = uuid.uuid4().hex
        profile = self.config.environment
        started = time.time()
        artifact_counts: dict[str, int] = {}
        chunk_count = 0
        success = False
        repo_head = _current_repo_head(self.config.repo_root)
        ledger_previous = self._load_artifact_ledger()
        current_ledger_entries: dict[str, dict[str, object]] = {}
        removed_artifacts: list[dict[str, object]] = []

        tracer = trace.get_tracer(__name__)
        ingest_span = tracer.start_span(
            "ingestion.run",
            attributes={
                "km.profile": profile,
                "km.repo_head": repo_head or "",
                "km.dry_run": self.config.dry_run,
                "km.embedding_model": self.config.text_embedding_model,
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
                                symbols_enabled=self.config.symbols_enabled,
                            )
                        )
                    )
                    if self.config.symbols_enabled:
                        _annotate_test_symbol_links(artifacts)
                    discover_span.set_attribute("km.ingest.artifact_total", len(artifacts))

                logger.info(
                    "Discovered artifacts",
                    extra={
                        "ingest_run_id": run_id,
                        "profile": profile,
                        "artifact_count": len(artifacts),
                    },
                )

                artifact_details: list[dict[str, object]] = []
                chunker = Chunker(window=self.config.chunk_window, overlap=self.config.chunk_overlap)
                max_workers = max(1, self.config.embed_parallel_workers)
                max_pending = max(1, self.config.max_pending_batches)
                total_chunk_count = 0

                embedder = self._build_embedder()
                image_embedder: Embedder | None = None
                if (
                    not self.config.use_dummy_embeddings
                    and self.config.image_embedding_model
                ):
                    try:
                        image_embedder = Embedder(self.config.image_embedding_model, kind="image")
                    except Exception as exc:
                        logger.warning("Image embedder unavailable: %s", exc)
                        image_embedder = None

                image_artifacts: list[Artifact] = []
                text_artifacts: list[Artifact] = []
                for artifact in artifacts:
                    if artifact.artifact_type == "image":
                        image_artifacts.append(artifact)
                    else:
                        text_artifacts.append(artifact)

                if self.qdrant_writer and not self.config.dry_run:
                    self.qdrant_writer.ensure_collection(embedder.dimension)
                if (
                    self.image_qdrant_writer
                    and image_embedder is not None
                    and not self.config.dry_run
                ):
                    self.image_qdrant_writer.ensure_collection(image_embedder.dimension)

                pending_batches: deque[tuple[Future[list[list[float]]], list[Chunk]]] = deque()

                def _drain_one() -> None:
                    nonlocal total_chunk_count
                    future, batch_chunks = pending_batches.popleft()
                    vectors = future.result()
                    embeddings = self._build_embeddings(batch_chunks, vectors)
                    total_chunk_count += self._persist_embeddings(embeddings)

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    with tracer.start_as_current_span("ingestion.chunk") as chunk_span:
                        for artifact in text_artifacts:
                            artifact_counts[artifact.artifact_type] = artifact_counts.get(artifact.artifact_type, 0) + 1
                            artifact_digest, _ = self._compute_artifact_digest(artifact)
                            path_text = artifact.path.as_posix()
                            existing_entry = ledger_previous.get(path_text)
                            subsystem_criticality = artifact.extra_metadata.get("subsystem_criticality")

                            chunk_count_existing: int | None = None
                            coverage_ratio_existing: float | None = None
                            if self.config.incremental and existing_entry and existing_entry.get("digest") == artifact_digest:
                                existing_chunk_count_raw = existing_entry.get("chunk_count")
                                chunk_count_existing = _coerce_int(existing_chunk_count_raw)
                                if chunk_count_existing is not None:
                                    coverage_ratio_existing = _coerce_float(existing_entry.get("coverage_ratio"))
                                    if coverage_ratio_existing is None:
                                        coverage_ratio_existing = 1.0 if chunk_count_existing else 0.0
                            if chunk_count_existing is not None:
                                artifact_details.append(
                                    {
                                        "path": path_text,
                                        "artifact_type": artifact.artifact_type,
                                        "subsystem": artifact.subsystem,
                                        "chunk_count": chunk_count_existing,
                                        "git_commit": artifact.git_commit,
                                        "git_timestamp": artifact.git_timestamp,
                                        "subsystem_criticality": subsystem_criticality,
                                        "coverage_ratio": coverage_ratio_existing,
                                        "content_digest": artifact_digest,
                                        "skipped": True,
                                        "symbols": artifact.extra_metadata.get("symbols"),
                                        "exercises_symbols": artifact.extra_metadata.get("exercises_symbols"),
                                    }
                                )
                                current_ledger_entries[path_text] = {
                                    "artifact_type": artifact.artifact_type,
                                    "subsystem": artifact.subsystem,
                                    "digest": artifact_digest,
                                    "git_commit": artifact.git_commit,
                                    "git_timestamp": artifact.git_timestamp,
                                    "chunk_count": chunk_count_existing,
                                    "coverage_ratio": coverage_ratio_existing,
                                    "last_seen": started,
                                }
                                INGEST_SKIPS_TOTAL.labels(reason="unchanged").inc()
                                continue

                            artifact_chunks = list(chunker.split(artifact))
                            coverage_ratio = 1.0 if artifact_chunks else 0.0
                            coverage_missing = 1.0 - coverage_ratio
                            for chunk in artifact_chunks:
                                chunk.metadata["environment"] = profile
                                if subsystem_criticality is not None:
                                    chunk.metadata["subsystem_criticality"] = subsystem_criticality
                                chunk.metadata["coverage_ratio"] = coverage_ratio
                                chunk.metadata["coverage_missing"] = coverage_missing

                            if self.neo4j_writer and not self.config.dry_run:
                                self.neo4j_writer.sync_artifact(artifact)

                            artifact_details.append(
                                {
                                    "path": path_text,
                                    "artifact_type": artifact.artifact_type,
                                    "subsystem": artifact.subsystem,
                                    "chunk_count": len(artifact_chunks),
                                    "git_commit": artifact.git_commit,
                                    "git_timestamp": artifact.git_timestamp,
                                    "subsystem_criticality": subsystem_criticality,
                                    "coverage_ratio": coverage_ratio,
                                    "content_digest": artifact_digest,
                                    "skipped": False,
                                    "symbols": artifact.extra_metadata.get("symbols"),
                                    "exercises_symbols": artifact.extra_metadata.get("exercises_symbols"),
                                }
                            )
                            current_ledger_entries[path_text] = {
                                "artifact_type": artifact.artifact_type,
                                "subsystem": artifact.subsystem,
                                "digest": artifact_digest,
                                "git_commit": artifact.git_commit,
                                "git_timestamp": artifact.git_timestamp,
                                "chunk_count": len(artifact_chunks),
                                "coverage_ratio": coverage_ratio,
                                "last_seen": started,
                            }

                            if artifact_chunks:
                                future = executor.submit(self._encode_batch, embedder, artifact_chunks)
                                pending_batches.append((future, artifact_chunks))
                                if len(pending_batches) >= max_pending:
                                    _drain_one()

                        while pending_batches:
                            _drain_one()

                        for artifact in image_artifacts:
                            artifact_counts[artifact.artifact_type] = artifact_counts.get(artifact.artifact_type, 0) + 1
                            artifact_digest, artifact_bytes = self._compute_artifact_digest(artifact)
                            path_text = artifact.path.as_posix()
                            existing_entry = ledger_previous.get(path_text)
                            subsystem_criticality = artifact.extra_metadata.get("subsystem_criticality")

                            chunk_count_existing: int | None = None
                            coverage_ratio_existing: float | None = None
                            if self.config.incremental and existing_entry and existing_entry.get("digest") == artifact_digest:
                                chunk_count_existing = _coerce_int(existing_entry.get("chunk_count"))
                                if chunk_count_existing is not None:
                                    coverage_ratio_existing = _coerce_float(existing_entry.get("coverage_ratio"))
                                    if coverage_ratio_existing is None:
                                        coverage_ratio_existing = 1.0 if chunk_count_existing else 0.0
                            if chunk_count_existing is not None:
                                artifact_details.append(
                                    {
                                        "path": path_text,
                                        "artifact_type": artifact.artifact_type,
                                        "subsystem": artifact.subsystem,
                                        "chunk_count": chunk_count_existing,
                                        "git_commit": artifact.git_commit,
                                        "git_timestamp": artifact.git_timestamp,
                                        "subsystem_criticality": subsystem_criticality,
                                        "coverage_ratio": coverage_ratio_existing,
                                        "content_digest": artifact_digest,
                                        "skipped": True,
                                        "symbols": artifact.extra_metadata.get("symbols"),
                                        "exercises_symbols": artifact.extra_metadata.get("exercises_symbols"),
                                    }
                                )
                                current_ledger_entries[path_text] = {
                                    "artifact_type": artifact.artifact_type,
                                    "subsystem": artifact.subsystem,
                                    "digest": artifact_digest,
                                    "git_commit": artifact.git_commit,
                                    "git_timestamp": artifact.git_timestamp,
                                    "chunk_count": chunk_count_existing,
                                    "coverage_ratio": coverage_ratio_existing,
                                    "last_seen": started,
                                }
                                INGEST_SKIPS_TOTAL.labels(reason="unchanged").inc()
                                continue

                            if self.neo4j_writer and not self.config.dry_run:
                                self.neo4j_writer.sync_artifact(artifact)

                            image_embeddings: list[ChunkEmbedding] = []
                            if (
                                not self.config.dry_run
                                and self.image_qdrant_writer is not None
                                and image_embedder is not None
                            ):
                                image_embeddings = self._embed_image_artifact(artifact, image_embedder, artifact_bytes)
                                if image_embeddings:
                                    for embedding in image_embeddings:
                                        chunk = embedding.chunk
                                        chunk.metadata["environment"] = profile
                                        if subsystem_criticality is not None:
                                            chunk.metadata["subsystem_criticality"] = subsystem_criticality
                                        chunk.metadata["coverage_ratio"] = 1.0
                                        chunk.metadata["coverage_missing"] = 0.0
                                    total_chunk_count += self._persist_image_embeddings(image_embeddings)
                            else:
                                if image_embedder is None and not self.config.dry_run:
                                    logger.warning("Image embedder not available; skipping vector index for %s", artifact.path)
                                image_embeddings = []

                            coverage_chunks = len(image_embeddings)
                            coverage_ratio = 1.0 if coverage_chunks else 0.0

                            artifact_details.append(
                                {
                                    "path": path_text,
                                    "artifact_type": artifact.artifact_type,
                                    "subsystem": artifact.subsystem,
                                    "chunk_count": coverage_chunks,
                                    "git_commit": artifact.git_commit,
                                    "git_timestamp": artifact.git_timestamp,
                                    "subsystem_criticality": subsystem_criticality,
                                    "coverage_ratio": coverage_ratio,
                                    "content_digest": artifact_digest,
                                    "skipped": False,
                                    "symbols": artifact.extra_metadata.get("symbols"),
                                    "exercises_symbols": artifact.extra_metadata.get("exercises_symbols"),
                                }
                            )
                            current_ledger_entries[path_text] = {
                                "artifact_type": artifact.artifact_type,
                                "subsystem": artifact.subsystem,
                                "digest": artifact_digest,
                                "git_commit": artifact.git_commit,
                                "git_timestamp": artifact.git_timestamp,
                                "chunk_count": coverage_chunks,
                                "coverage_ratio": coverage_ratio,
                                "last_seen": started,
                            }
                            total_chunk_count += coverage_chunks

                        chunk_span.set_attribute("km.ingest.chunk_total", total_chunk_count)
                        chunk_span.set_attribute(
                            "km.ingest.artifact_kinds",
                            ",".join(sorted(artifact_counts.keys())) or "",
                        )

                logger.info(
                    "Generated chunks",
                    extra={
                        "ingest_run_id": run_id,
                        "profile": profile,
                        "chunk_count": total_chunk_count,
                    },
                )

                chunk_count = total_chunk_count
                removed_artifacts = self._handle_stale_artifacts(ledger_previous, current_ledger_entries, profile)

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
                    removed_artifacts=removed_artifacts,
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

    def _compute_artifact_digest(self, artifact: Artifact) -> tuple[str, bytes | None]:
        if artifact.artifact_type == "image":
            image_path = self.config.repo_root / artifact.path
            try:
                data = image_path.read_bytes()
            except OSError as exc:
                logger.warning("Failed to read image artifact %s: %s", artifact.path, exc)
                return hashlib.sha256(artifact.path.as_posix().encode("utf-8")).hexdigest(), None
            return hashlib.sha256(data).hexdigest(), data
        return hashlib.sha256(artifact.content.encode("utf-8")).hexdigest(), None

    def _embed_image_artifact(
        self,
        artifact: Artifact,
        embedder: Embedder,
        artifact_bytes: bytes | None,
    ) -> list[ChunkEmbedding]:
        image_path = self.config.repo_root / artifact.path
        try:
            vectors = embedder.encode([str(image_path)])
        except Exception as exc:  # pragma: no cover - hardware dependent
            logger.warning("Failed to embed image artifact %s: %s", artifact.path, exc)
            return []
        if not vectors:
            return []
        vector = vectors[0]
        namespace = artifact.path.parts[0] if artifact.path.parts else ""
        media_type = artifact.extra_metadata.get("media_type")
        digest_source = artifact_bytes if artifact_bytes is not None else image_path.as_posix().encode("utf-8")
        digest = hashlib.sha256(digest_source).hexdigest()
        metadata = {
            "path": artifact.path.as_posix(),
            "artifact_type": artifact.artifact_type,
            "subsystem": artifact.subsystem,
            "git_commit": artifact.git_commit,
            "git_timestamp": artifact.git_timestamp,
            "content_digest": digest,
            "chunk_index": 0,
            "namespace": namespace,
            "media_type": media_type,
        }
        metadata.update(artifact.extra_metadata)
        chunk = Chunk(
            artifact=artifact,
            chunk_id=f"{artifact.path.as_posix()}::image",
            text=artifact.path.name,
            sequence=0,
            content_digest=digest,
            metadata=metadata,
        )
        return [ChunkEmbedding(chunk=chunk, vector=list(vector))]

    def _build_embedder(self) -> Embedder:
        if self.config.use_dummy_embeddings:
            logger.warning("Using dummy embeddings; results are not suitable for production")
            return DummyEmbedder()
        model_name = self.config.text_embedding_model or self.config.embedding_model
        return Embedder(model_name, kind="text")

    def _encode_batch(self, embedder: Embedder, chunks: Sequence[Chunk]) -> list[list[float]]:
        return embedder.encode(chunk.text for chunk in chunks)

    def _build_embeddings(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> list[ChunkEmbedding]:
        embeddings: list[ChunkEmbedding] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            embeddings.append(ChunkEmbedding(chunk=chunk, vector=list(vector)))
        return embeddings

    def _persist_image_embeddings(self, embeddings: Sequence[ChunkEmbedding]) -> int:
        if not embeddings:
            return 0
        if self.image_qdrant_writer and not self.config.dry_run:
            self.image_qdrant_writer.upsert_chunks(embeddings)
        if self.neo4j_writer and not self.config.dry_run:
            self.neo4j_writer.sync_chunks(embeddings)
        return len(embeddings)

    def _persist_embeddings(self, embeddings: Sequence[ChunkEmbedding]) -> int:
        if not embeddings:
            return 0
        if self.qdrant_writer and not self.config.dry_run:
            self.qdrant_writer.upsert_chunks(embeddings)
        if self.neo4j_writer and not self.config.dry_run:
            self.neo4j_writer.sync_chunks(embeddings)
        return len(embeddings)

    def _handle_stale_artifacts(
        self,
        previous: dict[str, dict[str, object]],
        current: dict[str, dict[str, object]],
        profile: str,
    ) -> list[dict[str, object]]:
        ledger_path = self.config.ledger_path
        if ledger_path is None:
            return []

        stale_paths = sorted(set(previous) - set(current))
        removed: list[dict[str, object]] = []

        if stale_paths:
            logger.info(
                "Detected %d stale artifact(s)",
                len(stale_paths),
                extra={"stale_artifacts": stale_paths},
            )

        for path in stale_paths:
            entry = previous.get(path, {})
            status = "dry-run" if self.config.dry_run else self._delete_artifact_from_backends(path)
            removed.append(
                {
                    "path": path,
                    "artifact_type": entry.get("artifact_type"),
                    "subsystem": entry.get("subsystem"),
                    "digest": entry.get("digest"),
                    "status": status,
                }
            )

        deleted_count = sum(1 for item in removed if item.get("status") == "deleted")
        if deleted_count:
            INGEST_STALE_RESOLVED_TOTAL.labels(profile=profile).inc(deleted_count)

        if not self.config.dry_run:
            self._write_artifact_ledger(current)

        return removed

    def _delete_artifact_from_backends(self, path: str) -> str:
        errors: list[str] = []

        if self.neo4j_writer is not None:
            try:
                self.neo4j_writer.delete_artifact(path)
            except Exception as exc:  # pragma: no cover - driver/network error
                errors.append(f"neo4j: {exc}")

        if self.qdrant_writer is not None:
            try:
                self.qdrant_writer.delete_artifact(path)
            except Exception as exc:  # pragma: no cover - network error
                errors.append(f"qdrant: {exc}")
        if self.image_qdrant_writer is not None:
            try:
                self.image_qdrant_writer.delete_artifact(path)
            except Exception as exc:  # pragma: no cover - network error
                errors.append(f"qdrant_image: {exc}")

        if errors:
            message = ", ".join(errors)
            logger.error("Failed to delete stale artifact %s: %s", path, message)
            raise RuntimeError(f"Failed to delete stale artifact {path}: {message}")

        logger.info("Removed stale artifact %s", path)
        return "deleted"

    def _load_artifact_ledger(self) -> dict[str, dict[str, object]]:
        ledger_path = self.config.ledger_path
        if ledger_path is None or not ledger_path.exists():
            return {}

        lock = self._ledger_lock
        if lock is not None:
            try:
                lock.acquire(timeout=1)
            except Timeout:
                logger.warning("Timed out waiting for ledger lock at %s", lock.lock_file)
                return {}
            try:
                return self._read_ledger_file(ledger_path)
            finally:
                lock.release()
        return self._read_ledger_file(ledger_path)

    def _read_ledger_file(self, ledger_path: Path) -> dict[str, dict[str, object]]:
        try:
            data = json.loads(ledger_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("Failed to read artifact ledger %s: %s", ledger_path, exc)
            return {}

        entries = data.get("artifacts") if isinstance(data, dict) else None
        if not isinstance(entries, dict):
            logger.warning("Artifact ledger %s missing 'artifacts' mapping", ledger_path)
            return {}

        cleaned: dict[str, dict[str, object]] = {}
        for path, payload in entries.items():
            if isinstance(path, str) and isinstance(payload, dict):
                cleaned[path] = payload
        return cleaned

    def _write_artifact_ledger(self, entries: dict[str, dict[str, object]]) -> None:
        ledger_path = self.config.ledger_path
        if ledger_path is None:
            return

        payload = {
            "updated_at": time.time(),
            "artifacts": entries,
        }

        lock = self._ledger_lock
        if lock is not None:
            try:
                lock.acquire(timeout=5)
            except Timeout as exc:
                raise RuntimeError(f"Timed out acquiring ledger lock for {ledger_path}") from exc
            try:
                self._atomic_write(ledger_path, payload)
            finally:
                lock.release()
        else:
            self._atomic_write(ledger_path, payload)

    def _atomic_write(self, ledger_path: Path, payload: dict[str, object]) -> None:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = ledger_path.with_suffix(ledger_path.suffix + f".{uuid.uuid4().hex}.tmp")
        try:
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            os.replace(tmp_path, ledger_path)
        finally:
            with suppress(FileNotFoundError):
                tmp_path.unlink()


_SYMBOL_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")


def _annotate_test_symbol_links(artifacts: list[Artifact]) -> None:
    """Annotate test artifacts with symbol relationships derived from heuristics."""

    symbol_index, alias_map = _build_symbol_index(artifacts)
    if not symbol_index or not alias_map:
        return

    for artifact in artifacts:
        if artifact.artifact_type != "test" or artifact.path.suffix.lower() != ".py":
            continue
        matches = _match_symbol_aliases(artifact, symbol_index, alias_map)
        if not matches:
            continue
        sorted_ids = sorted(matches)
        artifact.extra_metadata["exercises_symbols"] = sorted_ids
        artifact.extra_metadata["exercises_symbol_details"] = [
            {
                "symbol_id": symbol_id,
                "qualified_name": symbol_index[symbol_id]["qualified_name"],
                "name": symbol_index[symbol_id]["name"],
                "source_path": symbol_index[symbol_id]["path"],
            }
            for symbol_id in sorted_ids
        ]


def _build_symbol_index(artifacts: list[Artifact]) -> tuple[dict[str, dict[str, str]], dict[str, set[str]]]:
    index: dict[str, dict[str, str]] = {}
    alias_map: dict[str, set[str]] = defaultdict(set)

    for artifact in artifacts:
        metadata = artifact.extra_metadata or {}
        symbols = metadata.get("symbols")
        if not isinstance(symbols, list):
            continue
        for raw_symbol in symbols:
            if not isinstance(raw_symbol, dict):
                continue
            symbol_id = raw_symbol.get("id")
            qualified = str(raw_symbol.get("qualified_name") or raw_symbol.get("name") or "").strip()
            if not symbol_id or not qualified:
                continue
            name = str(raw_symbol.get("name") or qualified.split(".")[-1]).strip()
            language = str(raw_symbol.get("language") or "").strip().lower()
            module_alias = _module_alias_for_path(artifact.path)
            entry = {
                "id": symbol_id,
                "qualified_name": qualified,
                "name": name,
                "language": language,
                "path": artifact.path.as_posix(),
                "module_alias": module_alias,
            }
            aliases = _symbol_aliases(entry)
            if not aliases:
                continue
            index[symbol_id] = entry
            for alias in aliases:
                alias_map.setdefault(alias, set()).add(symbol_id)

    return index, alias_map


def _symbol_aliases(entry: dict[str, str]) -> set[str]:
    aliases: set[str] = set()
    qualified = entry["qualified_name"]
    name = entry["name"]
    module_alias = entry.get("module_alias") or ""

    for candidate in (qualified, name, qualified.split(".")[-1]):
        if candidate:
            aliases.add(candidate)

    if module_alias:
        if name:
            aliases.add(f"{module_alias}.{name}")
        if qualified:
            aliases.add(f"{module_alias}.{qualified}")

    return {alias for alias in aliases if alias and len(alias) >= 3}


def _module_alias_for_path(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[0] in {"src", "source", "lib"}:
        parts = parts[1:]
    return ".".join(parts)


def _match_symbol_aliases(
    artifact: Artifact,
    symbol_index: dict[str, dict[str, str]],
    alias_map: dict[str, set[str]],
) -> set[str]:
    content = artifact.content
    if not content.strip():
        return set()

    matches: set[str] = set()
    for match in _SYMBOL_TOKEN_PATTERN.finditer(content):
        token = match.group()
        if token not in alias_map:
            continue
        if not _token_context_valid(content, match):
            continue
        for symbol_id in alias_map[token]:
            entry = symbol_index[symbol_id]
            language = entry.get("language") or ""
            if language and language != "python":
                continue
            if not _paths_related(artifact.path, entry["path"], token):
                continue
            matches.add(symbol_id)
    return matches


def _token_context_valid(content: str, match: re.Match[str]) -> bool:
    start, end = match.span()
    if start > 0:
        preceding = content[start - 1]
        if preceding in {'"', "'", "#"}:
            return False
        if preceding == "@":
            return True
    tail = content[end:]
    stripped = tail.lstrip()
    token = match.group()
    if "." in token:
        return True
    if stripped.startswith(("(", ".", "=", ",", ")", ":")):
        return True
    return False


def _paths_related(test_path: Path, symbol_path: str, alias: str) -> bool:
    try:
        symbol_parts = Path(symbol_path).with_suffix("").parts
    except Exception:  # pragma: no cover - defensive
        symbol_parts = ()
    test_parts = test_path.with_suffix("").parts

    test_tokens = {part for part in test_parts if part not in {"tests", "src", "test"}}
    symbol_tokens = {part for part in symbol_parts if part not in {"src", "lib"}}

    if test_tokens & symbol_tokens:
        return True
    return "." in alias


def _current_repo_head(repo_root: Path) -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            or None
        )
    except Exception:
        return None


def _coerce_int(value: object) -> int | None:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _coerce_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None
