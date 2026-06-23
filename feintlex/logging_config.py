from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from logging import LogRecord

from feintlex.config import Settings, get_settings


SENSITIVE_WORDS = ("api_key", "token", "secret", "webhook")


class JsonFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in payload or key in {"args", "msg", "exc_info", "exc_text", "stack_info"}:
                continue
            if any(word in key.lower() for word in SENSITIVE_WORDS):
                payload[key] = "[redacted]"
            elif isinstance(value, (str, int, float, bool)) or value is None:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    log_path = settings.resolved_log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("feintlex")
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()
    root.propagate = False

    formatter = JsonFormatter()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
