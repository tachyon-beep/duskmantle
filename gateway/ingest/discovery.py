from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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


def discover(config: DiscoveryConfig) -> Iterable[Artifact]:
    """Yield textual artifacts from the repository."""

    repo_root = config.repo_root
    if not repo_root.exists():
        raise FileNotFoundError(f"Repository root {repo_root} does not exist")

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
        subsystem = _infer_subsystem(path, repo_root)
        git_commit, git_timestamp = _lookup_git_metadata(path, repo_root)
        extra = {
            "leyline_entities": sorted(set(_LEYLINE_PATTERN.findall(content))),
            "telemetry_signals": sorted(set(_TELEMETRY_PATTERN.findall(content))),
        }

        yield Artifact(
            path=path.relative_to(repo_root),
            artifact_type=artifact_type,
            subsystem=subsystem,
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
