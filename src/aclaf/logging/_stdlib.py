"""Standard library logging adapter for Aclaf.

This module provides an adapter that wraps Python's built-in logging
module to conform to Aclaf's Logger protocol. This is always available
as it uses only the standard library.
"""
# pyright: reportAny=false, reportExplicitAny=false

from logging import Logger as StdlibLogger, getLogger
from typing import Any
from typing_extensions import override

from ._protocol import Logger


class StandardLibraryLogger(Logger):
    """Adapter for Python's stdlib logging module.

    Wraps a stdlib Logger instance to conform to Aclaf's Logger
    protocol. Handles the mapping of **context kwargs to the
    'extra' parameter that stdlib logging expects.

    Args:
        logger: Optional stdlib Logger instance. If not provided,
            uses getLogger() with the specified name or root logger.
        name: Optional logger name. Only used if logger is not provided.

    Example:
        >>> import logging
        >>> from aclaf.logging import StandardLibraryLogger
        >>> logging.basicConfig(level=logging.INFO)
        >>> logger = StandardLibraryLogger(name="myapp")
        >>> logger.info("Starting", version="1.0")

    Note:
        This adapter always uses the 'extra' parameter for context,
        which means context keys must not conflict with LogRecord
        attributes. Use namespacing (e.g., "app_user_id") to avoid
        conflicts.
    """

    def __init__(
        self,
        logger: StdlibLogger | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize adapter with stdlib logger.

        Args:
            logger: Optional stdlib Logger instance. If provided,
                the name parameter is ignored.
            name: Logger name for getLogger(). Only used if logger
                is None. If both are None, uses root logger.
        """
        self._logger: StdlibLogger = logger or getLogger(name)

    @override
    def debug(self, message: str, **context: Any) -> None:
        """Log debug message with context as 'extra'."""
        self._logger.debug(message, extra=context)

    @override
    def info(self, message: str, **context: Any) -> None:
        """Log info message with context as 'extra'."""
        self._logger.info(message, extra=context)

    @override
    def warning(self, message: str, **context: Any) -> None:
        """Log warning message with context as 'extra'."""
        self._logger.warning(message, extra=context)

    @override
    def error(self, message: str, **context: Any) -> None:
        """Log error message with context as 'extra'."""
        self._logger.error(message, extra=context)

    @override
    def critical(self, message: str, **context: Any) -> None:
        """Log critical message with context as 'extra'."""
        self._logger.critical(message, extra=context)

    @override
    def exception(self, message: str, **context: Any) -> None:
        """Log exception with traceback and context as 'extra'."""
        self._logger.exception(message, extra=context)
