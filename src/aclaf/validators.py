from dataclasses import dataclass
from typing_extensions import override

from annotated_types import (
    BaseMetadata,
    Ge,
    GroupedMetadata,
    Gt,
    Interval,
    Le,
    Lt,
    MaxLen,
    MinLen,
    MultipleOf,
    Not,
    Predicate,
    Timezone,
)

__all__ = [
    "BaseMetadata",
    "Ge",
    "GroupedMetadata",
    "Gt",
    "Interval",
    "Le",
    "Lt",
    "MaxLen",
    "MinLen",
    "MultipleOf",
    "Not",
    "Predicate",
    "Required",
    "Timezone",
]


@dataclass(slots=True, frozen=True)
class Required(BaseMetadata):
    required: bool = True

    @override
    def __hash__(self) -> int:
        return hash(self.required)


@dataclass(slots=True, frozen=True)
class NotBlank(BaseMetadata):
    not_blank: bool = True

    @override
    def __hash__(self) -> int:
        return hash(self.not_blank)
