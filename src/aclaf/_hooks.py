from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Sequence


class Hook(Protocol):
    pass


H = TypeVar("H", bound=Hook)


@dataclass(slots=True)
class HookRegistry:
    hooks: dict[type, list[Hook]] = field(default_factory=dict, init=False, repr=False)

    def register(self, hook: Hook) -> None:
        hook_type = type(hook)
        if hook_type not in self.hooks:
            self.hooks[hook_type] = []
        self.hooks[hook_type].append(hook)

    def unregister(self, hook: Hook) -> None:
        hook_type = type(hook)
        if hook_type in self.hooks:
            self.hooks[hook_type].remove(hook)
            if not self.hooks[hook_type]:
                del self.hooks[hook_type]

    def get_hooks(self, hook_type: type[H]) -> "Sequence[H]":
        return cast("Sequence[H]", self.hooks.get(hook_type, []))
