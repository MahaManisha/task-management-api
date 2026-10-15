import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Standard keys to exclude from custom extra attributes in JSON logs
RESERVED_LOG_ATTRS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs", "msg",
    "name", "pathname", "process", "processName", "relativeCreated", "stack_info",
    "thread", "threadName", "taskName"
}


class JSONFormatter(logging.Formatter):
    """Custom logging Formatter that outputs log records as structured JSON strings."""

    def __init__(self, environment: str = "production"):
        super().__init__()
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": self.environment,
        }

        # Include custom extra fields passed during logging
        for key, value in record.__dict__.items():
            if key not in RESERVED_LOG_ATTRS and not key.startswith("_"):
                # Mask sensitive key names if present
                if any(secret in key.lower() for secret in ("password", "secret", "token", "api_key", "auth")):
                    log_entry[key] = "***MASKED***"
                else:
                    try:
                        json.dumps(value)
                        log_entry[key] = value
                    except (TypeError, OverflowError):
                        log_entry[key] = str(value)

        # Include Exception Traceback if available
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def configure_logging(
    environment: str = "development",
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Centralized logging configuration supporting development, production, and file logging modes."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)

    # Clear existing handlers to prevent duplicate logging
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    for handler in list(app_logger.handlers):
        app_logger.removeHandler(handler)
        handler.close()

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    if environment.lower() == "production":
        console_handler.setFormatter(JSONFormatter(environment="production"))
    else:
        plain_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(plain_formatter)

    root_logger.addHandler(console_handler)

    # 2. File Handler (if file path provided)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter(environment=environment))
        root_logger.addHandler(file_handler)

    return app_logger


def get_logger(name: str) -> logging.Logger:
    """Helper function to retrieve a configured logger instance."""
    return logging.getLogger(name)
