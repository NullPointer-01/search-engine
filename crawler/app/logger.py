import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Set up a logger with JSON formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Remove existing handlers
    logger.handlers = []

    # Add stdout handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger


def log_event(logger: logging.Logger, event_type: str, **kwargs):
    """Log an event with extra fields."""
    extra_record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=event_type,
        args=(),
        exc_info=None,
    )
    extra_record.extra_fields = kwargs
    logger.handle(extra_record)