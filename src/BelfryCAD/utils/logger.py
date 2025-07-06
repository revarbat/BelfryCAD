"""
Logging utilities for BelfryCad.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logger(
    name: str = "BelfryCad",
    level: int = logging.INFO
) -> logging.Logger:
    """Set up the main application logger.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    global _logger

    if _logger is not None:
        return _logger

    # Create logger
    _logger = logging.getLogger(name)
    _logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # Create file handler (optional)
    try:
        log_dir = Path.home() / ".pytkcad"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "pytkcad.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    except Exception as e:
        # If file logging fails, just continue with console logging
        _logger.warning(f"Could not set up file logging: {e}")

    return _logger


def get_logger(name: str = "BelfryCad") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (will be appended to main logger name)

    Returns:
        Logger instance
    """
    if _logger is None:
        setup_logger()

    return logging.getLogger(f"BelfryCad.{name}")
