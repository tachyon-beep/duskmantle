"""Command-line utilities for managing the Neo4j graph schema."""

from __future__ import annotations

import argparse
import logging

from neo4j import GraphDatabase

from gateway.config.settings import get_settings
from gateway.graph.migrations import MigrationRunner

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser for graph administration commands."""
    parser = argparse.ArgumentParser(description="Graph administration commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    migrate_parser = subparsers.add_parser("migrate", help="Run Neo4j schema migrations")
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show migrations that would run without executing them",
    )

    return parser


def run_migrations(*, dry_run: bool = False) -> None:
    """Execute graph schema migrations, optionally printing the pending set."""
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        runner = MigrationRunner(driver=driver, database=settings.neo4j_database)
        if dry_run:
            pending = runner.pending_ids()
            if not pending:
                print("No pending migrations.")
            else:
                for migration_id in pending:
                    print(migration_id)
        else:
            runner.run()
    finally:
        driver.close()


def main(argv: list[str] | None = None) -> None:
    """Entrypoint for the `gateway-graph` command-line interface."""
    logging.basicConfig(level=logging.INFO)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "migrate":
        run_migrations(dry_run=args.dry_run)
    else:  # pragma: no cover - safety guard
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
