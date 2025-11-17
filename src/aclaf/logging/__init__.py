"""Logging support for Aclaf applications.

This module provides a Protocol-based logging interface with adapters
for popular Python logging libraries. The Protocol approach enables
structural subtyping: any object with the right methods works as a
logger without inheritance.

Available adapters:
    - StandardLibraryLogger: Always available (stdlib logging)
    - LoguruLogger: Requires 'loguru' package
    - StructlogLogger: Requires 'structlog' package
    - NullLogger: Always available (no-op implementation)
"""

from ._loguru import LOGURU_AVAILABLE, LoguruLogger
from ._mock import MockLogger
from ._null import NullLogger
from ._protocol import Logger
from ._stdlib import StandardLibraryLogger
from ._structlog import STRUCTLOG_AVAILABLE, StructlogLogger

__all__ = [
    "LOGURU_AVAILABLE",
    "STRUCTLOG_AVAILABLE",
    "Logger",
    "LoguruLogger",
    "MockLogger",
    "NullLogger",
    "StandardLibraryLogger",
    "StructlogLogger",
]


def create_logger(logger: Logger | str | None, name: str | None = None) -> Logger:
    if isinstance(logger, Logger):
        return logger

    if isinstance(logger, str):
        if logger == "stdlib":
            return StandardLibraryLogger(name=name)
        if logger == "loguru":
            if not LOGURU_AVAILABLE:
                msg = "LoguruLogger requires 'loguru' package."
                raise ImportError(msg)
            return LoguruLogger()
        if logger == "structlog":
            if not STRUCTLOG_AVAILABLE:
                msg = "StructlogLogger requires 'structlog' package."
                raise ImportError(msg)
            return StructlogLogger()
        msg = f"Unknown logger type string: '{logger}'"
        raise ValueError(msg)

    return NullLogger()
