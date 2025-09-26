from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from gateway.config.settings import get_settings
from gateway.ingest import cli


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "src" / "esper" / "kasmina").mkdir(parents=True)
    (tmp_path / "docs" / "spec.md").write_text("Sample doc")
    (tmp_path / "src" / "esper" / "kasmina" / "module.py").write_text("print('hi')")
    return tmp_path


def test_cli_rebuild_dry_run(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_REPO_PATH", str(sample_repo))
    monkeypatch.setenv("KM_INGEST_USE_DUMMY", "true")
    monkeypatch.setenv("KM_INGEST_DRY_RUN", "true")
    monkeypatch.setenv("KM_STATE_PATH", str(sample_repo / "state"))

    dummy_result = mock.Mock(
        run_id="run",
        chunk_count=0,
        artifact_counts={},
    )

    with mock.patch("gateway.ingest.cli.execute_ingestion", return_value=dummy_result) as execute:
        cli.main(["rebuild", "--dry-run", "--dummy-embeddings"])
        execute.assert_called_once()
