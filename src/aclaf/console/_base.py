import sys
from abc import ABC, abstractmethod
from typing import Any, TextIO

DEFAULT_SEP: str = " "
DEFAULT_END: str = "\n"


class BaseConsole(ABC):
    """Base class for console implementations."""

    def __init__(self, file: TextIO | None = None) -> None:
        self._file: TextIO = file or sys.stdout

    @abstractmethod
    def print(
        self,
        *objects: Any,  # pyright: ignore[reportExplicitAny, reportAny]
        sep: str = DEFAULT_SEP,
        end: str = DEFAULT_END,
        flush: bool = False,
    ) -> None: ...
