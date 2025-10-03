"""Repository discovery helpers for ingestion pipeline."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli as tomllib  # type: ignore

from gateway.ingest.artifacts import Artifact
from gateway.ingest.symbols import SymbolRecord, extract_symbols

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

_MESSAGE_PATTERN = re.compile(r"[A-Z]\w*Message")
_TELEMETRY_PATTERN = re.compile(r"Telemetry\w+")


@dataclass(slots=True)
class DiscoveryConfig:
    """Runtime knobs influencing which artifacts are discovered."""

    repo_root: Path
    include_patterns: tuple[str, ...] = (
        "docs",
        "src",
        "tests",
        ".codacy",
    )
    symbols_enabled: bool = False


_SUBSYSTEM_METADATA_CACHE: dict[Path, dict[str, Any]] = {}
_SOURCE_PREFIX_CACHE: dict[Path, list[tuple[str, ...]]] = {}


def discover(config: DiscoveryConfig) -> Iterable[Artifact]:
    """Yield textual artifacts from the repository."""

    repo_root = config.repo_root
    if not repo_root.exists():
        raise FileNotFoundError(f"Repository root {repo_root} does not exist")

    subsystem_catalog = _load_subsystem_catalog(repo_root)
    source_prefixes = _detect_source_prefixes(repo_root)

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

        relative_path = path.relative_to(repo_root)
        artifact_type = _infer_artifact_type(path, repo_root)
        inferred_subsystem = _infer_subsystem(path, repo_root, source_prefixes)
        catalog_entry = None
        if inferred_subsystem:
            catalog_entry = subsystem_catalog.get(inferred_subsystem.lower())
        if catalog_entry is None:
            catalog_entry = _match_catalog_entry(path, repo_root, subsystem_catalog)

        if catalog_entry:
            subsystem_name = catalog_entry["name"]
            subsystem_meta = catalog_entry["metadata"]
        else:
            subsystem_name = _normalize_subsystem_name(inferred_subsystem) if inferred_subsystem else None
            subsystem_meta = {}

        git_commit, git_timestamp = _lookup_git_metadata(path, repo_root)

        extra: dict[str, Any] = {
            "message_entities": sorted(set(_MESSAGE_PATTERN.findall(content))),
            "telemetry_signals": sorted(set(_TELEMETRY_PATTERN.findall(content))),
            "subsystem_metadata": subsystem_meta,
            "subsystem_criticality": subsystem_meta.get("criticality"),
        }

        if config.symbols_enabled:
            relative_path = path.relative_to(repo_root)
            symbols = _extract_symbols(relative_path, content)
            if symbols:
                symbol_payloads = [symbol.to_metadata(path=relative_path) for symbol in symbols]
                extra["symbols"] = symbol_payloads
                extra["symbol_count"] = len(symbol_payloads)
                extra["symbol_names"] = [item["qualified_name"] for item in symbol_payloads]
                extra["symbol_kinds"] = [item["kind"] for item in symbol_payloads]
                extra["symbol_languages"] = [item["language"] for item in symbol_payloads]
                extra["symbol_ids"] = [item["id"] for item in symbol_payloads]

        yield Artifact(
            path=relative_path,
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
    if parts[0] == "src":
        if "_generated" in parts:
            return "proto"
        return "code"
    if parts[0] == ".codacy":
        return "config"
    return "other"


def _lookup_git_metadata(path: Path, repo_root: Path) -> tuple[str | None, int | None]:
    rel = path.relative_to(repo_root).as_posix()
    try:
        commit = (
            subprocess.check_output(
                ["git", "log", "-n", "1", "--pretty=%H", "--", rel],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            or None
        )
        timestamp_raw = (
            subprocess.check_output(
                ["git", "log", "-n", "1", "--pretty=%ct", "--", rel],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            or None
        )
        timestamp = int(timestamp_raw) if timestamp_raw else None
        return commit, timestamp
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        logger.debug("Git metadata unavailable for %s", rel)
        return None, None


def _extract_symbols(path: Path, content: str) -> list[SymbolRecord]:
    try:
        return extract_symbols(path, content)
    except Exception:  # pragma: no cover - defensive guard
        logger.debug("Failed to extract symbols for %s", path, exc_info=True)
        return []


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
                    catalog = {}
                    for key, value in data.items():
                        lower_key = str(key).lower()
                        name = key if isinstance(key, str) else str(key)
                        metadata = value if isinstance(value, dict) else {}
                        catalog[lower_key] = {"name": name, "metadata": metadata}
                break
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to parse subsystem metadata file %s", candidate)
    _SUBSYSTEM_METADATA_CACHE[root] = catalog
    return catalog


def _detect_source_prefixes(repo_root: Path) -> list[tuple[str, ...]]:
    """Infer source package prefixes (e.g. ``("src", "gateway")``)."""

    root = repo_root.resolve()
    if root in _SOURCE_PREFIX_CACHE:
        return _SOURCE_PREFIX_CACHE[root]

    prefixes: set[tuple[str, ...]] = set()
    _collect_pyproject_prefixes(root, prefixes)
    _collect_src_directory_prefixes(root, prefixes)
    prefixes.add(("src",))

    resolved = sorted(prefixes)
    _SOURCE_PREFIX_CACHE[root] = resolved
    return resolved


def _collect_pyproject_prefixes(root: Path, prefixes: set[tuple[str, ...]]) -> None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return

    data = _load_pyproject(pyproject)
    if not isinstance(data, Mapping):
        return

    tool_cfg = data.get("tool", {}) if isinstance(data, Mapping) else {}
    if isinstance(tool_cfg, Mapping):
        _collect_poetry_prefixes(tool_cfg, prefixes)
        _collect_setuptools_prefixes(tool_cfg, prefixes)

    project_cfg = data.get("project") if isinstance(data, Mapping) else None
    if isinstance(project_cfg, Mapping):
        _collect_project_prefixes(project_cfg, prefixes)


def _load_pyproject(path: Path) -> Mapping[str, Any] | dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:  # pragma: no cover - defensive
        logger.debug("Failed to parse pyproject.toml: %s", exc)
        return {}


def _collect_poetry_prefixes(tool_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None:
    poetry_cfg = tool_cfg.get("poetry")
    if not isinstance(poetry_cfg, Mapping):
        return

    packages = poetry_cfg.get("packages")
    if isinstance(packages, list):
        for entry in packages:
            if isinstance(entry, Mapping):
                _add_prefix(prefixes, entry.get("include"), entry.get("from", "src"))
        return

    _add_prefix(prefixes, poetry_cfg.get("name"))


def _collect_project_prefixes(project_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None:
    packages = project_cfg.get("packages")
    if isinstance(packages, list):
        for entry in packages:
            if isinstance(entry, Mapping):
                include = entry.get("include") or entry.get("name")
                _add_prefix(prefixes, include, entry.get("from", "src"))
        return

    _add_prefix(prefixes, project_cfg.get("name"))


def _collect_setuptools_prefixes(tool_cfg: Mapping[str, Any], prefixes: set[tuple[str, ...]]) -> None:
    setuptools_cfg = tool_cfg.get("setuptools")
    if not isinstance(setuptools_cfg, Mapping):
        return

    packages_cfg = setuptools_cfg.get("packages")
    if not isinstance(packages_cfg, Mapping):
        return

    find_cfg = packages_cfg.get("find")
    if not isinstance(find_cfg, Mapping):
        return

    includes = _ensure_str_list(find_cfg.get("include"))
    wheres = _ensure_str_list(find_cfg.get("where", "src")) or ["src"]

    for include in includes:
        for where in wheres:
            _add_prefix(prefixes, include, where)


def _collect_src_directory_prefixes(root: Path, prefixes: set[tuple[str, ...]]) -> None:
    src_dir = root / "src"
    if not src_dir.exists():
        return
    for child in src_dir.iterdir():
        if child.is_dir():
            prefixes.add(("src", child.name))


def _add_prefix(prefixes: set[tuple[str, ...]], include: str | None, base: str | None = "src") -> None:
    if not include:
        return
    include = include.strip()
    if not include or include == "*":
        return
    include = include.replace(".", "/").replace("-", "_")
    base_normalized = (base or "").strip()
    path = Path(base_normalized) / include if base_normalized else Path(include)
    parts = tuple(part for part in path.parts if part)
    if parts:
        prefixes.add(parts)


def _ensure_str_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _infer_subsystem(path: Path, repo_root: Path, source_prefixes: list[tuple[str, ...]]) -> str | None:
    rel_parts = path.relative_to(repo_root).parts
    if not rel_parts:
        return None

    best_match: tuple[str, ...] | None = None
    best_len = 0
    for prefix in source_prefixes:
        if len(rel_parts) < len(prefix):
            continue
        if tuple(rel_parts[: len(prefix)]) == prefix and len(prefix) > best_len:
            best_match = prefix
            best_len = len(prefix)

    if best_match:
        remainder = rel_parts[len(best_match) :]
        if remainder:
            return remainder[0]
        return best_match[-1]

    if rel_parts[0] == "src" and len(rel_parts) > 1:
        return rel_parts[1]

    return None


def _normalize_subsystem_name(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text.islower():
        return text.capitalize()
    return text


def _match_catalog_entry(path: Path, repo_root: Path, catalog: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not catalog:
        return None
    rel_posix = path.relative_to(repo_root).as_posix()
    for entry in catalog.values():
        metadata = entry.get("metadata", {})
        if not isinstance(metadata, Mapping):
            continue
        if any(_pattern_matches(rel_posix, pattern) for pattern in _iter_metadata_patterns(metadata)):
            return entry
    return None


def _iter_metadata_patterns(metadata: Mapping[str, Any]) -> Iterable[str]:
    raw_patterns = metadata.get("paths") or metadata.get("includes") or []
    candidates: Iterable[object]
    if isinstance(raw_patterns, str):
        candidates = [raw_patterns]
    elif isinstance(raw_patterns, (list, tuple, set)):
        candidates = raw_patterns
    else:
        return []

    cleaned: list[str] = []
    for pattern in candidates:
        if not isinstance(pattern, str):
            continue
        stripped = pattern.strip()
        if stripped:
            cleaned.append(stripped)
    return cleaned


def _pattern_matches(target: str, pattern: str) -> bool:
    base = pattern.rstrip("*/")
    if base and target.startswith(base):
        return True
    return fnmatch(target, pattern)


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
