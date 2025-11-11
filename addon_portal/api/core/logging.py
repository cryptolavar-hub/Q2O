"""Structured logging utilities for the licensing API.

This module centralizes logging configuration across the licensing service.
Logs are emitted in JSON format to simplify ingestion by observability stacks.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JsonLogFormatter(logging.Formatter):
    """Format log records using a structured JSON schema."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - custom format doc
        base_record: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            base_record["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            base_record.update(record.extra)  # type: ignore[arg-type]

        return json.dumps(base_record, ensure_ascii=False)


def configure_logging(default_level: int = logging.INFO) -> None:
    """Configure the root logger with JSON formatting.

    Args:
        default_level: Logging level to apply to the root logger.
    """

    root_logger = logging.getLogger()
    if any(isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root_logger.handlers = [handler]
    root_logger.setLevel(default_level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger.

    Args:
        name: Logger name. If omitted, the default licensing logger is returned.

    Returns:
        A configured :class:`logging.Logger` instance.
    """

    configure_logging()
    return logging.getLogger(name or "q2o.licensing")
