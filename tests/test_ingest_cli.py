from __future__ import annotations

from pathlib import Path
import time
from unittest import mock

import pytest

from gateway.config.settings import get_settings
from gateway.ingest import cli
from gateway.ingest.audit import AuditLogger
from gateway.ingest.pipeline import IngestionResult


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "src" / "project" / "kasmina").mkdir(parents=True)
    (tmp_path / "docs" / "spec.md").write_text("Sample doc")
    (tmp_path / "src" / "project" / "kasmina" / "module.py").write_text("print('hi')")
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


def test_cli_rebuild_requires_maintainer_token(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_REPO_PATH", str(sample_repo))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_STATE_PATH", str(sample_repo / "state"))
    get_settings.cache_clear()

    with pytest.raises(SystemExit):
        cli.main(["rebuild"])


def test_cli_rebuild_with_maintainer_token(sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_REPO_PATH", str(sample_repo))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "secret")
    monkeypatch.setenv("KM_STATE_PATH", str(sample_repo / "state"))
    get_settings.cache_clear()

    dummy_result = mock.Mock(run_id="r", chunk_count=0, artifact_counts={})
    with mock.patch("gateway.ingest.cli.execute_ingestion", return_value=dummy_result) as execute:
        cli.main(["rebuild", "--dry-run", "--dummy-embeddings"])
        execute.assert_called_once()


def test_cli_audit_history_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    state_path = tmp_path / "state"
    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    get_settings.cache_clear()

    logger = AuditLogger(state_path / "audit" / "audit.db")
    result = IngestionResult(
        run_id="abc123",
        profile="local",
        started_at=time.time(),
        duration_seconds=1.5,
        artifact_counts={"docs": 2},
        chunk_count=10,
        repo_head="deadbeef",
        success=True,
    )
    logger.record(result)

    cli.main(["audit-history", "--limit", "5", "--json"])
    output = capsys.readouterr().out
    assert "abc123" in output
    assert "chunk_count" in output


def test_cli_audit_history_no_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    state_path = tmp_path / "state"
    monkeypatch.setenv("KM_STATE_PATH", str(state_path))
    get_settings.cache_clear()

    cli.main(["audit-history"])
    output = capsys.readouterr().out
    assert "No audit history records found." in output
