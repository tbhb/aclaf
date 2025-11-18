from dataclasses import dataclass
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Protocol, TypeAlias, runtime_checkable

if TYPE_CHECKING:
    from aclaf.console import Console

    from ._types import ResponseType


RenderableType: TypeAlias = "ResponseType | Renderable"


@dataclass(slots=True, frozen=True)
class RenderContext:
    pass


class RenderCapability(IntEnum):
    COLOR = auto()

    EMOJI = auto()

    UNICODE = auto()

    ANSI = auto()


@runtime_checkable
class Renderable(Protocol):
    def __render__(
        self, renderer: "Renderer", console: "Console", context: RenderContext
    ) -> None: ...


@runtime_checkable
class Renderer(Protocol):
    def render(
        self, value: RenderableType, console: "Console", context: RenderContext
    ) -> None: ...

    def supports(
        self, capability: RenderCapability, context: RenderContext
    ) -> bool: ...
