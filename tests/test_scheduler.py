from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from gateway.config.settings import AppSettings
from gateway.ingest.pipeline import IngestionResult
from gateway.scheduler import IngestionScheduler


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def scheduler_settings(tmp_path: Path) -> AppSettings:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = AppSettings()
    return base.model_copy(
        update={
            "repo_root": repo_root,
            "state_path": tmp_path / "state",
            "scheduler_enabled": True,
            "scheduler_interval_minutes": 1,
        }
    )


def make_result(head: str) -> IngestionResult:
    return IngestionResult(
        run_id="r",
        profile="scheduled",
        started_at=0.0,
        duration_seconds=0.1,
        artifact_counts={},
        chunk_count=0,
        repo_head=head,
        success=True,
    )


def test_scheduler_skips_when_repo_head_unchanged(scheduler_settings: AppSettings) -> None:
    scheduler = IngestionScheduler(scheduler_settings)

    first_result = make_result("abc")
    with mock.patch(
        "gateway.scheduler.execute_ingestion", return_value=first_result
    ) as execute, mock.patch(
        "gateway.scheduler._current_repo_head", return_value="abc"
    ):
        scheduler._run_ingestion()
        execute.assert_called_once()

    with mock.patch("gateway.scheduler.execute_ingestion") as execute_again, mock.patch(
        "gateway.scheduler._current_repo_head", return_value="abc"
    ):
        scheduler._run_ingestion()
        execute_again.assert_not_called()


def test_scheduler_runs_when_repo_head_changes(scheduler_settings: AppSettings) -> None:
    scheduler = IngestionScheduler(scheduler_settings)
    scheduler._write_last_head("abc")

    with mock.patch(
        "gateway.scheduler.execute_ingestion", return_value=make_result("def")
    ) as execute, mock.patch(
        "gateway.scheduler._current_repo_head", return_value="def"
    ):
        scheduler._run_ingestion()
        execute.assert_called_once()
        assert scheduler._read_last_head() == "def"
