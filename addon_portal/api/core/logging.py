"""Structured logging utilities for the licensing API.

This module provides file-based logging with configurable levels and log rotation.
Logs are stored in the logs/ directory and can be configured via environment variables.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .settings import settings


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


class TextLogFormatter(logging.Formatter):
    """Format log records as human-readable text."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        logger = record.name
        message = record.getMessage()
        
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            return f"{timestamp} [{level}] {logger}: {message}\n{exc_text}"
        
        return f"{timestamp} [{level}] {logger}: {message}"


def get_log_level(level_name: str) -> int:
    """Convert log level name to logging constant."""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_name.upper(), logging.INFO)


def configure_logging() -> None:
    """Configure the root logger with file and console handlers."""
    root_logger = logging.getLogger()
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Get log level from settings
    log_level = get_log_level(settings.LOG_LEVEL)
    root_logger.setLevel(log_level)
    
    # Only configure if logging is enabled
    if not settings.LOG_ENABLED:
        # Add a null handler to suppress all logging
        root_logger.addHandler(logging.NullHandler())
        return
    
    # Create logs directory if it doesn't exist (relative to project root)
    # Try multiple possible locations
    project_root = Path(__file__).parent.parent.parent.parent  # Go up from api/core/logging.py to project root
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create log file with date-based naming
    log_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = logs_dir / f"api_{log_date}.log"
    
    # File handler - write to log file
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    
    # Use text formatter for file logs (more readable)
    file_formatter = TextLogFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler - write to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use JSON formatter for console logs (for structured logging)
    console_formatter = JsonLogFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger.

    Args:
        name: Logger name. If omitted, the default licensing logger is returned.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    configure_logging()
    return logging.getLogger(name or "q2o.licensing")
