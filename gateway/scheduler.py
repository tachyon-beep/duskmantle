from __future__ import annotations

import logging
import subprocess
from contextlib import suppress
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from filelock import FileLock, Timeout

from gateway.config.settings import AppSettings
from gateway.ingest.service import execute_ingestion

logger = logging.getLogger(__name__)


class IngestionScheduler:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self._started = False
        self._state_dir = self.settings.state_path / "scheduler"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._lock_path = self._state_dir / "ingest.lock"
        self._last_head_path = self._state_dir / "last_repo_head.txt"

    def start(self) -> None:
        if self._started or not self.settings.scheduler_enabled:
            return
        interval = max(1, self.settings.scheduler_interval_minutes)
        self.scheduler.add_job(
            self._run_ingestion,
            IntervalTrigger(minutes=interval),
            id="ingest",
            replace_existing=True,
        )
        self.scheduler.start()
        self._started = True
        logger.info("Scheduler started", extra={"interval_minutes": interval})

    def shutdown(self) -> None:
        if self._started:
            with suppress(Exception):
                self.scheduler.shutdown(wait=False)
            self._started = False

    def _run_ingestion(self) -> None:
        lock = FileLock(str(self._lock_path))
        try:
            try:
                lock.acquire(timeout=0)
            except Timeout:
                logger.info("Scheduled ingestion skipped: another run is active")
                return

            last_head = self._read_last_head()
            current_head = _current_repo_head(self.settings.repo_root)
            if (
                not self.settings.dry_run
                and current_head is not None
                and current_head == last_head
            ):
                logger.info(
                    "Scheduled ingestion skipped: repository unchanged",
                    extra={"repo_head": current_head},
                )
                return

            result = execute_ingestion(
                settings=self.settings,
                profile="scheduled",
                dry_run=self.settings.dry_run,
                use_dummy_embeddings=self.settings.ingest_use_dummy_embeddings,
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
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Scheduled ingestion failed", extra={"error": str(exc)})
        finally:
            with suppress(Exception):
                lock.release()

    def _read_last_head(self) -> str | None:
        try:
            return self._last_head_path.read_text().strip() or None
        except FileNotFoundError:
            return None

    def _write_last_head(self, head: str) -> None:
        self._last_head_path.write_text(head)


def _current_repo_head(repo_root: Path) -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            .strip()
            or None
        )
    except Exception:
        return None
