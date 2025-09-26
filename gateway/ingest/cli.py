from __future__ import annotations

import argparse
import logging
from contextlib import nullcontext
from pathlib import Path

from neo4j import GraphDatabase
from qdrant_client import QdrantClient

from gateway.config.settings import get_settings
from gateway.ingest.neo4j_writer import Neo4jWriter
from gateway.ingest.pipeline import IngestionConfig, IngestionPipeline
from gateway.ingest.qdrant_writer import QdrantWriter

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the ingestion CLI."""
    parser = argparse.ArgumentParser(description="Knowledge gateway ingestion commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rebuild_parser = subparsers.add_parser("rebuild", help="Trigger a full ingestion run")
    rebuild_parser.add_argument(
        "--profile",
        default="local",
        help="Ingestion profile to run (e.g., local, dev, prod)",
    )
    rebuild_parser.add_argument(
        "--repo",
        type=Path,
        help="Override repository path (defaults to KM_REPO_PATH)",
    )
    rebuild_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform discovery and chunking without writing to external services",
    )
    rebuild_parser.add_argument(
        "--dummy-embeddings",
        action="store_true",
        help="Use deterministic dummy embeddings (testing only)",
    )

    return parser


def rebuild(*, profile: str, repo: Path | None, dry_run: bool, dummy_embeddings: bool) -> None:
    """Execute a full ingestion pass."""

    settings = get_settings()
    repo_root = repo or settings.repo_root
    dry = dry_run or settings.dry_run
    use_dummy = dummy_embeddings or settings.ingest_use_dummy_embeddings

    qdrant_writer = None
    if not dry:
        qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        qdrant_writer = QdrantWriter(qdrant_client, settings.qdrant_collection)

    neo4j_writer = None
    driver = None
    if not dry:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        neo4j_writer = Neo4jWriter(driver)

    config = IngestionConfig(
        repo_root=repo_root,
        dry_run=dry,
        chunk_window=settings.ingest_window,
        chunk_overlap=settings.ingest_overlap,
        embedding_model=settings.embedding_model,
        use_dummy_embeddings=use_dummy,
        environment=profile,
    )

    pipeline = IngestionPipeline(qdrant_writer=qdrant_writer, neo4j_writer=neo4j_writer, config=config)

    try:
        if neo4j_writer and not dry:
            neo4j_writer.ensure_constraints()
        pipeline.run()
        logger.info("Ingestion run completed for profile=%s", profile)
    finally:
        if driver is not None:
            driver.close()


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    logging.basicConfig(level=logging.INFO)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "rebuild":
        rebuild(
            profile=args.profile,
            repo=args.repo,
            dry_run=args.dry_run,
            dummy_embeddings=args.dummy_embeddings,
        )
    else:  # pragma: no cover - safety fallback
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()
