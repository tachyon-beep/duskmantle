"""High-level orchestration routines for running ingestion."""

from __future__ import annotations

import logging
from pathlib import Path

from neo4j import GraphDatabase
from qdrant_client import QdrantClient

from gateway.config.settings import AppSettings
from gateway.ingest.audit import AuditLogger
from gateway.ingest.coverage import write_coverage_report
from gateway.ingest.lifecycle import LifecycleConfig, build_graph_service, write_lifecycle_report
from gateway.ingest.neo4j_writer import Neo4jWriter
from gateway.ingest.pipeline import IngestionConfig, IngestionPipeline, IngestionResult
from gateway.ingest.qdrant_writer import QdrantWriter

logger = logging.getLogger(__name__)


def execute_ingestion(
    *,
    settings: AppSettings,
    profile: str,
    repo_override: Path | None = None,
    dry_run: bool | None = None,
    use_dummy_embeddings: bool | None = None,
    incremental: bool | None = None,
) -> IngestionResult:
    """Run ingestion using shared settings and return result."""

    repo_root = repo_override or settings.repo_root
    dry = settings.dry_run if dry_run is None else dry_run
    use_dummy = settings.ingest_use_dummy_embeddings if use_dummy_embeddings is None else use_dummy_embeddings
    incremental_enabled = settings.ingest_incremental_enabled if incremental is None else incremental

    state_path = settings.state_path

    qdrant_writer = None
    if not dry:
        qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        qdrant_writer = QdrantWriter(qdrant_client, settings.qdrant_collection)

    neo4j_writer = None
    driver = None
    if not dry:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        neo4j_writer = Neo4jWriter(driver, database=settings.neo4j_database)

    audit_logger = None
    audit_path = None
    coverage_path = None
    lifecycle_path = None
    ledger_path = state_path / "reports" / "artifact_ledger.json"
    if not dry:
        audit_path = state_path / "audit" / "audit.db"
        coverage_path = state_path / "reports" / "coverage_report.json"
        lifecycle_path = state_path / "reports" / "lifecycle_report.json"
        audit_logger = AuditLogger(audit_path)

    config = IngestionConfig(
        repo_root=repo_root,
        dry_run=dry,
        chunk_window=settings.ingest_window,
        chunk_overlap=settings.ingest_overlap,
        embedding_model=settings.embedding_model,
        use_dummy_embeddings=use_dummy,
        environment=profile,
        audit_path=audit_path,
        coverage_path=coverage_path,
        coverage_history_limit=settings.coverage_history_limit,
        ledger_path=ledger_path,
        incremental=incremental_enabled,
        embed_parallel_workers=max(1, settings.ingest_parallel_workers),
        max_pending_batches=max(1, settings.ingest_max_pending_batches),
    )

    pipeline = IngestionPipeline(qdrant_writer=qdrant_writer, neo4j_writer=neo4j_writer, config=config)

    graph_service = None
    if driver is not None and settings.lifecycle_report_enabled:
        graph_service = build_graph_service(driver=driver, database=settings.neo4j_database, cache_ttl=0)

    try:
        if neo4j_writer and not dry:
            neo4j_writer.ensure_constraints()
        result = pipeline.run()
        if audit_logger and result.success:
            audit_logger.record(result)
        if not dry and settings.coverage_enabled and coverage_path is not None:
            write_coverage_report(
                result,
                config,
                output_path=coverage_path,
                history_limit=settings.coverage_history_limit,
            )
        if not dry and settings.lifecycle_report_enabled and lifecycle_path is not None:
            lifecycle_config = LifecycleConfig(
                output_path=lifecycle_path,
                stale_days=settings.lifecycle_stale_days,
                graph_enabled=graph_service is not None,
                history_limit=settings.lifecycle_history_limit,
            )
            write_lifecycle_report(
                result,
                config=lifecycle_config,
                graph_service=graph_service,
            )
        return result
    finally:
        if driver is not None:
            driver.close()
