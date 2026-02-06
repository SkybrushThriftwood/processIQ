"""
Logging configuration for ProcessIQ.

Log Levels:
    DEBUG:   Development details (LLM calls, state transitions, data transforms)
    INFO:    Key operations ("Analyzing process...", "Found 3 bottlenecks")
    WARNING: Recoverable issues (missing optional data, fallback used)
    ERROR:   Failures (LLM API error, validation failure)

Usage:
    from processiq.logging_config import setup_logging
    setup_logging()

    # In any module:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Starting analysis")
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the entire application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Quiet noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
