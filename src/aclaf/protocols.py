from typing import Protocol, runtime_checkable
from typing_extensions import override

__all__ = ["Printable"]


@runtime_checkable
class Printable(Protocol):
    @override
    def __str__(self) -> str: ...
