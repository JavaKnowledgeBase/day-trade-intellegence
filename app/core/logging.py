"""Structured logging configuration used by API and worker processes."""

import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def configure_logging(log_level: str) -> None:
    """Configure the root logger to emit JSON logs suitable for centralized observability."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d"))
    root_logger.addHandler(handler)
