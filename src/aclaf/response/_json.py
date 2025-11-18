from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing_extensions import override

from ._protocol import RenderableType, RenderCapability, RenderContext, Renderer

if TYPE_CHECKING:
    from aclaf.console import Console


@dataclass(slots=True, frozen=True)
class JSONRenderer(Renderer):
    @override
    def render(
        self, value: "RenderableType", console: "Console", context: RenderContext
    ) -> None:
        console.print(value)

    @override
    def supports(self, capability: RenderCapability, context: RenderContext) -> bool:
        return True
