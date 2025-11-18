from collections.abc import Mapping, Sequence, Set as AbstractSet
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import IntEnum, auto
from pathlib import Path
from typing import Annotated, Protocol, TypeAlias, runtime_checkable
from typing_extensions import override

from annotated_types import BaseMetadata, Ge, Gt, Le, Lt

from aclaf.parser._types import (
    ParsedParameterValue,
)

__all__ = [
    "FiniteFloat",
    "FromArgument",
    "NegativeFloat",
    "NegativeInt",
    "NonNegativeFloat",
    "NonNegativeInt",
    "NonPositiveFloat",
    "NonPositiveInt",
    "ParameterValueType",
    "PositiveFloat",
    "PositiveInt",
    "PrimitiveType",
    "Strict",
    "StrictBool",
    "StrictFloat",
    "StrictInt",
]


@runtime_checkable
class FromArgument(Protocol):
    @classmethod
    def from_cli_value(
        cls,
        value: "ParsedParameterValue",
        metadata: tuple[BaseMetadata, ...] | None = None,
    ) -> "ParameterValueType": ...


PrimitiveType: TypeAlias = str | int | float | bool


@dataclass(slots=True, frozen=True)
class Strict(BaseMetadata):
    strict: bool = True

    @override
    def __hash__(self) -> int:
        return hash(self.strict)


StrictBool = Annotated[bool, Strict()]

PositiveInt = Annotated[int, Gt(0)]
NegativeInt = Annotated[int, Lt(0)]
NonPositiveInt = Annotated[int, Le(0)]
NonNegativeInt = Annotated[int, Ge(0)]

StrictInt = Annotated[int, Strict()]


@dataclass(slots=True, frozen=True)
class AllowInfNan(BaseMetadata):
    allow_inf_nan: bool = True

    @override
    def __hash__(self) -> int:
        return hash(self.allow_inf_nan)


PositiveFloat = Annotated[float, Gt(0)]
NegativeFloat = Annotated[float, Lt(0)]
NonPositiveFloat = Annotated[float, Le(0)]
NonNegativeFloat = Annotated[float, Ge(0)]

StrictFloat = Annotated[float, Strict()]
FiniteFloat = Annotated[float, AllowInfNan(False)]  # noqa: FBT003


class ParameterKind(IntEnum):
    OPTION = auto()
    POSITIONAL = auto()


ParameterValueType: TypeAlias = (
    PrimitiveType
    | StrictBool
    | PositiveInt
    | NegativeInt
    | NonPositiveInt
    | NonNegativeInt
    | StrictInt
    | PositiveFloat
    | NegativeFloat
    | NonPositiveFloat
    | NonNegativeFloat
    | StrictFloat
    | FiniteFloat
    | Path
    | ParsedParameterValue
    | FromArgument
    | date
    | datetime
    | time
    | timedelta
    | Sequence[PrimitiveType | Sequence[PrimitiveType]]
    | AbstractSet[PrimitiveType]
    | Mapping[str | int, PrimitiveType | Sequence[PrimitiveType]]
)

ParameterValueMappingType: TypeAlias = Mapping[str, ParameterValueType | None]
