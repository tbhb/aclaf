# pyright: reportAny=false, reportExplicitAny=false, reportUnusedParameter=false

from typing import Any
from typing_extensions import override

from ._protocol import Logger


class MockLogger(Logger):
    """Mock logger implementation for testing logging behavior."""

    def __init__(self) -> None:
        self.logs: list[tuple[str, str, dict[str, Any]]] = []

    @override
    def debug(self, message: str, **context: Any) -> None:
        self.logs.append(("debug", message, context))

    @override
    def info(self, message: str, **context: Any) -> None:
        self.logs.append(("info", message, context))

    @override
    def warning(self, message: str, **context: Any) -> None:
        self.logs.append(("warning", message, context))

    @override
    def error(self, message: str, **context: Any) -> None:
        self.logs.append(("error", message, context))

    @override
    def critical(self, message: str, **context: Any) -> None:
        self.logs.append(("critical", message, context))

    @override
    def exception(self, message: str, **context: Any) -> None:
        self.logs.append(("exception", message, context))
