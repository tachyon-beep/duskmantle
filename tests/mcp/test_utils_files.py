from __future__ import annotations

from pathlib import Path

import pytest

from gateway.mcp.utils import files


def test_sweep_documents_copies_supported_files(tmp_path: Path) -> None:
    root = tmp_path
    docs_dir = root / "docs"
    docs_dir.mkdir()
    source_dir = root / "notes"
    source_dir.mkdir()
    (source_dir / "meeting.md").write_text("notes")

    results = list(files.sweep_documents(root, Path("docs")))

    assert any(result.copied for result in results)
    copied_path = docs_dir / "notes" / "meeting.md"
    assert copied_path.exists()


def test_sweep_documents_dry_run_reports_actions(tmp_path: Path) -> None:
    root = tmp_path
    (root / "raw").mkdir()
    (root / "raw" / "outline.txt").write_text("outline")

    results = list(files.sweep_documents(root, Path("docs"), dry_run=True))

    assert any(result.reason == "dry-run" for result in results)
    assert not (root / "docs" / "raw" / "outline.txt").exists()


def test_copy_into_root_prevents_traversal(tmp_path: Path) -> None:
    source = tmp_path / "input.md"
    source.write_text("content")
    root = tmp_path / "root"
    root.mkdir()

    with pytest.raises(files.DocumentCopyError):
        files.copy_into_root(source, root, Path(".."))


def test_write_text_document_requires_content(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()

    with pytest.raises(files.DocumentCopyError):
        files.write_text_document("", root, Path("docs/empty.md"))


def test_slugify_generates_fallback_when_empty() -> None:
    assert files.slugify("!!!", fallback="fallback") == "fallback"
    assert files.slugify("Project Brief") == "project-brief"

