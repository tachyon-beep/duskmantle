from __future__ import annotations

import json
import time
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from neo4j import Driver

from gateway.graph import GraphService, get_graph_service
from gateway.ingest.pipeline import IngestionResult

SECONDS_PER_DAY = 60 * 60 * 24


@dataclass(slots=True)
class LifecycleConfig:
    output_path: Path
    stale_days: int
    graph_enabled: bool


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
    }

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_graph_service(*, driver: Driver, database: str, cache_ttl: float) -> GraphService:
    return get_graph_service(driver, database, cache_ttl=cache_ttl, cache_max_entries=256)


def _fetch_isolated_nodes(graph_service: GraphService | None) -> dict[str, list[dict[str, Any]]]:
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
    cutoff = now - max(0, stale_days) * SECONDS_PER_DAY
    stale: list[dict[str, Any]] = []
    for artifact in artifacts:
        if artifact.get("artifact_type") != "DesignDoc":
            continue
        timestamp = artifact.get("git_timestamp")
        try:
            ts = float(timestamp)
        except (TypeError, ValueError):
            continue
        if ts > 0 and ts < cutoff:
            stale.append(
                {
                    "path": artifact.get("path"),
                    "subsystem": artifact.get("subsystem"),
                    "git_timestamp": ts,
                }
            )
    return stale


def _find_missing_tests(artifacts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
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
