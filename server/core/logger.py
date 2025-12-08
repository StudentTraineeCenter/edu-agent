import json
import logging
import os
import sys
from typing import Any, Dict


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


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


class PrettyFormatter(logging.Formatter):
    """Pretty formatter with colors for development."""

    LEVEL_COLORS = {
        "DEBUG": Colors.CYAN,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.RED + Colors.BOLD,
    }

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.use_colors = sys.stdout.isatty()

    def _get_level_color(self, levelname: str) -> str:
        """Get color code for log level."""
        if not self.use_colors:
            return ""
        return self.LEVEL_COLORS.get(levelname, Colors.RESET)

    def format(self, record: logging.LogRecord) -> str:
        # Format timestamp
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        
        # Get level color
        level_color = self._get_level_color(record.levelname)
        reset = Colors.RESET if self.use_colors else ""
        
        # Format level with color
        level = f"{level_color}{record.levelname:8s}{reset}"
        
        # Format logger name (truncate if too long)
        logger_name = record.name
        if len(logger_name) > 30:
            logger_name = "..." + logger_name[-27:]
        logger_name = f"{Colors.DIM}{logger_name}{reset}" if self.use_colors else logger_name
        
        # Format message
        message = record.getMessage()
        
        # Build base log line
        log_line = f"{Colors.DIM}{timestamp}{reset} {level} {logger_name} {message}"
        
        # Add extra fields if present
        if hasattr(record, "extra_fields") and record.extra_fields:
            extra_str = " ".join(
                f"{Colors.CYAN}{k}{reset}={Colors.YELLOW}{v}{reset}"
                if self.use_colors
                else f"{k}={v}"
                for k, v in record.extra_fields.items()
            )
            log_line += f" {extra_str}"
        
        # Add exception info if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if self.use_colors:
                exc_text = f"{Colors.RED}{exc_text}{reset}"
            log_line += f"\n{exc_text}"
        
        return log_line


def _setup_logging() -> None:
    """Configure logging with structured JSON or pretty formatting.

    Note: Azure Monitor OpenTelemetry is configured in main.py before this module is imported.
    This ensures proper initialization order and automatic collection of traces, metrics, logs, and exceptions.
    """
    root_logger = logging.getLogger()
    
    # Get log level from environment (default: INFO)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Check if pretty logs are enabled (default: true for better readability in Azure log stream)
    # Set JSON_LOGS=true to use structured JSON logging instead
    use_json_logs = os.getenv("JSON_LOGS", "").lower() in ("true", "1", "yes")
    use_pretty_logs = not use_json_logs

    # Console handler with pretty formatting (default) or structured JSON
    # Pretty logs are more readable in Azure log stream and development
    # Azure Monitor OpenTelemetry will also collect logs automatically
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    if use_pretty_logs:
        console_handler.setFormatter(
            PrettyFormatter(
                fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    else:
        console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)


# Initialize logging on module import
_setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name and structured logging support."""
    logger = logging.getLogger(name)

    # Add helper methods for structured logging
    def log_with_extra(level: int, msg: str, exc_info: Any = None, **kwargs: Any) -> None:
        """Log with extra structured fields."""
        extra = {"extra_fields": kwargs}
        logger.log(level, msg, extra=extra, exc_info=exc_info)

    def info_structured(msg: str, exc_info: Any = None, **kwargs: Any) -> None:
        """Log info level with structured fields."""
        log_with_extra(logging.INFO, msg, exc_info=exc_info, **kwargs)

    def error_structured(msg: str, exc_info: Any = None, **kwargs: Any) -> None:
        """Log error level with structured fields."""
        log_with_extra(logging.ERROR, msg, exc_info=exc_info, **kwargs)

    def warning_structured(msg: str, exc_info: Any = None, **kwargs: Any) -> None:
        """Log warning level with structured fields."""
        log_with_extra(logging.WARNING, msg, exc_info=exc_info, **kwargs)

    def debug_structured(msg: str, exc_info: Any = None, **kwargs: Any) -> None:
        """Log debug level with structured fields."""
        log_with_extra(logging.DEBUG, msg, exc_info=exc_info, **kwargs)

    # Attach structured logging methods to logger
    logger.info_structured = info_structured  # type: ignore
    logger.error_structured = error_structured  # type: ignore
    logger.warning_structured = warning_structured  # type: ignore
    logger.debug_structured = debug_structured  # type: ignore

    return logger
