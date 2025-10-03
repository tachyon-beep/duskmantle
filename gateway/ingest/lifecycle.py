"""Lifecycle reporting helpers for ingestion outputs."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from neo4j import Driver

from gateway.graph import GraphService, get_graph_service
from gateway.ingest.pipeline import IngestionResult
from gateway.observability.metrics import (
    LIFECYCLE_HISTORY_SNAPSHOTS,
    LIFECYCLE_ISOLATED_NODES_TOTAL,
    LIFECYCLE_LAST_RUN_STATUS,
    LIFECYCLE_LAST_RUN_TIMESTAMP,
    LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL,
    LIFECYCLE_REMOVED_ARTIFACTS_TOTAL,
    LIFECYCLE_STALE_DOCS_TOTAL,
)

SECONDS_PER_DAY = 60 * 60 * 24


@dataclass(slots=True)
class LifecycleConfig:
    """Configuration values that influence lifecycle report generation."""

    output_path: Path
    stale_days: int
    graph_enabled: bool
    history_limit: int | None = None


def write_lifecycle_report(
    result: IngestionResult,
    *,
    config: LifecycleConfig,
    graph_service: GraphService | None,
) -> None:
    """Persist lifecycle insights derived from the most recent ingest run."""

    output_path = config.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = time.time()
    generated_at_iso = datetime.fromtimestamp(generated_at, tz=UTC).isoformat()

    isolated = _fetch_isolated_nodes(graph_service) if config.graph_enabled else {}
    stale_docs = _find_stale_docs(result.artifacts, config.stale_days, generated_at)
    missing_tests = _find_missing_tests(result.artifacts)
    removed_artifacts = list(result.removed_artifacts)
    symbol_tests, symbol_test_gaps = _compute_symbol_test_coverage(result.artifacts)

    counts = _lifecycle_counts(
        isolated=isolated,
        stale_docs=stale_docs,
        missing_tests=missing_tests,
        removed=removed_artifacts,
        symbol_tests=symbol_tests,
        symbol_test_gaps=symbol_test_gaps,
    )

    payload = {
        "generated_at": generated_at,
        "generated_at_iso": generated_at_iso,
        "run": {
            "run_id": result.run_id,
            "profile": result.profile,
            "repo_head": result.repo_head,
        },
        "thresholds": {
            "stale_days": config.stale_days,
        },
        "isolated": isolated,
        "stale_docs": stale_docs,
        "missing_tests": missing_tests,
        "removed_artifacts": removed_artifacts,
        "symbol_tests": symbol_tests,
        "symbol_test_gaps": symbol_test_gaps,
        "summary": counts,
    }

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    snapshots: list[Path] = []
    history_limit = config.history_limit or 0
    if history_limit > 0:
        snapshots = _write_history_snapshot(payload, output_path.parent, history_limit)
    else:
        snapshots = []

    profile = result.profile
    LIFECYCLE_LAST_RUN_STATUS.labels(profile).set(1)
    LIFECYCLE_LAST_RUN_TIMESTAMP.labels(profile).set(generated_at)
    LIFECYCLE_STALE_DOCS_TOTAL.labels(profile).set(counts["stale_docs"])
    LIFECYCLE_ISOLATED_NODES_TOTAL.labels(profile).set(counts["isolated_nodes"])
    LIFECYCLE_MISSING_TEST_SUBSYSTEMS_TOTAL.labels(profile).set(counts["subsystems_missing_tests"])
    LIFECYCLE_REMOVED_ARTIFACTS_TOTAL.labels(profile).set(counts["removed_artifacts"])
    if history_limit > 0:
        LIFECYCLE_HISTORY_SNAPSHOTS.labels(profile).set(len(snapshots))
    else:
        LIFECYCLE_HISTORY_SNAPSHOTS.labels(profile).set(0)


def build_graph_service(*, driver: Driver, database: str, cache_ttl: float) -> GraphService:
    """Construct a graph service with sensible defaults for lifecycle usage."""
    return get_graph_service(driver, database, cache_ttl=cache_ttl, cache_max_entries=256)


def summarize_lifecycle(payload: dict[str, Any]) -> dict[str, Any]:
    """Produce a summarized view of lifecycle data for reporting."""
    counts = _lifecycle_counts(
        isolated=payload.get("isolated") or {},
        stale_docs=payload.get("stale_docs") or [],
        missing_tests=payload.get("missing_tests") or [],
        removed=payload.get("removed_artifacts") or [],
        symbol_tests=payload.get("symbol_tests") or [],
        symbol_test_gaps=payload.get("symbol_test_gaps") or [],
    )
    return {
        "generated_at": payload.get("generated_at"),
        "generated_at_iso": payload.get("generated_at_iso"),
        "counts": counts,
        "run": payload.get("run"),
        "thresholds": payload.get("thresholds"),
    }


def _fetch_isolated_nodes(graph_service: GraphService | None) -> dict[str, list[dict[str, Any]]]:
    """Collect isolated graph nodes grouped by label."""
    if graph_service is None:
        return {}

    labels = ["DesignDoc", "SourceFile", "TestCase", "IntegrationMessage"]
    isolated: dict[str, list[dict[str, Any]]] = {}

    for label in labels:
        nodes: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            page = graph_service.list_orphan_nodes(label=label, cursor=cursor, limit=200)
            nodes.extend(page["nodes"])
            cursor = page.get("cursor")
            if not cursor:
                break
        if nodes:
            isolated[label] = [
                {
                    "id": node.get("id"),
                    "path": node.get("properties", {}).get("path"),
                    "name": node.get("properties", {}).get("name"),
                }
                for node in nodes
            ]
    return isolated


def _find_stale_docs(artifacts: Iterable[dict[str, Any]], stale_days: int, now: float) -> list[dict[str, Any]]:
    """Identify design documents that are older than the stale threshold."""
    cutoff = now - max(0, stale_days) * SECONDS_PER_DAY
    stale: list[dict[str, Any]] = []
    for artifact in artifacts:
        if artifact.get("artifact_type") != "DesignDoc":
            continue
        ts = _coerce_float(artifact.get("git_timestamp"))
        if ts is None:
            continue
        if 0 < ts < cutoff:
            stale.append(
                {
                    "path": artifact.get("path"),
                    "subsystem": artifact.get("subsystem"),
                    "git_timestamp": ts,
                }
            )
    return stale


def _find_missing_tests(artifacts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Determine subsystems lacking corresponding tests."""
    per_subsystem: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for artifact in artifacts:
        subsystem = artifact.get("subsystem") or "unknown"
        artifact_type = str(artifact.get("artifact_type") or "unknown")
        per_subsystem[subsystem][artifact_type] += 1

    missing: list[dict[str, Any]] = []
    for subsystem, counts in per_subsystem.items():
        sources = counts.get("SourceFile", 0)
        tests = counts.get("TestCase", 0)
        if sources > 0 and tests == 0:
            missing.append(
                {
                    "subsystem": subsystem,
                    "source_files": sources,
                    "test_cases": tests,
                }
            )
    return missing


def _compute_symbol_test_coverage(artifacts: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Derive symbol test coverage from ingestion artifact metadata."""

    symbol_index: dict[str, dict[str, Any]] = {}
    coverage: dict[str, list[str]] = defaultdict(list)

    for artifact in artifacts:
        artifact_type = str(artifact.get("artifact_type") or "").lower()
        path = str(artifact.get("path") or "")
        if artifact_type in {"code", "sourcefile"}:
            symbols = artifact.get("symbols")
            if not isinstance(symbols, list):
                continue
            for entry in symbols:
                if not isinstance(entry, dict):
                    continue
                symbol_id = entry.get("id")
                if not symbol_id:
                    continue
                qualified = (entry.get("qualified_name") or entry.get("name") or "").strip()
                name = (entry.get("name") or qualified.split(".")[-1]).strip()
                symbol_index[str(symbol_id)] = {
                    "symbol_id": str(symbol_id),
                    "qualified_name": qualified,
                    "name": name,
                    "source_path": path,
                }
        elif artifact_type in {"test", "testcase"}:
            exercised = artifact.get("exercises_symbols")
            if not isinstance(exercised, list):
                continue
            for symbol_id in exercised:
                if not symbol_id:
                    continue
                coverage[str(symbol_id)].append(path)

    symbol_tests: list[dict[str, Any]] = []
    symbol_gaps: list[dict[str, Any]] = []

    for symbol_id, info in symbol_index.items():
        tests = sorted({test_path for test_path in coverage.get(symbol_id, []) if test_path})
        entry = {
            "symbol_id": symbol_id,
            "qualified_name": info.get("qualified_name"),
            "name": info.get("name"),
            "source_path": info.get("source_path"),
        }
        if tests:
            entry_with_tests = dict(entry)
            entry_with_tests["tests"] = tests
            entry_with_tests["status"] = "Covered"
            symbol_tests.append(entry_with_tests)
        else:
            entry_missing = dict(entry)
            entry_missing["status"] = "Missing"
            symbol_gaps.append(entry_missing)

    for symbol_id, tests in coverage.items():
        if symbol_id in symbol_index:
            continue
        cleaned = sorted({test_path for test_path in tests if test_path})
        if not cleaned:
            continue
        symbol_tests.append(
            {
                "symbol_id": symbol_id,
                "qualified_name": symbol_id.split("::")[-1],
                "name": symbol_id.split("::")[-1],
                "source_path": symbol_id.split("::")[0],
                "tests": cleaned,
                "status": "Covered",
            }
        )

    symbol_tests.sort(key=lambda item: (item.get("source_path") or "", item.get("qualified_name") or ""))
    symbol_gaps.sort(key=lambda item: (item.get("source_path") or "", item.get("qualified_name") or ""))
    return symbol_tests, symbol_gaps


def _write_history_snapshot(payload: dict[str, Any], reports_dir: Path, history_limit: int) -> list[Path]:
    """Write lifecycle history to disk while enforcing retention."""
    history_dir = reports_dir / "lifecycle_history"
    history_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%f")
    history_path = history_dir / f"lifecycle_{timestamp}.json"
    history_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    snapshots = sorted(history_dir.glob("lifecycle_*.json"), key=lambda path: path.stat().st_mtime)
    if len(snapshots) <= history_limit:
        return snapshots

    for old_path in snapshots[0 : len(snapshots) - history_limit]:
        with suppress(FileNotFoundError):
            old_path.unlink()
    return sorted(history_dir.glob("lifecycle_*.json"), key=lambda path: path.stat().st_mtime)


def _coerce_float(value: object) -> float | None:
    """Coerce numeric-like values to float when possible."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _lifecycle_counts(
    *,
    isolated: dict[str, list[dict[str, Any]]],
    stale_docs: list[dict[str, Any]],
    missing_tests: list[dict[str, Any]],
    removed: list[dict[str, Any]],
    symbol_tests: list[dict[str, Any]] | None = None,
    symbol_test_gaps: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Aggregate lifecycle metrics into counters."""
    isolated_count = sum(len(entries) for entries in isolated.values())
    return {
        "stale_docs": len(stale_docs),
        "isolated_nodes": isolated_count,
        "subsystems_missing_tests": len(missing_tests),
        "removed_artifacts": len(removed),
        "symbol_tests": len(symbol_tests or []),
        "symbol_test_gaps": len(symbol_test_gaps or []),
    }
