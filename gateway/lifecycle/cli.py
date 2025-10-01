from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from gateway.config.settings import get_settings
from gateway.observability import configure_logging, configure_tracing

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lifecycle health reporting")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit raw JSON payload",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        help="Override lifecycle report path (defaults to state_path/reports/lifecycle_report.json)",
    )
    return parser


def render_table(payload: dict[str, object]) -> None:
    generated = payload.get("generated_at_iso", "-")
    header = f"Lifecycle Report ({generated})"
    console.print(f"[bold]{header}[/bold]")

    _render_isolated_nodes(payload.get("isolated"))
    _render_stale_docs(payload.get("stale_docs"))
    _render_missing_tests(payload.get("missing_tests"))


def _render_isolated_nodes(value: object) -> None:
    isolated = value if isinstance(value, Mapping) else {}
    if not isolated:
        console.print("No isolated nodes detected.", style="green")
        return

    table = Table(title="Isolated Graph Nodes", show_lines=False)
    table.add_column("Label")
    table.add_column("Entries", justify="right")
    for label, nodes in isolated.items():
        if isinstance(label, str) and isinstance(nodes, Iterable):
            table.add_row(label, str(sum(1 for _ in nodes)))
    console.print(table)


def _render_stale_docs(value: object) -> None:
    docs = value if isinstance(value, list) else []
    rows = [entry for entry in docs if isinstance(entry, Mapping)]
    if not rows:
        console.print("No stale design docs beyond threshold.", style="green")
        return

    table = Table(title="Stale Design Docs", show_lines=False)
    table.add_column("Path")
    table.add_column("Subsystem")
    table.add_column("Last Commit")
    for entry in rows:
        table.add_row(
            str(entry.get("path")),
            str(entry.get("subsystem")),
            _format_timestamp(entry.get("git_timestamp")),
        )
    console.print(table)


def _render_missing_tests(value: object) -> None:
    candidates = value if isinstance(value, list) else []
    rows = [entry for entry in candidates if isinstance(entry, Mapping)]
    if not rows:
        console.print("All subsystems with source files have test coverage.", style="green")
        return

    table = Table(title="Subsystems Missing Tests", show_lines=False)
    table.add_column("Subsystem")
    table.add_column("Source Files", justify="right")
    table.add_column("Test Cases", justify="right")
    for entry in rows:
        table.add_row(
            str(entry.get("subsystem")),
            str(entry.get("source_files", 0)),
            str(entry.get("test_cases", 0)),
        )
    console.print(table)


def _format_timestamp(value: object) -> str:
    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value).isoformat(sep=" ", timespec="seconds")
    return "-"


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    settings = get_settings()
    configure_tracing(None, settings)

    parser = build_parser()
    args = parser.parse_args(argv)
    report_path = args.report_path or settings.state_path / "reports" / "lifecycle_report.json"
    if not report_path.exists():
        console.print(f"Lifecycle report not found at {report_path}", style="red")
        raise SystemExit(1)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if args.json:
        console.print_json(data=payload)
        return
    render_table(payload)


if __name__ == "__main__":  # pragma: no cover
    main()
