"""Background scheduler that drives periodic ingestion runs."""

from __future__ import annotations

import logging
import subprocess
import time
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.schedulers.base import SchedulerNotRunningError  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]
from filelock import FileLock, Timeout

from gateway.api.connections import Neo4jConnectionManager, QdrantConnectionManager
from gateway.backup import BackupExecutionError
from gateway.backup.service import default_backup_destination, is_backup_archive, run_backup
from gateway.config.settings import AppSettings
from gateway.ingest.service import execute_ingestion
from gateway.observability.metrics import (
    BACKUP_LAST_STATUS,
    BACKUP_LAST_SUCCESS_TIMESTAMP,
    BACKUP_RETENTION_DELETES_TOTAL,
    BACKUP_RUNS_TOTAL,
    INGEST_SKIPS_TOTAL,
    SCHEDULER_LAST_SUCCESS_TIMESTAMP,
    SCHEDULER_RUNS_TOTAL,
)

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """APScheduler wrapper that coordinates repo-aware ingestion jobs."""

    def __init__(
        self,
        settings: AppSettings,
        *,
        graph_manager: Neo4jConnectionManager | None = None,
        qdrant_manager: QdrantConnectionManager | None = None,
    ) -> None:
        """Initialise scheduler state and ensure the scratch directory exists."""
        self.settings = settings
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self._started = False
        self._state_dir = self.settings.state_path / "scheduler"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._lock_path = self._state_dir / "ingest.lock"
        self._last_head_path = self._state_dir / "last_repo_head.txt"
        self._graph_manager = graph_manager
        self._qdrant_manager = qdrant_manager
        self._backup_enabled = settings.backup_enabled
        self._backup_retention_limit = max(0, settings.backup_retention_limit)
        default_destination = default_backup_destination(self.settings.state_path)
        self._backup_destination = (settings.backup_destination or default_destination).resolve()
        self._backup_script_path = settings.backup_script_path
        self._backup_status: dict[str, object] = {"status": "disabled" if not self._backup_enabled else "pending"}
        self._backup_lock_path = self._state_dir / "backup.lock"

    def start(self) -> None:
        """Register the ingestion job and begin scheduling if enabled."""
        ingest_enabled = self.settings.scheduler_enabled
        backup_enabled = self._backup_enabled

        if self._started or not (ingest_enabled or backup_enabled):
            return
        if ingest_enabled and self.settings.auth_enabled and not self.settings.maintainer_token:
            logger.error(
                "Scheduler disabled: maintainer token required when auth is enabled",
                extra={"setting": "KM_ADMIN_TOKEN"},
            )
            SCHEDULER_RUNS_TOTAL.labels(result="skipped_auth").inc()
            INGEST_SKIPS_TOTAL.labels(reason="auth").inc()
            return
        job_summaries: list[str] = []
        if ingest_enabled:
            trigger_config = self.settings.scheduler_trigger_config()
            trigger = _build_trigger(trigger_config)
            self.scheduler.add_job(
                self._run_ingestion,
                trigger,
                id="ingest",
                replace_existing=True,
            )
            job_summaries.append(f"ingest:{_describe_trigger(trigger_config)}")

        if backup_enabled:
            trigger_config = self.settings.backup_trigger_config()
            trigger = _build_trigger(trigger_config)
            self.scheduler.add_job(
                self._run_backup,
                trigger,
                id="backup",
                replace_existing=True,
            )
            self._backup_status = {"status": "pending"}
            job_summaries.append(f"backup:{_describe_trigger(trigger_config)}")

        self.scheduler.start()
        self._started = True
        logger.info("Scheduler started", extra={"triggers": job_summaries})

    def shutdown(self) -> None:
        """Stop the scheduler and release APScheduler resources."""
        if self._started:
            with suppress(SchedulerNotRunningError):
                self.scheduler.shutdown(wait=False)
            self._started = False

    def _run_ingestion(self) -> None:
        """Execute a single ingestion cycle, guarding with a file lock."""
        lock = FileLock(str(self._lock_path))
        try:
            try:
                lock.acquire(timeout=0)
            except Timeout:
                logger.info("Scheduled ingestion skipped: another run is active")
                SCHEDULER_RUNS_TOTAL.labels(result="skipped_lock").inc()
                INGEST_SKIPS_TOTAL.labels(reason="lock").inc()
                return

            last_head = self._read_last_head()
            current_head = _current_repo_head(self.settings.repo_root)
            if not self.settings.dry_run and current_head is not None and current_head == last_head:
                logger.info(
                    "Scheduled ingestion skipped: repository unchanged",
                    extra={"repo_head": current_head},
                )
                SCHEDULER_RUNS_TOTAL.labels(result="skipped_head").inc()
                INGEST_SKIPS_TOTAL.labels(reason="head").inc()
                return

            result = execute_ingestion(
                settings=self.settings,
                profile="scheduled",
                dry_run=self.settings.dry_run,
                use_dummy_embeddings=self.settings.ingest_use_dummy_embeddings,
                graph_manager=self._graph_manager,
                qdrant_manager=self._qdrant_manager,
            )

            if not self.settings.dry_run and result.repo_head:
                self._write_last_head(result.repo_head)

            logger.info(
                "Scheduled ingestion completed",
                extra={
                    "profile": result.profile,
                    "run_id": result.run_id,
                    "chunk_count": result.chunk_count,
                },
            )
            if result.success:
                SCHEDULER_RUNS_TOTAL.labels(result="success").inc()
                SCHEDULER_LAST_SUCCESS_TIMESTAMP.set(time.time())
            else:
                SCHEDULER_RUNS_TOTAL.labels(result="failure").inc()
        except (RuntimeError, subprocess.SubprocessError, OSError, ValueError) as exc:  # pragma: no cover - defensive
            logger.exception("Scheduled ingestion failed", extra={"error": str(exc)})
            SCHEDULER_RUNS_TOTAL.labels(result="failure").inc()
        finally:
            with suppress(RuntimeError):
                lock.release()

    def _run_backup(self) -> None:
        """Run the backup job and record metrics/retention."""

        lock = FileLock(str(self._backup_lock_path))
        try:
            try:
                lock.acquire(timeout=0)
            except Timeout:
                logger.info("Scheduled backup skipped: another run is active")
                BACKUP_RUNS_TOTAL.labels(result="skipped_lock").inc()
                return

            script_path = self._backup_script_path or Path(__file__).resolve().parents[1] / "bin" / "km-backup"
            try:
                result = run_backup(
                    state_path=self.settings.state_path,
                    script_path=script_path,
                    destination_path=self._backup_destination,
                )
            except BackupExecutionError as exc:  # pragma: no cover - defensive guard
                logger.exception("Scheduled backup failed", extra={"error": str(exc)})
                BACKUP_RUNS_TOTAL.labels(result="failure").inc()
                BACKUP_LAST_STATUS.set(0)
                now = time.time()
                self._backup_status = {
                    "status": "error",
                    "last_failure": now,
                    "error": str(exc),
                }
                return

            archive_path = Path(result["archive"]).resolve()
            BACKUP_RUNS_TOTAL.labels(result="success").inc()
            BACKUP_LAST_STATUS.set(1)
            timestamp = time.time()
            BACKUP_LAST_SUCCESS_TIMESTAMP.set(timestamp)
            deleted = self._prune_backups()
            self._backup_status = {
                "status": "ok",
                "last_success": timestamp,
                "archive": str(archive_path),
                "deleted": deleted,
            }
            size_bytes = result.get("size_bytes")
            if size_bytes is not None:
                self._backup_status["size_bytes"] = size_bytes
            logger.info(
                "Scheduled backup completed",
                extra={"archive": str(archive_path), "deleted": deleted},
            )
        finally:
            with suppress(RuntimeError):
                lock.release()

    def _read_last_head(self) -> str | None:
        try:
            return self._last_head_path.read_text().strip() or None
        except FileNotFoundError:
            return None

    def _write_last_head(self, head: str) -> None:
        self._last_head_path.write_text(head)

    def _prune_backups(self) -> int:
        if self._backup_retention_limit <= 0:
            return 0
        if not self._backup_destination.exists():
            return 0

        try:
            candidates = list(self._backup_destination.iterdir())
        except OSError:  # pragma: no cover - defensive guard
            return 0

        managed_archives: list[tuple[float, Path]] = []
        for path in candidates:
            if not is_backup_archive(path):
                continue
            try:
                managed_archives.append((path.stat().st_mtime, path))
            except OSError:
                continue

        managed_archives.sort(key=lambda item: item[0], reverse=True)

        deleted = 0
        for index, (_, archive) in enumerate(managed_archives):
            if index < self._backup_retention_limit:
                continue
            try:
                archive.unlink()
            except OSError as exc:
                logger.warning(
                    "Failed to delete expired backup archive",
                    extra={"archive": str(archive), "error": str(exc)},
                )
            else:
                deleted += 1
                BACKUP_RETENTION_DELETES_TOTAL.inc()
                logger.info(
                    "Deleted expired backup archive",
                    extra={"archive": str(archive)},
                )
        return deleted

    def backup_health(self) -> dict[str, object]:
        if not self._backup_enabled:
            return {"status": "disabled"}
        return dict(self._backup_status)


def _current_repo_head(repo_root: Path) -> str | None:
    """Return the git HEAD sha for the repo, or ``None`` when unavailable."""
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            or None
        )
    except (subprocess.CalledProcessError, OSError):
        return None


def _build_trigger(config: Mapping[str, object]) -> CronTrigger | IntervalTrigger:
    """Construct the APScheduler trigger based on user configuration."""
    trigger_type = config.get("type")
    if trigger_type == "cron":
        expression = str(config.get("expression", "")).strip()
        if not expression:
            raise ValueError("scheduler_cron expression cannot be empty when provided")
        return CronTrigger.from_crontab(expression, timezone="UTC")
    if trigger_type == "interval":
        raw_minutes = config.get("minutes", 1)
        minutes = _coerce_positive_int(raw_minutes, default=1)
        return IntervalTrigger(minutes=minutes)
    raise ValueError(f"Unsupported scheduler trigger type: {trigger_type}")


def _describe_trigger(config: Mapping[str, object]) -> str:
    """Provide a human readable summary of the configured trigger."""
    if config.get("type") == "cron":
        return f"cron:{config.get('expression')}"
    if config.get("type") == "interval":
        return f"interval:{config.get('minutes')}m"
    return "unknown"


def _coerce_positive_int(value: object, *, default: int) -> int:
    """Best-effort conversion to a positive integer with sane defaults."""
    numeric: int
    if isinstance(value, bool):
        numeric = int(value)
    elif isinstance(value, int):
        numeric = value
    elif isinstance(value, float):
        numeric = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            numeric = default
        else:
            try:
                numeric = int(text)
            except ValueError:
                numeric = default
    else:
        numeric = default
    if numeric < 1:
        return max(1, default)
    return numeric
