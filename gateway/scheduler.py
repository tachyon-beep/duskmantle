from __future__ import annotations

import logging
import subprocess
import time
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]
from filelock import FileLock, Timeout

from gateway.config.settings import AppSettings
from gateway.ingest.service import execute_ingestion
from gateway.observability.metrics import INGEST_SKIPS_TOTAL, SCHEDULER_LAST_SUCCESS_TIMESTAMP, SCHEDULER_RUNS_TOTAL

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
        if self.settings.auth_enabled and not self.settings.maintainer_token:
            logger.error(
                "Scheduler disabled: maintainer token required when auth is enabled",
                extra={"setting": "KM_ADMIN_TOKEN"},
            )
            SCHEDULER_RUNS_TOTAL.labels(result="skipped_auth").inc()
            INGEST_SKIPS_TOTAL.labels(reason="auth").inc()
            return
        trigger_config = self.settings.scheduler_trigger_config()
        trigger = _build_trigger(trigger_config)
        self.scheduler.add_job(
            self._run_ingestion,
            trigger,
            id="ingest",
            replace_existing=True,
        )
        trigger_summary = _describe_trigger(trigger_config)
        self.scheduler.start()
        self._started = True
        logger.info("Scheduler started", extra={"trigger": trigger_summary})

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
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Scheduled ingestion failed", extra={"error": str(exc)})
            SCHEDULER_RUNS_TOTAL.labels(result="failure").inc()
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
            ).strip()
            or None
        )
    except Exception:
        return None


def _build_trigger(config: Mapping[str, object]) -> CronTrigger | IntervalTrigger:
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
    if config.get("type") == "cron":
        return f"cron:{config.get('expression')}"
    if config.get("type") == "interval":
        return f"interval:{config.get('minutes')}m"
    return "unknown"


def _coerce_positive_int(value: object, *, default: int) -> int:
    try:
        numeric = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        numeric = default
    if numeric < 1:
        return max(1, default)
    return numeric
