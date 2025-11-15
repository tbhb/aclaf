"""Loguru adapter for Aclaf logging.

This module provides an adapter that wraps loguru's logger to conform
to Aclaf's Logger protocol. Loguru is an optional dependency.
"""
# pyright: reportAny=false, reportExplicitAny=false, reportUnknownMemberType=false

from typing import TYPE_CHECKING, Any
from typing_extensions import override

from ._protocol import Logger

if TYPE_CHECKING:
    try:  # noqa: SIM105 - contextlib.suppress not available in TYPE_CHECKING
        from loguru import _logger as loguru_logger
    except ImportError:
        pass  # Loguru is optional

try:
    from loguru import _logger as loguru_logger
except ImportError as e:
    _loguru_import_error = e
else:
    _loguru_import_error = None

LOGURU_AVAILABLE = _loguru_import_error is None


class LoguruLogger(Logger):
    """Adapter for loguru logging library.

    Wraps a loguru logger instance to conform to Aclaf's Logger
    protocol. Loguru naturally accepts **kwargs so this adapter
    is essentially pass-through with consistent naming.

    Args:
        logger: Loguru logger instance. If not provided, uses the
            default loguru logger instance.

    Example:
        >>> from loguru import logger
        >>> from aclaf.logging import LoguruLogger
        >>> adapter = LoguruLogger(logger)
        >>> adapter.info("Request processed", status_code=200, duration_ms=42)

    Raises:
        ImportError: If loguru is not installed.

    Note:
        Requires loguru to be installed: `pip install loguru`
    """

    def __init__(
        self,
        logger: "loguru_logger.Logger | None" = None,
    ) -> None:
        """Initialize adapter with loguru logger.

        Args:
            logger: Loguru logger instance. If None, imports and uses
                the default loguru logger.

        Raises:
            ImportError: If loguru is not installed.
        """
        if not LOGURU_AVAILABLE:
            msg = "The 'loguru' library is required for LoguruLogger."
            raise ImportError(msg) from _loguru_import_error

        self._logger: loguru_logger.Logger = logger or loguru_logger  # pyright: ignore[reportAttributeAccessIssue, reportPossiblyUnboundVariable]

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
        """Log exception with traceback and context."""
        self._logger.exception(message, **context)
