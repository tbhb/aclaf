from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ._base import BaseConsole


@runtime_checkable
class SupportsConsole(Protocol):
    def __console__(self, console: "BaseConsole") -> None: ...
