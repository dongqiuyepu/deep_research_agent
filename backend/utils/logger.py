import json
import logging
from datetime import datetime
from typing import Any, Dict


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Structured logger adapter."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        extra = kwargs.get("extra", {})
        log_dict = {"timestamp": datetime.utcnow().isoformat() + "Z", "message": msg, **extra}
        kwargs["extra"] = {}
        return json.dumps(log_dict, ensure_ascii=False), kwargs


def get_logger(name: str) -> StructuredLoggerAdapter:
    base_logger = logging.getLogger(name)
    return StructuredLoggerAdapter(base_logger, {})
