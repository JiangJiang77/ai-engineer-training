"""日志工具模块."""
from __future__ import annotations

import logging
import os
from typing import Optional


def _resolve_level(default: str = "INFO") -> int:
    raw = os.getenv("LOG_LEVEL", default).upper()
    return getattr(logging, raw, logging.INFO)


def setup_logger(name: str = "smart_customer_service", level: Optional[str] = None) -> logging.Logger:
    """创建并返回日志实例."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, (level or "").upper(), _resolve_level()))
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取模块级logger."""
    return setup_logger(name=name)


logger = setup_logger()

