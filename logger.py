import os
import logging
from typing import Optional

# Configure logging - set level from LOG_LEVEL environment variable
# Valid values: "debug", "info", "warn", "error" (case-insensitive)
LOG_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "err": logging.ERROR,
}

# Define the logger as a global variable to avoid creating a new logger for each call
_logger: Optional[logging.Logger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    if _logger is not None:
        return _logger

    if name is None:
        name = __name__
    log_level_name = os.getenv("LOG_LEVEL", "info").lower()
    log_level = LOG_LEVEL_MAP.get(log_level_name, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
    )
    _logger = logging.getLogger(name)
    return _logger
