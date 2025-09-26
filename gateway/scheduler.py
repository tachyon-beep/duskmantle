from __future__ import annotations

import logging
from contextlib import suppress

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from gateway.config.settings import AppSettings
from gateway.ingest.service import execute_ingestion

logger = logging.getLogger(__name__)


class IngestionScheduler:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self._started = False

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
        try:
            result = execute_ingestion(
                settings=self.settings,
                profile="scheduled",
                dry_run=self.settings.dry_run,
                use_dummy_embeddings=self.settings.ingest_use_dummy_embeddings,
            )
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
