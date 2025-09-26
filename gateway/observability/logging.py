from __future__ import annotations

import logging
import sys
from typing import Any, MutableMapping

from pythonjsonlogger import jsonlogger

_LOG_CONFIGURED = False


class IngestAwareFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that enforces consistent keys."""

    def add_fields(
        self,
        log_record: MutableMapping[str, Any],
        record: logging.LogRecord,
        message_dict: MutableMapping[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)
        log_record.setdefault("message", record.getMessage())


def configure_logging() -> None:
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = IngestAwareFormatter("%(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)

    # Silence overly chatty libraries
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _LOG_CONFIGURED = True
