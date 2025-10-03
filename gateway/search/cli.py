"""Command-line helpers for search training, exports, and maintenance."""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from gateway.config.settings import AppSettings, get_settings
from gateway.observability import configure_logging, configure_tracing
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


def main(argv: list[str] | None = None) -> None:
    """Entry point for the `gateway-search` command-line interface."""
    configure_logging()
    settings = get_settings()
    configure_tracing(None, settings)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export-training-data":
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
