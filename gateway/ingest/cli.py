from __future__ import annotations

import argparse
import logging
from pathlib import Path

from gateway.config.settings import get_settings
from gateway.observability.logging import configure_logging
from gateway.ingest.service import execute_ingestion

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
    result = execute_ingestion(
        settings=settings,
        profile=profile,
        repo_override=repo,
        dry_run=dry_run,
        use_dummy_embeddings=dummy_embeddings,
    )
    logger.info(
        "Ingestion run completed",
        extra={
            "profile": profile,
            "run_id": result.run_id,
            "chunk_count": result.chunk_count,
            "artifact_counts": result.artifact_counts,
        },
    )


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    configure_logging()
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
