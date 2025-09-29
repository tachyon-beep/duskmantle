from __future__ import annotations

import argparse
import json
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
    header = f"Lifecycle Report ({payload.get('generated_at_iso', '-')})"
    console.print(f"[bold]{header}[/bold]")

    isolated = payload.get("isolated") or {}
    if isolated:
        table = Table(title="Isolated Graph Nodes", show_lines=False)
        table.add_column("Label")
        table.add_column("Entries", justify="right")
        for label, nodes in isolated.items():
            table.add_row(label, str(len(nodes)))
        console.print(table)
    else:
        console.print("No isolated nodes detected.", style="green")

    stale_docs = payload.get("stale_docs") or []
    if stale_docs:
        table = Table(title="Stale Design Docs", show_lines=False)
        table.add_column("Path")
        table.add_column("Subsystem")
        table.add_column("Last Commit")
        for entry in stale_docs:
            ts = entry.get("git_timestamp")
            ts_render = "-"
            if isinstance(ts, (int, float)) and ts > 0:
                ts_render = datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="seconds")
            table.add_row(str(entry.get("path")), str(entry.get("subsystem")), ts_render)
        console.print(table)
    else:
        console.print("No stale design docs beyond threshold.", style="green")

    missing_tests = payload.get("missing_tests") or []
    if missing_tests:
        table = Table(title="Subsystems Missing Tests", show_lines=False)
        table.add_column("Subsystem")
        table.add_column("Source Files", justify="right")
        table.add_column("Test Cases", justify="right")
        for entry in missing_tests:
            table.add_row(
                str(entry.get("subsystem")),
                str(entry.get("source_files", 0)),
                str(entry.get("test_cases", 0)),
            )
        console.print(table)
    else:
        console.print("All subsystems with source files have test coverage.", style="green")


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
