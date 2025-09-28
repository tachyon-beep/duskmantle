"""Shared helpers for MCP content management."""

from __future__ import annotations

import os
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {".md", ".docx", ".txt", ".doc", ".pdf"}


@dataclass(slots=True)
class DocumentCopyResult:
    """Result of an attempted document copy."""

    source: Path
    destination: Path
    copied: bool
    overwritten: bool = False
    reason: str | None = None


class DocumentCopyError(Exception):
    """Raised when a copy operation fails fatally."""


_SLUG_REGEX = re.compile(r"[^a-z0-9]+")


def slugify(value: str, *, fallback: str = "document") -> str:
    """Create a filesystem-friendly slug."""

    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    slug = _SLUG_REGEX.sub("-", normalized).strip("-")
    return slug or fallback


def is_supported_document(path: Path) -> bool:
    """Return ``True`` if the path has a supported document extension."""

    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def _assert_within_root(root: Path, candidate: Path) -> None:
    """Ensure ``candidate`` is within ``root`` to prevent path traversal."""

    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    if os.name == "nt":
        root_str = str(root_resolved).lower()
        candidate_str = str(candidate_resolved).lower()
    else:
        root_str = str(root_resolved)
        candidate_str = str(candidate_resolved)
    if not candidate_str.startswith(root_str.rstrip(os.sep) + os.sep) and candidate_resolved != root_resolved:
        raise DocumentCopyError(f"Destination {candidate} escapes root {root}")


def sweep_documents(
    root: Path,
    target: Path,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> Iterable[DocumentCopyResult]:
    """Copy supported documents under ``root`` into ``target``."""

    if not root.exists():
        raise FileNotFoundError(f"Source directory {root} does not exist")

    target_root = (root / target).resolve()
    results: list[DocumentCopyResult] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if not is_supported_document(path):
            continue

        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if not rel.parts:
            continue
        if rel.parts[0] == target.parts[0]:
            continue

        destination = (target_root / rel).resolve()
        try:
            _assert_within_root(root, destination)
        except DocumentCopyError as exc:
            results.append(
                DocumentCopyResult(
                    source=path,
                    destination=destination,
                    copied=False,
                    reason=str(exc),
                )
            )
            continue

        if dry_run:
            results.append(
                DocumentCopyResult(
                    source=path,
                    destination=destination,
                    copied=False,
                    reason="dry-run",
                )
            )
            continue

        existed = destination.exists()
        if existed and not overwrite:
            results.append(
                DocumentCopyResult(
                    source=path,
                    destination=destination,
                    copied=False,
                    reason="already exists",
                )
            )
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        results.append(
            DocumentCopyResult(
                source=path,
                destination=destination,
                copied=True,
                overwritten=existed,
            )
        )

    return results


def copy_into_root(
    source: Path,
    root: Path,
    destination: Path | None = None,
    *,
    overwrite: bool = False,
) -> DocumentCopyResult:
    """Copy ``source`` into ``root``."""

    if not source.exists() or not source.is_file():
        raise DocumentCopyError(f"Source file {source} does not exist or is not a file")

    if destination is None:
        relative = Path(source.name)
    else:
        relative = destination
        if relative.suffix == "":
            relative = relative / source.name

    dest_path = (root / relative).resolve()
    _assert_within_root(root, dest_path)

    existed = dest_path.exists()
    if existed and not overwrite:
        raise DocumentCopyError(f"Destination {dest_path} already exists; set overwrite=True to replace it")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest_path)
    return DocumentCopyResult(source=source, destination=dest_path, copied=True, overwritten=existed)


def write_text_document(
    content: str,
    root: Path,
    relative_path: Path,
    *,
    overwrite: bool = False,
    encoding: str = "utf-8",
) -> Path:
    """Write ``content`` to ``root / relative_path`` ensuring safety."""

    if not content:
        raise DocumentCopyError("Content must not be empty")

    destination = (root / relative_path).resolve()
    _assert_within_root(root, destination)

    existed = destination.exists()
    if existed and not overwrite:
        raise DocumentCopyError(f"Destination {destination} already exists; set overwrite=True to replace it")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding=encoding)
    return destination
