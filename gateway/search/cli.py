"""Command-line helpers for search training, exports, and maintenance."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from rich.console import Console

from gateway.config.settings import AppSettings, get_settings
from gateway.observability import configure_logging, configure_tracing
from gateway.mcp.client import GatewayClient
from gateway.mcp.config import MCPSettings
from gateway.mcp.exceptions import GatewayRequestError, MissingTokenError
from gateway.search.evaluation import evaluate_model
from gateway.search.exporter import (
    ExportOptions,
    discover_feedback_logs,
    export_feedback_logs,
    export_training_dataset,
)
from gateway.search.maintenance import PruneOptions, RedactOptions, prune_feedback_log, redact_dataset
from gateway.search.trainer import DatasetLoadError, save_artifact, train_from_dataset

logger = logging.getLogger(__name__)
console = Console()


def build_parser() -> argparse.ArgumentParser:
    """Return an argument parser covering all search CLI commands."""
    parser = argparse.ArgumentParser(description="Search tooling commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser(
        "export-training-data",
        help="Transform feedback telemetry into a training dataset",
    )
    export_parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Defaults to feedback/datasets/training-<timestamp>.csv",
    )
    export_parser.add_argument(
        "--format",
        choices=["csv", "jsonl"],
        default="csv",
        help="Output dataset format (default: csv)",
    )
    export_parser.add_argument(
        "--require-vote",
        action="store_true",
        help="Skip results without an explicit feedback vote",
    )
    export_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of rows to export",
    )
    export_parser.add_argument(
        "--include-rotations",
        action="store_true",
        help="Include rotated feedback logs (events.log.N) when exporting",
    )

    train_parser = subparsers.add_parser(
        "train-model",
        help="Fit a linear ranking model from a feedback dataset",
    )
    train_parser.add_argument(
        "dataset",
        type=Path,
        help="Path to the training dataset (CSV or JSONL)",
    )
    train_parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Defaults to feedback/models/model-<timestamp>.json",
    )

    prune_parser = subparsers.add_parser(
        "prune-feedback",
        help="Apply retention and pruning rules to the feedback log",
    )
    prune_parser.add_argument(
        "--max-age-days",
        type=int,
        help="Remove feedback requests older than the specified number of days",
    )
    prune_parser.add_argument(
        "--max-requests",
        type=int,
        help="Keep only the newest N feedback requests after age filtering",
    )
    prune_parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path (defaults to rewriting the existing events.log)",
    )

    redact_parser = subparsers.add_parser(
        "redact-dataset",
        help="Redact sensitive columns from an exported training dataset",
    )
    redact_parser.add_argument(
        "dataset",
        type=Path,
        help="Path to the dataset file (CSV or JSONL)",
    )
    redact_parser.add_argument(
        "--output",
        type=Path,
        help="Optional output dataset path (defaults to in-place)",
    )
    redact_parser.add_argument(
        "--drop-query",
        action="store_true",
        help="Blank the free-text query column",
    )
    redact_parser.add_argument(
        "--drop-context",
        action="store_true",
        help="Blank the serialized context payload",
    )
    redact_parser.add_argument(
        "--drop-note",
        action="store_true",
        help="Blank operator feedback notes",
    )

    evaluate_parser = subparsers.add_parser(
        "evaluate-model",
        help="Evaluate a trained model against a labelled dataset",
    )
    evaluate_parser.add_argument(
        "dataset",
        type=Path,
        help="Path to the evaluation dataset (CSV or JSONL)",
    )
    evaluate_parser.add_argument(
        "model",
        type=Path,
        help="Path to the model artifact JSON",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Execute a search query against the gateway API",
    )
    search_parser.add_argument("query", help="Search query text")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to return (default: 10, max: 25)",
    )
    search_parser.add_argument(
        "--symbol",
        action="append",
        dest="symbols",
        help="Symbol filter (repeatable or comma-separated)",
    )
    search_parser.add_argument(
        "--kind",
        action="append",
        dest="symbol_kinds",
        help="Symbol kind filter (repeatable or comma-separated)",
    )
    search_parser.add_argument(
        "--lang",
        action="append",
        dest="symbol_languages",
        help="Symbol language filter (repeatable or comma-separated)",
    )
    search_parser.add_argument(
        "--filters",
        help="Additional filters JSON payload to merge with flag-provided filters",
    )
    search_parser.add_argument(
        "--no-graph",
        action="store_true",
        help="Disable graph enrichment in responses (enabled by default)",
    )
    search_parser.add_argument(
        "--sort-by-vector",
        action="store_true",
        help="Sort strictly by vector score (otherwise hybrid scoring applies)",
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit raw JSON instead of a human-friendly summary",
    )

    subparsers.add_parser(
        "show-weights",
        help="Display the active search weight profile and resolved weights",
    )

    return parser


def export_training_data(
    *,
    output: Path | None,
    fmt: str,
    require_vote: bool,
    limit: int | None,
    include_rotations: bool,
    settings: AppSettings | None = None,
) -> None:
    """Materialise feedback events into a training dataset file."""
    if settings is None:
        settings = get_settings()
    feedback_dir = settings.state_path / "feedback"
    log_paths = (
        discover_feedback_logs(feedback_dir, include_rotations=include_rotations)
        if include_rotations
        else [feedback_dir / "events.log"]
    )
    existing_logs = [path for path in log_paths if path.exists()]
    if not existing_logs:
        target = feedback_dir / "events.log"
        console.print(f"No feedback events found at {target}", style="yellow")
        logger.warning("Feedback events log missing under %s (searched: %s)", feedback_dir, log_paths)
        return

    datasets_dir = feedback_dir / "datasets"
    if output is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        suffix = "jsonl" if fmt == "jsonl" else "csv"
        output = datasets_dir / f"training-{timestamp}.{suffix}"

    options = ExportOptions(
        output_path=output,
        output_format=fmt,  # type: ignore[arg-type]
        require_vote=require_vote,
        limit=limit,
    )
    stats = (
        export_feedback_logs(existing_logs, options=options)
        if include_rotations
        else export_training_dataset(existing_logs[0], options=options)
    )

    console.print(
        f"Export complete → {output} (wrote {stats.written_rows} rows from {stats.total_events} events; "
        f"skipped without vote: {stats.skipped_without_vote})",
        style="green",
    )
    logger.info(
        "Exported %d rows (total events %d, skipped without vote %d) to %s",
        stats.written_rows,
        stats.total_events,
        stats.skipped_without_vote,
        output,
    )


def train_model(
    *,
    dataset: Path,
    output: Path | None,
    settings: AppSettings,
) -> None:
    """Train a ranking model from a prepared dataset and save the artifact."""
    feedback_dir = settings.state_path / "feedback"
    models_dir = feedback_dir / "models"

    if output is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output = models_dir / f"model-{timestamp}.json"

    try:
        artifact = train_from_dataset(dataset)
    except DatasetLoadError as exc:
        console.print(f"Training failed: {exc}", style="red")
        logger.error("Training failed: %s", exc)
        return

    save_artifact(artifact, output)
    console.print(
        f"Model trained ({artifact.training_rows} rows, mse={artifact.metrics['mse']:.4f}, r2={artifact.metrics['r2']:.4f}) → {output}",
        style="green",
    )
    logger.info(
        "Model trained with %d rows; metrics=%s; artifact=%s",
        artifact.training_rows,
        artifact.metrics,
        output,
    )


def show_weights(*, settings: AppSettings) -> None:
    """Print the active search weight profile to the console."""
    profile, weights = settings.resolved_search_weights()
    console.print(f"Active profile: [bold]{profile}[/bold]")
    console.print(f"Slow graph warn threshold: {settings.search_warn_slow_graph_ms} ms")
    console.print("Weights:")
    for label, key in [
        ("Subsystem Affinity", "weight_subsystem"),
        ("Relationship Density", "weight_relationship"),
        ("Supporting Artifacts", "weight_support"),
        ("Coverage Penalty", "weight_coverage_penalty"),
        ("Subsystem Criticality", "weight_criticality"),
    ]:
        value = weights.get(key)
        console.print(f"  • {label}: {value:.3f}")


def prune_feedback(*, settings: AppSettings, max_age_days: int | None, max_requests: int | None, output: Path | None) -> None:
    """Trim feedback logs by age/request count and optionally archive removals."""
    feedback_dir = settings.state_path / "feedback"
    events_log = feedback_dir / "events.log"
    if not events_log.exists():
        console.print(f"No feedback events found at {events_log}", style="yellow")
        logger.warning("Feedback events log missing: %s", events_log)
        return

    options = PruneOptions(max_age_days=max_age_days, max_requests=max_requests, output_path=output)
    try:
        stats = prune_feedback_log(events_log, options=options)
    except (ValueError, FileNotFoundError) as exc:
        console.print(f"Prune failed: {exc}", style="red")
        logger.error("Prune failed: %s", exc)
        return

    console.print(
        f"Prune complete — retained {stats.retained_requests} of {stats.total_requests} requests (removed {stats.removed_requests})",
        style="green",
    )
    logger.info(
        "Prune complete: total=%d retained=%d removed=%d",
        stats.total_requests,
        stats.retained_requests,
        stats.removed_requests,
    )


def redact_training_dataset(
    *,
    dataset: Path,
    output: Path | None,
    drop_query: bool,
    drop_context: bool,
    drop_note: bool,
) -> None:
    """Strip sensitive fields and emit a sanitized dataset."""
    options = RedactOptions(output_path=output, drop_query=drop_query, drop_context=drop_context, drop_note=drop_note)
    try:
        stats = redact_dataset(dataset, options=options)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"Redaction failed: {exc}", style="red")
        logger.error("Redaction failed: %s", exc)
        return

    console.print(
        f"Redaction complete — processed {stats.total_rows} rows; redacted {stats.redacted_rows}",
        style="green",
    )
    logger.info(
        "Redaction complete: total_rows=%d redacted_rows=%d dataset=%s",
        stats.total_rows,
        stats.redacted_rows,
        output or dataset,
    )


def evaluate_trained_model(*, dataset: Path, model: Path) -> None:
    """Run offline evaluation of a trained model against a labelled dataset."""
    try:
        metrics = evaluate_model(dataset, model)
    except (DatasetLoadError, ValueError) as exc:
        console.print(f"Evaluation failed: {exc}", style="red")
        logger.error("Evaluation failed: %s", exc)
        return

    spearman_display = "n/a" if metrics.spearman is None else f"{metrics.spearman:.4f}"
    console.print(
        "Evaluation metrics:\n"
        f"  MSE: {metrics.mse:.4f}\n"
        f"  R²: {metrics.r2:.4f}\n"
        f"  NDCG@5: {metrics.ndcg_at_5:.4f}\n"
        f"  NDCG@10: {metrics.ndcg_at_10:.4f}\n"
        f"  Spearman: {spearman_display}",
        style="green",
    )
    logger.info(
        "Evaluation complete: mse=%.4f r2=%.4f ndcg5=%.4f ndcg10=%.4f spearman=%s",
        metrics.mse,
        metrics.r2,
        metrics.ndcg_at_5,
        metrics.ndcg_at_10,
        spearman_display,
    )


def command_search(args: argparse.Namespace) -> None:
    """Execute a search request against the gateway API."""
    filters = _load_filters(args.filters)

    symbol_terms = _collect_symbol_terms(args.symbols)
    if symbol_terms:
        _merge_symbol_filter(filters, symbol_terms)

    kind_terms = _collect_lower_terms(args.symbol_kinds)
    if kind_terms:
        _merge_lowercase_filter(filters, "symbol_kinds", kind_terms)

    language_terms = _collect_lower_terms(args.symbol_languages)
    if language_terms:
        _merge_lowercase_filter(filters, "symbol_languages", language_terms)

    payload: dict[str, Any] = {
        "query": args.query,
        "limit": max(1, min(args.limit, 25)),
        "include_graph": not args.no_graph,
    }
    if args.sort_by_vector:
        payload["sort_by_vector"] = True
    if filters:
        payload["filters"] = filters

    settings = MCPSettings()

    async def _execute() -> dict[str, Any]:
        async with GatewayClient(settings) as client:
            return await client.search(payload)

    try:
        result = asyncio.run(_execute())
    except MissingTokenError as exc:  # pragma: no cover - depends on env configuration
        console.print(f"Missing token: {exc}", style="red")
        raise SystemExit(1) from exc
    except GatewayRequestError as exc:  # pragma: no cover - network path
        detail = exc.detail or "gateway request failed"
        console.print(f"Search failed ({exc.status_code}): {detail}", style="red")
        payload = getattr(exc, "payload", None)
        if payload:
            try:
                console.print_json(data=payload)
            except Exception:  # pragma: no cover - defensive
                console.print(str(payload))
        raise SystemExit(1) from exc
    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"Search failed: {exc}", style="red")
        raise SystemExit(1) from exc

    if args.json:
        console.print_json(data=result)
    else:
        _render_search_results(result)


def _load_filters(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        console.print(f"Invalid filters JSON: {exc}", style="red")
        raise SystemExit(1) from exc
    if not isinstance(data, dict):
        console.print("Filters payload must be a JSON object", style="red")
        raise SystemExit(1)
    return dict(data)


def _collect_symbol_terms(values: list[str] | None) -> list[str]:
    if not values:
        return []
    terms: list[str] = []
    seen: set[str] = set()
    for raw in values:
        for part in str(raw).split(","):
            term = part.strip()
            if not term:
                continue
            key = term.lower()
            if key in seen:
                continue
            seen.add(key)
            terms.append(term)
    return terms


def _collect_lower_terms(values: list[str] | None) -> list[str]:
    if not values:
        return []
    terms: list[str] = []
    seen: set[str] = set()
    for raw in values:
        for part in str(raw).split(","):
            term = part.strip().lower()
            if not term or term in seen:
                continue
            seen.add(term)
            terms.append(term)
    return terms


def _merge_symbol_filter(filters: dict[str, Any], additions: list[str]) -> None:
    existing = filters.get("symbols")
    merged: list[str] = []
    seen: set[str] = set()
    if isinstance(existing, list):
        for value in existing:
            text = str(value).strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(text)
    for value in additions:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(value)
    filters["symbols"] = merged


def _merge_lowercase_filter(filters: dict[str, Any], key: str, additions: list[str]) -> None:
    existing = filters.get(key)
    merged: list[str] = []
    seen: set[str] = set()
    if isinstance(existing, list):
        for value in existing:
            text = str(value).strip().lower()
            if not text or text in seen:
                continue
            seen.add(text)
            merged.append(text)
    for value in additions:
        if value in seen:
            continue
        seen.add(value)
        merged.append(value)
    filters[key] = merged


def _render_search_results(result: Mapping[str, Any]) -> None:
    request_id = result.get("request_id") if isinstance(result, Mapping) else None
    if request_id:
        console.print(f"Request ID: {request_id}")

    hits = []
    if isinstance(result, Mapping):
        raw_hits = result.get("results")
        if isinstance(raw_hits, list):
            hits = raw_hits

    console.print(f"[bold]{len(hits)} result(s)[/bold]")
    for idx, entry in enumerate(hits, 1):
        if not isinstance(entry, Mapping):
            continue
        chunk = entry.get("chunk")
        if not isinstance(chunk, Mapping):
            chunk = {}
        score_info = entry.get("score")
        combined_score = None
        if isinstance(score_info, Mapping):
            combined_score = score_info.get("combined")
        path = (
            chunk.get("path")
            or chunk.get("artifact_path")
            or (chunk.get("metadata") or {}).get("path")
        )
        console.print(f"[bold]{idx}. {path or 'unknown path'}[/bold]")
        if combined_score is not None:
            console.print(f"   combined score: {combined_score}")
        snippet = chunk.get("snippet") or chunk.get("text")
        if isinstance(snippet, str) and snippet.strip():
            preview_line = snippet.strip().splitlines()[0][:160]
            console.print(f"   snippet: {preview_line}")
        symbols = chunk.get("symbols")
        if isinstance(symbols, list) and symbols:
            first = symbols[0]
            if isinstance(first, Mapping):
                qualifier = first.get("qualified_name") or first.get("name")
                kind = first.get("kind")
                language = first.get("language")
                console.print(
                    "   symbol: {qual} ({kind}/{lang})".format(
                        qual=qualifier or "?",
                        kind=kind or "?",
                        lang=language or "?",
                    )
                )

def main(argv: list[str] | None = None) -> None:
    """Entry point for the `gateway-search` command-line interface."""
    configure_logging()
    settings = get_settings()
    configure_tracing(None, settings)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "search":
        command_search(args)
    elif args.command == "export-training-data":
        export_training_data(
            output=args.output,
            fmt=args.format,
            require_vote=args.require_vote,
            limit=args.limit,
            include_rotations=args.include_rotations,
            settings=settings,
        )
    elif args.command == "train-model":
        train_model(
            dataset=args.dataset,
            output=args.output,
            settings=settings,
        )
    elif args.command == "prune-feedback":
        prune_feedback(
            settings=settings,
            max_age_days=args.max_age_days,
            max_requests=args.max_requests,
            output=args.output,
        )
    elif args.command == "redact-dataset":
        if not any([args.drop_query, args.drop_context, args.drop_note]):
            console.print("Nothing to redact — supply at least one drop flag", style="yellow")
            return
        redact_training_dataset(
            dataset=args.dataset,
            output=args.output,
            drop_query=args.drop_query,
            drop_context=args.drop_context,
            drop_note=args.drop_note,
        )
    elif args.command == "evaluate-model":
        evaluate_trained_model(dataset=args.dataset, model=args.model)
    elif args.command == "show-weights":
        show_weights(settings=settings)
    else:  # pragma: no cover
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()
