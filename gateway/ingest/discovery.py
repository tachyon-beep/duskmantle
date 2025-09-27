from __future__ import annotations

import json
import logging
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from gateway.ingest.artifacts import Artifact

logger = logging.getLogger(__name__)

_TEXTUAL_SUFFIXES = {
    ".md",
    ".txt",
    ".py",
    ".proto",
    ".yml",
    ".yaml",
    ".json",
    ".ini",
    ".cfg",
    ".toml",
    ".sql",
}

_SUBSYSTEM_PATTERN = re.compile(r"src/esper/(?P<subsystem>[^/]+)/")
_LEYLINE_PATTERN = re.compile(r"Leyline[A-Za-z0-9_]+")
_TELEMETRY_PATTERN = re.compile(r"Telemetry[A-Za-z0-9_]+")


@dataclass(slots=True)
class DiscoveryConfig:
    repo_root: Path
    include_patterns: tuple[str, ...] = (
        "docs",
        "src/esper",
        "tests",
        "src/esper/leyline/_generated",
        ".codacy",
    )


_SUBSYSTEM_METADATA_CACHE: dict[Path, dict[str, Any]] = {}


def discover(config: DiscoveryConfig) -> Iterable[Artifact]:
    """Yield textual artifacts from the repository."""

    repo_root = config.repo_root
    if not repo_root.exists():
        raise FileNotFoundError(f"Repository root {repo_root} does not exist")

    subsystem_catalog = _load_subsystem_catalog(repo_root)

    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if not _should_include(path, repo_root, config.include_patterns):
            continue
        if not _is_textual(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.debug("Skipping non-utf8 file %s", path)
            continue

        artifact_type = _infer_artifact_type(path, repo_root)
        inferred_subsystem = _infer_subsystem(path, repo_root)
        catalog_entry = None
        if inferred_subsystem:
            catalog_entry = subsystem_catalog.get(inferred_subsystem.lower())
        if catalog_entry is None:
            catalog_entry = _match_catalog_entry(path, repo_root, subsystem_catalog)

        if catalog_entry:
            subsystem_name = catalog_entry["name"]
            subsystem_meta = catalog_entry["metadata"]
        else:
            subsystem_name = inferred_subsystem.capitalize() if inferred_subsystem else None
            subsystem_meta = {}

        git_commit, git_timestamp = _lookup_git_metadata(path, repo_root)

        extra = {
            "leyline_entities": sorted(set(_LEYLINE_PATTERN.findall(content))),
            "telemetry_signals": sorted(set(_TELEMETRY_PATTERN.findall(content))),
            "subsystem_metadata": subsystem_meta,
            "subsystem_criticality": subsystem_meta.get("criticality"),
        }

        yield Artifact(
            path=path.relative_to(repo_root),
            artifact_type=artifact_type,
            subsystem=subsystem_name,
            content=content,
            git_commit=git_commit,
            git_timestamp=git_timestamp,
            extra_metadata=extra,
        )


def _should_include(path: Path, repo_root: Path, include_patterns: tuple[str, ...]) -> bool:
    rel = path.relative_to(repo_root)
    for pattern in include_patterns:
        if rel.as_posix().startswith(pattern):
            return True
    return False


def _is_textual(path: Path) -> bool:
    if path.suffix in _TEXTUAL_SUFFIXES:
        return True
    try:
        snippet = path.read_bytes()[:1024]
    except OSError:
        return False
    return b"\x00" not in snippet


def _infer_artifact_type(path: Path, repo_root: Path) -> str:
    rel = path.relative_to(repo_root)
    parts = rel.parts
    if parts[0] == "docs":
        return "doc"
    if parts[0] == "tests":
        return "test"
    if parts[0] == "src" and len(parts) > 1 and parts[1] == "esper":
        if "_generated" in parts:
            return "proto"
        return "code"
    if parts[0] == ".codacy":
        return "config"
    return "other"


def _infer_subsystem(path: Path, repo_root: Path) -> str | None:
    rel = path.relative_to(repo_root).as_posix()
    match = _SUBSYSTEM_PATTERN.search(rel)
    if match:
        subsystem = match.group("subsystem")
        # normalize capitalization e.g. kasmina -> Kasmina
        return subsystem.capitalize()
    return None


def _lookup_git_metadata(path: Path, repo_root: Path) -> tuple[str | None, int | None]:
    rel = path.relative_to(repo_root).as_posix()
    try:
        commit = (
            subprocess.check_output(
                ["git", "log", "-n", "1", "--pretty=%H", "--", rel],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            .strip()
            or None
        )
        timestamp_raw = (
            subprocess.check_output(
                ["git", "log", "-n", "1", "--pretty=%ct", "--", rel],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            .strip()
            or None
        )
        timestamp = int(timestamp_raw) if timestamp_raw else None
        return commit, timestamp
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        logger.debug("Git metadata unavailable for %s", rel)
        return None, None


def _load_subsystem_catalog(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    if root in _SUBSYSTEM_METADATA_CACHE:
        return _SUBSYSTEM_METADATA_CACHE[root]

    candidates = [
        root / ".metadata" / "subsystems.json",
        root / "docs" / "subsystems.json",
    ]
    catalog: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    catalog = {
                        str(key).lower(): {
                            "name": str(key) if isinstance(key, str) else str(key),
                            "metadata": value if isinstance(value, dict) else {},
                        }
                        for key, value in data.items()
                    }
                break
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to parse subsystem metadata file %s", candidate)
    _SUBSYSTEM_METADATA_CACHE[root] = catalog
    return catalog


def _match_catalog_entry(
    path: Path, repo_root: Path, catalog: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    if not catalog:
        return None
    rel_posix = path.relative_to(repo_root).as_posix()
    for entry in catalog.values():
        metadata = entry.get("metadata", {})
        patterns = metadata.get("paths") or metadata.get("includes") or []
        if not isinstance(patterns, (list, tuple, set)):
            continue
        for pattern in patterns:
            if not isinstance(pattern, str):
                continue
            cleaned = pattern.strip()
            if not cleaned:
                continue
            prefix_match = rel_posix.startswith(cleaned.rstrip("*/"))
            glob_match = fnmatch(rel_posix, cleaned)
            if prefix_match or glob_match:
                return entry
    return None


def dump_artifacts(artifacts: Iterable[Artifact]) -> str:
    """Serialize artifacts for debugging or dry-run output."""

    return json.dumps(
        [
            {
                "path": artifact.path.as_posix(),
                "artifact_type": artifact.artifact_type,
                "subsystem": artifact.subsystem,
                "git_commit": artifact.git_commit,
                "git_timestamp": artifact.git_timestamp,
                **artifact.extra_metadata,
            }
            for artifact in artifacts
        ],
        indent=2,
    )
