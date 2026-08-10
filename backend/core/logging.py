from __future__ import annotations

import logging
import sys
import math
from backend.core.request_context import get_request_id


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "request_id=%(request_id)s | "
    "%(message)s"
)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(
        logging.Formatter(LOG_FORMAT)
    )

    handler.addFilter(
        RequestContextFilter()
    )

    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True,
    )
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)