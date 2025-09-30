from __future__ import annotations

import argparse
import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from gateway.config.settings import AppSettings, get_settings
from gateway.ingest.audit import AuditLogger
from gateway.ingest.service import execute_ingestion
from gateway.observability import configure_logging, configure_tracing

logger = logging.getLogger(__name__)
console = Console()


def _ensure_maintainer_scope(settings: AppSettings) -> None:
    if settings.auth_enabled and not settings.maintainer_token:
        raise SystemExit("Maintainer token (KM_ADMIN_TOKEN) required when auth is enabled")


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
    incremental_group = rebuild_parser.add_mutually_exclusive_group()
    incremental_group.add_argument(
        "--incremental",
        dest="incremental",
        action="store_true",
        help="Force incremental ingest even if disabled in configuration",
    )
    incremental_group.add_argument(
        "--full-rebuild",
        dest="incremental",
        action="store_false",
        help="Disable incremental ingest for this run",
    )
    rebuild_parser.set_defaults(incremental=None)

    history_parser = subparsers.add_parser(
        "audit-history",
        help="Show recent ingestion runs recorded in the audit ledger",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of recent runs to display (default: 20)",
    )
    history_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit raw JSON instead of a formatted table",
    )

    return parser


def rebuild(
    *,
    profile: str,
    repo: Path | None,
    dry_run: bool,
    dummy_embeddings: bool,
    incremental: bool | None,
    settings: AppSettings | None = None,
) -> None:
    """Execute a full ingestion pass."""

    if settings is None:
        settings = get_settings()
    _ensure_maintainer_scope(settings)
    result = execute_ingestion(
        settings=settings,
        profile=profile,
        repo_override=repo,
        dry_run=dry_run,
        use_dummy_embeddings=dummy_embeddings,
        incremental=incremental,
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


def audit_history(
    *,
    limit: int,
    output_json: bool,
    settings: AppSettings | None = None,
) -> None:
    """Display recent ingestion runs from the audit ledger."""

    if settings is None:
        settings = get_settings()
    _ensure_maintainer_scope(settings)
    audit_path = settings.state_path / "audit" / "audit.db"
    logger = AuditLogger(audit_path)
    entries = logger.recent(limit=limit)

    if output_json:
        console.print_json(data=entries)
        return

    if not entries:
        console.print("No audit history records found.", style="yellow")
        return

    console.print(_render_audit_table(entries))


def _render_audit_table(entries: Iterable[dict[str, object]]) -> Table:
    table = Table(title="Ingestion Audit History", show_lines=False)
    table.add_column("Run ID", overflow="fold")
    table.add_column("Profile")
    table.add_column("Started", style="cyan")
    table.add_column("Duration (s)", justify="right")
    table.add_column("Artifacts", justify="right")
    table.add_column("Chunks", justify="right")
    table.add_column("Success", justify="center")

    for entry in entries:
        started = _format_timestamp(entry.get("started_at"))
        duration = f"{float(entry.get('duration_seconds', 0.0)):.2f}"
        artifact_count = str(int(entry.get("artifact_count", 0)))
        chunk_count = str(int(entry.get("chunk_count", 0)))
        success = "✅" if entry.get("success") else "❌"
        table.add_row(
            str(entry.get("run_id", "-")),
            str(entry.get("profile", "-")),
            started,
            duration,
            artifact_count,
            chunk_count,
            success,
        )
    return table


def _format_timestamp(raw: object) -> str:
    try:
        ts = float(raw)
    except (TypeError, ValueError):  # pragma: no cover - defensive guard
        return "-"
    return datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="seconds")


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    configure_logging()
    settings = get_settings()
    configure_tracing(None, settings)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "rebuild":
        rebuild(
            profile=args.profile,
            repo=args.repo,
            dry_run=args.dry_run,
            dummy_embeddings=args.dummy_embeddings,
            incremental=args.incremental,
            settings=settings,
        )
    elif args.command == "audit-history":
        audit_history(limit=args.limit, output_json=args.json, settings=settings)
    else:  # pragma: no cover - safety fallback
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()
