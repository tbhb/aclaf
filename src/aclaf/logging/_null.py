# pyright: reportAny=false, reportExplicitAny=false, reportUnusedParameter=false

from typing import Any
from typing_extensions import override

from ._protocol import Logger


class NullLogger(Logger):
    """No-op logger implementation for testing or disabling logging.

    All methods are no-ops, making this useful for tests that don't
    care about logging output or for applications that want to
    completely disable logging without changing code.

    Example:
        >>> from aclaf.logging import NullLogger
        >>> logger = NullLogger()
        >>> logger.info("This goes nowhere")  # No output, no side effects
    """

    @override
    def debug(self, message: str, **context: Any) -> None:
        """No-op debug method."""

    @override
    def info(self, message: str, **context: Any) -> None:
        """No-op info method."""

    @override
    def warning(self, message: str, **context: Any) -> None:
        """No-op warning method."""

    @override
    def error(self, message: str, **context: Any) -> None:
        """No-op error method."""

    @override
    def critical(self, message: str, **context: Any) -> None:
        """No-op critical method."""

    @override
    def exception(self, message: str, **context: Any) -> None:
        """No-op exception method."""
