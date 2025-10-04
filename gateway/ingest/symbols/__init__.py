"""Symbol extraction helpers for the ingestion pipeline."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, cast

logger = logging.getLogger(__name__)

try:  # Prefer prebuilt grammars when available
    from tree_sitter_languages import get_parser  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    get_parser = None  # type: ignore

Glyph = list[int]  # alias for row/column pairs


@dataclass(slots=True)
class SymbolRecord:
    """Represents a symbol discovered within a source artifact."""

    name: str
    kind: str
    language: str
    line_start: int
    line_end: int
    qualified_name: str

    def to_metadata(self, *, path: Path | None = None) -> dict[str, object]:
        """Return a JSON-serialisable payload for downstream indexing."""

        data: dict[str, object] = {
            "name": self.name,
            "kind": self.kind,
            "language": self.language,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "qualified_name": self.qualified_name,
        }
        if path is not None:
            data["id"] = f"{path.as_posix()}::{self.qualified_name}"
        return data


_LANGUAGE_HINTS: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
}


def extract_symbols(path: Path, content: str) -> list[SymbolRecord]:
    """Extract language symbols for a given repository artifact.

    Provides best-effort coverage using tree-sitter when available, with a
    universal-ctags fallback for environments that lack the prebuilt grammars.
    Failures are logged at debug level to avoid disrupting ingestion.
    """

    language = _detect_language(path)
    if language is None or not content.strip():
        return []

    try:
        if get_parser is not None:
            return _extract_with_tree_sitter(path, content, language)
    except Exception:  # pragma: no cover - defensive guard around optional dep
        logger.debug("tree-sitter extraction failed for %s", path, exc_info=True)

    fallback_symbols = _extract_with_ctags(path, content, language)
    if not fallback_symbols and get_parser is None:
        logger.debug(
            "Symbol extraction requires tree_sitter_languages or universal-ctags; none available for %s",
            path,
        )
    return fallback_symbols


def _detect_language(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in (".d.ts", ".cts", ".mts"):
        return "typescript"
    return _LANGUAGE_HINTS.get(suffix)


def _extract_with_tree_sitter(path: Path, content: str, language: str) -> list[SymbolRecord]:
    parser = get_parser(language)  # type: ignore[misc]
    tree = parser.parse(content.encode("utf-8"))
    source_bytes = content.encode("utf-8")
    results: list[SymbolRecord] = []
    _visit_tree(
        tree.root_node,
        source_bytes,
        results,
        language,
        parents=[],
    )
    results.sort(key=lambda symbol: (symbol.line_start, symbol.qualified_name))
    return results


def _visit_tree(node, source: bytes, results: list[SymbolRecord], language: str, parents: list[SymbolRecord]) -> None:
    """Depth-first traversal capturing symbols for supported languages."""

    kind_map: dict[str, str]
    if language == "python":
        kind_map = {
            "module": "module",
            "class_definition": "class",
            "function_definition": "function",
        }
    elif language in {"typescript", "tsx", "javascript"}:
        kind_map = {
            "program": "module",
            "class_declaration": "class",
            "abstract_class_declaration": "class",
            "interface_declaration": "interface",
            "function_declaration": "function",
            "method_definition": "method",
        }
    elif language == "go":
        kind_map = {
            "source_file": "module",
            "type_declaration": "type",
            "function_declaration": "function",
            "method_declaration": "method",
        }
    else:
        kind_map = {}

    record: SymbolRecord | None = None
    symbol_kind = kind_map.get(node.type)
    if symbol_kind and symbol_kind != "module":
        name = _resolve_node_name(node, source)
        if name:
            if symbol_kind == "function" and parents and parents[-1].kind in {"class", "interface", "type"}:
                symbol_kind = "method"
            qualified = ".".join([parent.qualified_name for parent in parents] + [name]) if parents else name
            record = SymbolRecord(
                name=name,
                kind=symbol_kind,
                language=language,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                qualified_name=qualified,
            )
            results.append(record)

    child_parents = parents
    if record and record.kind in {"class", "interface", "type"}:
        child_parents = parents + [record]
    for child in node.children:
        _visit_tree(child, source, results, language, child_parents)


def _resolve_node_name(node, source: bytes) -> str | None:
    candidate = node.child_by_field_name("name")
    if candidate:
        return _slice_bytes(source, candidate.start_byte, candidate.end_byte)
    for child in node.children:
        if child.type in {"identifier", "property_identifier", "type_identifier", "field_identifier"}:
            return _slice_bytes(source, child.start_byte, child.end_byte)
    return None


def _slice_bytes(source: bytes, start: int, end: int) -> str:
    return cast(str, source[start:end].decode("utf-8"))


def _extract_with_ctags(path: Path, content: str, language: str) -> list[SymbolRecord]:
    ctags_binary = shutil.which("ctags")
    if not ctags_binary:
        return []

    with tempfile.NamedTemporaryFile("w", suffix=path.suffix, encoding="utf-8", delete=False) as handle:
        handle.write(content)
        temp_name = handle.name

    try:
        proc = subprocess.run(
            [
                ctags_binary,
                "--fields=+n",
                "--extras=-F",
                "--output-format=json",
                "-o",
                "-",
                temp_name,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        Path(temp_name).unlink(missing_ok=True)

    if proc.returncode != 0:
        logger.debug("ctags failed for %s: %s", path, proc.stderr.strip())
        return []

    symbols: list[SymbolRecord] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = payload.get("name")
        kind = payload.get("kind") or payload.get("kindName")
        line_no = payload.get("line") or payload.get("lineNumber")
        if not name or not kind or not line_no:
            continue
        try:
            line_start = int(line_no)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            continue
        qualified = name if not symbols else f"{path.stem}.{name}"
        symbols.append(
            SymbolRecord(
                name=str(name),
                kind=str(kind),
                language=language,
                line_start=line_start,
                line_end=line_start,
                qualified_name=qualified,
            )
        )
    symbols.sort(key=lambda symbol: (symbol.line_start, symbol.qualified_name))
    return symbols


__all__ = ["SymbolRecord", "extract_symbols"]
