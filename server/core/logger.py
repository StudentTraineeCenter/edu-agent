import json
import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add standard record attributes that might be useful
        if record.pathname:
            log_data["pathname"] = record.pathname
        if record.lineno:
            log_data["lineno"] = record.lineno
        if record.funcName:
            log_data["function"] = record.funcName

        return json.dumps(log_data, default=str)


def _setup_logging() -> None:
    """Configure logging with structured JSON formatting.
    
    Note: Azure Monitor OpenTelemetry is configured in main.py before this module is imported.
    This ensures proper initialization order and automatic collection of traces, metrics, logs, and exceptions.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler with structured JSON formatting
    # Azure Monitor OpenTelemetry will also collect logs automatically
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)


# Initialize logging on module import
_setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name and structured logging support."""
    logger = logging.getLogger(name)

    # Add helper methods for structured logging
    def log_with_extra(level: int, msg: str, **kwargs: Any) -> None:
        """Log with extra structured fields."""
        extra = {"extra_fields": kwargs}
        logger.log(level, msg, extra=extra)

    def info_structured(msg: str, **kwargs: Any) -> None:
        """Log info level with structured fields."""
        log_with_extra(logging.INFO, msg, **kwargs)

    def error_structured(msg: str, **kwargs: Any) -> None:
        """Log error level with structured fields."""
        log_with_extra(logging.ERROR, msg, **kwargs)

    def warning_structured(msg: str, **kwargs: Any) -> None:
        """Log warning level with structured fields."""
        log_with_extra(logging.WARNING, msg, **kwargs)

    def debug_structured(msg: str, **kwargs: Any) -> None:
        """Log debug level with structured fields."""
        log_with_extra(logging.DEBUG, msg, **kwargs)

    # Attach structured logging methods to logger
    logger.info_structured = info_structured  # type: ignore
    logger.error_structured = error_structured  # type: ignore
    logger.warning_structured = warning_structured  # type: ignore
    logger.debug_structured = debug_structured  # type: ignore

    return logger
