"""Logging configuration with JSON formatting and CloudWatch support."""

import json
import logging
import logging.config
from typing import Any, Dict

from bedrock_poc.logging.correlation import get_correlation_id
from bedrock_poc.config import get_settings


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        record.correlation_id = get_correlation_id()
        return True


class JSONFormatter(logging.Formatter):
    """Format logs as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string with structured log data
        """
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extras"):
            log_data.update(record.extras)

        # Add function and line number for debugging
        if record.levelno >= logging.WARNING:
            log_data["source"] = f"{record.filename}:{record.lineno}"
            log_data["function"] = record.funcName

        return json.dumps(log_data)


def setup_logging(settings: Any = None) -> None:
    """Configure structured logging for the application.

    Args:
        settings: Application settings (uses get_settings() if None)
    """
    if settings is None:
        settings = get_settings()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with appropriate formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.logging.level))

    if settings.logging.format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(correlation_id)s: %(message)s"
        )

    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationIDFilter())

    root_logger.addHandler(console_handler)

    # File handler if configured
    if settings.logging.log_file:
        file_handler = logging.FileHandler(settings.logging.log_file)
        file_handler.setLevel(getattr(logging, settings.logging.level))
        file_handler.setFormatter(formatter)
        file_handler.addFilter(CorrelationIDFilter())
        root_logger.addHandler(file_handler)

    # Set logging level for specific modules
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("bedrock_poc").setLevel(getattr(logging, settings.logging.level))

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "extras": {
                "level": settings.logging.level,
                "format": settings.logging.format,
                "environment": settings.environment,
            }
        },
    )


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a logger with correlation ID support.

    Args:
        name: Logger name (typically __name__)

    Returns:
        LoggerAdapter with correlation ID support
    """
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, {"correlation_id": get_correlation_id})
