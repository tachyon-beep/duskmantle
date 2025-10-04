from pathlib import Path

import pytest

from gateway.ingest.discovery import DiscoveryConfig, discover

pytest.importorskip("tree_sitter_languages")


def _write(repo: Path, relative: str, content: str) -> Path:
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def test_discover_includes_symbols(tmp_path: Path) -> None:
    repo = tmp_path
    _write(
        repo,
        "src/foo/module.py",
        """
class Demo:
    def call(self):
        return 42
""".strip(),
    )

    artifacts = list(
        discover(
            DiscoveryConfig(
                repo_root=repo,
                symbols_enabled=True,
            )
        )
    )

    assert artifacts, "expected artifact discovery"
    metadata = artifacts[0].extra_metadata
    symbols = metadata.get("symbols")
    assert symbols and any(symbol["qualified_name"] == "Demo.call" for symbol in symbols)
    assert metadata.get("symbol_count") == len(symbols)
    assert metadata.get("symbol_names") == [symbol["qualified_name"] for symbol in symbols]
    assert metadata.get("symbol_kinds") == [symbol["kind"] for symbol in symbols]
    assert metadata.get("symbol_languages") == [symbol["language"] for symbol in symbols]
    assert metadata.get("symbol_ids") == [symbol["id"] for symbol in symbols]


def test_discover_skips_symbols_when_disabled(tmp_path: Path) -> None:
    repo = tmp_path
    _write(repo, "src/foo/sample.py", "def helper():\n    return None\n")

    artifacts = list(
        discover(
            DiscoveryConfig(
                repo_root=repo,
                symbols_enabled=False,
            )
        )
    )

    assert artifacts
    metadata = artifacts[0].extra_metadata
    assert "symbols" not in metadata
    assert "symbol_names" not in metadata
    assert "symbol_ids" not in metadata


def test_discover_excludes_dotenv(tmp_path: Path) -> None:
    repo = tmp_path
    dotenv = repo / 'docs' / '.env'
    dotenv.parent.mkdir(parents=True, exist_ok=True)
    dotenv.write_text("SECRET=1\n", encoding='utf-8')

    artifacts = list(
        discover(
            DiscoveryConfig(
                repo_root=repo,
                symbols_enabled=False,
            )
        )
    )

    assert all(artifact.path.name != '.env' for artifact in artifacts)


def test_discover_includes_dotenv_example(tmp_path: Path) -> None:
    repo = tmp_path
    dotenv_example = repo / 'docs' / '.env.example'
    dotenv_example.parent.mkdir(parents=True, exist_ok=True)
    dotenv_example.write_text('SAMPLE=1\n', encoding='utf-8')

    artifacts = list(
        discover(
            DiscoveryConfig(
                repo_root=repo,
                symbols_enabled=False,
            )
        )
    )

    assert any(artifact.path.name == '.env.example' for artifact in artifacts)
