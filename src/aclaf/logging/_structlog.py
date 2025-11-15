"""Structlog adapter for Aclaf logging.

This module provides an adapter that wraps structlog's BoundLogger
to conform to Aclaf's Logger protocol. Structlog is an optional dependency.
"""
# pyright: reportAny=false, reportExplicitAny=false

from typing import TYPE_CHECKING, Any
from typing_extensions import override

from ._protocol import Logger

if TYPE_CHECKING:
    try:  # noqa: SIM105 - contextlib.suppress not available in TYPE_CHECKING
        from structlog import (
            typing as structlog_typing,
        )
    except ImportError:
        pass  # Structlog is optional

try:
    import structlog
    from structlog import typing as structlog_typing
except ImportError as e:
    _structlog_import_error = e
else:
    _structlog_import_error = None

STRUCTLOG_AVAILABLE = _structlog_import_error is None


class StructlogLogger(Logger):
    """Adapter for structlog logging library.

    Wraps a structlog BoundLogger to conform to Aclaf's Logger
    protocol. Handles structlog's binding semantics where context
    can be bound to the logger or passed per-call.

    Args:
        logger: Structlog BoundLogger instance. If not provided,
            calls structlog.get_logger() to create one.

    Example:
        >>> import structlog
        >>> from aclaf.logging import StructlogLogger
        >>> structlog.configure(...)  # Configure as needed
        >>> struct_logger = structlog.get_logger()
        >>> adapter = StructlogLogger(struct_logger)
        >>> adapter.info("Service started", port=8000, env="production")

    Raises:
        ImportError: If structlog is not installed.

    Note:
        Requires structlog to be installed: `pip install structlog`
    """

    def __init__(
        self,
        logger: "structlog_typing.FilteringBoundLogger | None" = None,
    ) -> None:
        """Initialize adapter with structlog logger.

        Args:
            logger: Structlog BoundLogger instance. If None, calls
                structlog.get_logger() to create one.

        Raises:
            ImportError: If structlog is not installed.
        """
        if not STRUCTLOG_AVAILABLE:
            msg = "The 'structlog' library is required for StructlogLogger."
            raise ImportError(msg) from _structlog_import_error

        self._logger: structlog_typing.FilteringBoundLogger = (
            logger or structlog.get_logger()  # pyright: ignore[reportPossiblyUnboundVariable]
        )

    @override
    def debug(self, message: str, **context: Any) -> None:
        """Log debug message with context."""
        self._logger.debug(message, **context)

    @override
    def info(self, message: str, **context: Any) -> None:
        """Log info message with context."""
        self._logger.info(message, **context)

    @override
    def warning(self, message: str, **context: Any) -> None:
        """Log warning message with context."""
        self._logger.warning(message, **context)

    @override
    def error(self, message: str, **context: Any) -> None:
        """Log error message with context."""
        self._logger.error(message, **context)

    @override
    def critical(self, message: str, **context: Any) -> None:
        """Log critical message with context."""
        self._logger.critical(message, **context)

    @override
    def exception(self, message: str, **context: Any) -> None:
        """Log exception with context.

        Structlog doesn't have a dedicated exception() method
        by default, so this logs at error level with exc_info=True
        to capture traceback information via structlog's exception
        processor.
        """
        self._logger.error(message, exc_info=True, **context)  # noqa: LOG014
