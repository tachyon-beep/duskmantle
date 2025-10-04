"""Command-line utilities for managing the Neo4j graph schema."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from typing import Any, Mapping

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

    tests_parser = subparsers.add_parser("tests-of", help="List tests associated with a symbol")
    tests_parser.add_argument(
        "symbol_id",
        help="Symbol identifier (e.g. src/service.py::handler)",
    )
    tests_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output (default: human-readable summary)",
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


def list_symbol_tests(symbol_id: str, *, json_output: bool) -> None:
    """List tests linked to a symbol via EXERCISES edges."""
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        with driver.session(database=settings.neo4j_database) as session:
            record = session.run(
                """
                MATCH (sym:Symbol {id: $symbol_id})
                OPTIONAL MATCH (t:TestCase)-[:EXERCISES]->(sym)
                RETURN sym, collect(t) AS tests
                """,
                symbol_id=symbol_id,
            ).single()
    finally:
        driver.close()

    if record is None or record.get("sym") is None:
        print(f"Symbol '{symbol_id}' not found", file=sys.stderr)
        raise SystemExit(1)

    symbol_node = record["sym"]
    raw_tests = record.get("tests") or []
    tests = [node for node in raw_tests if node is not None]

    payload = {
        "symbol": _serialize_node(symbol_node),
        "tests": [_serialize_node(node) for node in tests],
    }

    if json_output:
        print(json.dumps(payload, indent=2))
        return

    symbol_props = payload["symbol"].get("properties", {})
    qualifier = symbol_props.get("qualified_name") or symbol_props.get("name") or symbol_id
    print(f"Symbol: {qualifier}")
    if not payload["tests"]:
        print("No linked tests found.")
        return

    print("Tests:")
    for idx, test in enumerate(payload["tests"], 1):
        properties = test.get("properties", {})
        path = properties.get("path") or test.get("id")
        subsystem = properties.get("subsystem")
        line = f"  {idx}. {path}" if path else f"  {idx}. {test.get('id')}"
        if subsystem:
            line += f" [{subsystem}]"
        print(line)


def _serialize_node(node: Any) -> dict[str, Any]:
    """Serialise a Neo4j node into a JSON-friendly mapping."""
    if node is None:
        return {}
    labels = list(getattr(node, "labels", []))
    element_id = getattr(node, "element_id", None) or getattr(node, "id", None)
    try:
        properties = dict(node)
    except TypeError:  # pragma: no cover - defensive guard
        properties = {}
    return {
        "id": element_id,
        "labels": labels,
        "properties": properties,
    }




def main(argv: list[str] | None = None) -> None:
    """Entrypoint for the `gateway-graph` command-line interface."""
    logging.basicConfig(level=logging.INFO)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "migrate":
        run_migrations(dry_run=args.dry_run)
    elif args.command == "tests-of":
        list_symbol_tests(args.symbol_id, json_output=args.json)
    else:  # pragma: no cover - safety guard
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
