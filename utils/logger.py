"""Structured logging configuration for console and file output."""

import logging
import sys
from pathlib import Path


def setup_logger(log_file: Path, log_level: str = "INFO") -> logging.Logger:
    """Configure and return the root assessment logger with console and file handlers."""
    logger = logging.getLogger("toolshop_rpa")
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console stream handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def log_business_outcome(
    logger: logging.Logger,
    action: str,
    outcome: str,
    details: str,
) -> None:
    """Record an expected business outcome separately from technical errors."""
    message = f"[BUSINESS_OUTCOME] [{action}] status='{outcome}' details='{details}'"
    logger.info(message)
