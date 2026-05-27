"""
Logging configuration and utilities.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):
    """Handler that intercepts standard logging to route through loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
) -> None:
    """
    Configure logging with loguru.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        log_format: Format string for log messages
    """
    # Remove default handler
    loguru_logger.remove()

    # Add console handler
    loguru_logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        colorize=True,
    )

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        loguru_logger.add(
            log_file,
            level=log_level,
            format=log_format,
            rotation="500 MB",
            retention="30 days",
            compression="zip",
        )

    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0)


def get_logger(name: str) -> "loguru_logger":
    """
    Get a logger instance.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        Logger instance
    """
    return loguru_logger.bind(name=name)
