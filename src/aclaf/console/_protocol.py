from typing import Protocol, runtime_checkable


@runtime_checkable
class Console(Protocol):
    def print(self, *objects: object, sep: str = " ", end: str = "\n") -> None: ...


@runtime_checkable
class SupportsConsole(Protocol):
    def __console__(self, console: "Console") -> None: ...
