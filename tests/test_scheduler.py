"""Unit tests exercising the ingestion scheduler behaviour and metrics."""

# pylint: disable=protected-access,redefined-outer-name

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from unittest import mock

import pytest
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from filelock import Timeout
from prometheus_client import REGISTRY

from gateway.backup.exceptions import BackupExecutionError
from gateway.config.settings import AppSettings, get_settings
from gateway.ingest.pipeline import IngestionResult
from gateway.observability.metrics import BACKUP_LAST_STATUS
from gateway.scheduler import IngestionScheduler


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    """Clear cached settings before and after each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def scheduler_settings(tmp_path: Path) -> AppSettings:
    """Provide scheduler settings pointing at a temporary repo."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base = AppSettings()
    return base.model_copy(
        update={
            "repo_root": repo_root,
            "state_path": tmp_path / "state",
            "scheduler_enabled": True,
            "scheduler_interval_minutes": 1,
            "maintainer_token": "maintainer-token",
        }
    )


def make_scheduler(settings: AppSettings) -> IngestionScheduler:
    """Instantiate a scheduler with its APScheduler stubbed out."""
    scheduler = IngestionScheduler(settings)
    scheduler.scheduler = mock.Mock()
    return scheduler


def _metric_value(name: str, labels: dict[str, str] | None = None) -> float:
    """Fetch a Prometheus sample value with defaults for missing metrics."""
    value = REGISTRY.get_sample_value(name, labels or {})
    return float(value) if value is not None else 0.0


def make_result(head: str) -> IngestionResult:
    """Construct a minimal ingestion result for scheduler tests."""
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
    """Scheduler skips when repository head hash matches the cached value."""
    scheduler = IngestionScheduler(scheduler_settings)

    first_result = make_result("abc")
    before = _metric_value("km_scheduler_runs_total", {"result": "success"})
    with (
        mock.patch("gateway.scheduler.execute_ingestion", return_value=first_result) as execute,
        mock.patch("gateway.scheduler._current_repo_head", return_value="abc"),
    ):
        scheduler._run_ingestion()
        execute.assert_called_once()
    after = _metric_value("km_scheduler_runs_total", {"result": "success"})
    assert after == pytest.approx(before + 1)

    skipped_head_before = _metric_value("km_scheduler_runs_total", {"result": "skipped_head"})
    ingest_skip_before = _metric_value("km_ingest_skips_total", {"reason": "head"})
    with (
        mock.patch("gateway.scheduler.execute_ingestion") as execute_again,
        mock.patch("gateway.scheduler._current_repo_head", return_value="abc"),
    ):
        scheduler._run_ingestion()
        execute_again.assert_not_called()
    skipped_head_after = _metric_value("km_scheduler_runs_total", {"result": "skipped_head"})
    ingest_skip_after = _metric_value("km_ingest_skips_total", {"reason": "head"})
    assert skipped_head_after == pytest.approx(skipped_head_before + 1)
    assert ingest_skip_after == pytest.approx(ingest_skip_before + 1)


def test_scheduler_runs_when_repo_head_changes(scheduler_settings: AppSettings) -> None:
    """Scheduler triggers ingestion when the repository head changes."""
    scheduler = IngestionScheduler(scheduler_settings)
    scheduler._write_last_head("abc")

    before_success = _metric_value("km_scheduler_runs_total", {"result": "success"})
    with (
        mock.patch("gateway.scheduler.execute_ingestion", return_value=make_result("def")) as execute,
        mock.patch("gateway.scheduler._current_repo_head", return_value="def"),
    ):
        scheduler._run_ingestion()
        execute.assert_called_once()
        assert scheduler._read_last_head() == "def"
    after_success = _metric_value("km_scheduler_runs_total", {"result": "success"})
    assert after_success == pytest.approx(before_success + 1)


def test_scheduler_start_uses_interval_trigger(scheduler_settings: AppSettings) -> None:
    """Schedulers without cron use the configured interval trigger."""
    scheduler = make_scheduler(scheduler_settings)
    scheduler.start()
    scheduler.scheduler.add_job.assert_called_once()
    trigger = scheduler.scheduler.add_job.call_args[0][1]
    assert isinstance(trigger, IntervalTrigger)
    scheduler.scheduler.start.assert_called_once()


def test_scheduler_start_uses_cron_trigger(tmp_path: Path) -> None:
    """Cron expressions configure a cron trigger instead of interval."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    settings = AppSettings().model_copy(
        update={
            "repo_root": repo_root,
            "state_path": tmp_path / "state",
            "scheduler_enabled": True,
            "scheduler_cron": "0 * * * *",
            "maintainer_token": "secret",
        }
    )
    scheduler = make_scheduler(settings)
    scheduler.start()
    trigger = scheduler.scheduler.add_job.call_args[0][1]
    assert isinstance(trigger, CronTrigger)


def test_scheduler_schedules_backup_job(tmp_path: Path) -> None:
    """Standalone backup schedules a job even when ingestion is disabled."""

    state_path = tmp_path / "state"
    settings = AppSettings().model_copy(
        update={
            "state_path": state_path,
            "repo_root": tmp_path / "repo",
            "scheduler_enabled": False,
            "backup_enabled": True,
            "backup_interval_minutes": 1,
        }
    )
    settings.repo_root.mkdir()
    scheduler = make_scheduler(settings)
    scheduler.start()
    scheduler.scheduler.add_job.assert_called_once()
    add_job_call = scheduler.scheduler.add_job.call_args
    assert add_job_call[1]["id"] == "backup"
    assert scheduler.scheduler.start.called


def test_scheduler_backup_run_records_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Backup job updates metrics and retention tracking."""

    state_path = tmp_path / "state"
    state_path.mkdir()
    destination = state_path / "backups" / "archives"
    archive_path = destination / "km-backup-001.tgz"
    settings = AppSettings().model_copy(
        update={
            "state_path": state_path,
            "repo_root": tmp_path / "repo",
            "scheduler_enabled": False,
            "backup_enabled": True,
            "backup_retention_limit": 1,
        }
    )
    settings.repo_root.mkdir()
    scheduler = IngestionScheduler(settings)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text("")
    old_archive = destination / "km-backup-000.tgz"
    old_archive.write_text("")
    os.utime(old_archive, (1, 1))
    foreign_file = destination / "notes.txt"
    foreign_file.write_text("keep")
    monkeypatch.setattr(
        "gateway.scheduler.run_backup",
        lambda state_path, script_path, destination_path=None: {
            "archive": str(archive_path),
        },
    )
    BACKUP_LAST_STATUS.set(0)
    before_success = _metric_value("km_backup_runs_total", {"result": "success"})
    before_deleted = _metric_value("km_backup_retention_deletes_total")
    scheduler._run_backup()
    assert BACKUP_LAST_STATUS._value.get() == 1
    assert _metric_value("km_backup_runs_total", {"result": "success"}) == pytest.approx(
        before_success + 1,
    )
    health = scheduler.backup_health()
    assert health["status"] == "ok"
    assert health.get("deleted") == 1
    assert "last_success" in health
    assert not old_archive.exists()
    assert foreign_file.exists()
    assert _metric_value("km_backup_retention_deletes_total") == pytest.approx(before_deleted + 1)


def test_scheduler_backup_failure_records_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failures set the status gauge and increment failure counters."""

    state_path = tmp_path / "state"
    state_path.mkdir()
    settings = AppSettings().model_copy(
        update={
            "state_path": state_path,
            "repo_root": tmp_path / "repo",
            "scheduler_enabled": False,
            "backup_enabled": True,
        }
    )
    settings.repo_root.mkdir()
    scheduler = IngestionScheduler(settings)
    monkeypatch.setattr(
        "gateway.scheduler.run_backup",
        mock.Mock(side_effect=BackupExecutionError("boom")),
    )
    before_failure = _metric_value("km_backup_runs_total", {"result": "failure"})
    scheduler._run_backup()
    assert BACKUP_LAST_STATUS._value.get() == 0
    assert _metric_value("km_backup_runs_total", {"result": "failure"}) == pytest.approx(
        before_failure + 1,
    )
    health = scheduler.backup_health()
    assert health["status"] == "error"
    assert "error" in health


def test_scheduler_skips_when_lock_contended(scheduler_settings: AppSettings) -> None:
    """Lock contention causes the scheduler to skip runs and record metrics."""
    scheduler = IngestionScheduler(scheduler_settings)
    skipped_before = _metric_value("km_scheduler_runs_total", {"result": "skipped_lock"})
    ingest_skip_before = _metric_value("km_ingest_skips_total", {"reason": "lock"})
    with mock.patch(
        "gateway.scheduler.FileLock.acquire",
        side_effect=lambda *args, **kwargs: (_ for _ in ()).throw(Timeout(str(scheduler._lock_path))),
    ):
        with mock.patch("gateway.scheduler.execute_ingestion") as execute:
            scheduler._run_ingestion()
            execute.assert_not_called()
    skipped_after = _metric_value("km_scheduler_runs_total", {"result": "skipped_lock"})
    ingest_skip_after = _metric_value("km_ingest_skips_total", {"reason": "lock"})
    assert skipped_after == pytest.approx(skipped_before + 1)
    assert ingest_skip_after == pytest.approx(ingest_skip_before + 1)


def test_scheduler_requires_maintainer_token(tmp_path: Path) -> None:
    """Schedulers skip setup when auth is enabled without a maintainer token."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    settings = AppSettings().model_copy(
        update={
            "repo_root": repo_root,
            "state_path": tmp_path / "state",
            "scheduler_enabled": True,
            "auth_enabled": True,
            "maintainer_token": None,
        }
    )
    scheduler = make_scheduler(settings)
    before_ingest_skip = _metric_value("km_ingest_skips_total", {"reason": "auth"})
    scheduler.start()
    scheduler.scheduler.add_job.assert_not_called()
    skipped_auth = _metric_value("km_scheduler_runs_total", {"result": "skipped_auth"})
    ingest_skip_after = _metric_value("km_ingest_skips_total", {"reason": "auth"})
    assert skipped_auth >= 1
    assert ingest_skip_after == pytest.approx(before_ingest_skip + 1)
