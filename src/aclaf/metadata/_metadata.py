from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias
from typing_extensions import override

from annotated_types import BaseMetadata

if TYPE_CHECKING:
    from aclaf.conversion import ConverterFunctionType
    from aclaf.types import ParameterValueType


MetadataType: TypeAlias = BaseMetadata | str | int

MetadataByType: TypeAlias = MappingProxyType[type[BaseMetadata], BaseMetadata]


@dataclass(slots=True, frozen=True)
class CommandMetadata(BaseMetadata):
    """Base class for command-scoped metadata."""


@dataclass(slots=True, frozen=True)
class ParameterMetadata(BaseMetadata):
    """Base class for parameter-scoped metadata."""


# Parsing


class Arg(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class ExactlyOne(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class AtLeastOne(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class AtMostOne(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class ZeroOrMore(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class FirstWins(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class LastWins(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class Collect(ParameterMetadata):
    flatten: bool = False


@dataclass(slots=True, frozen=True)
class Count(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class ErrorOnDuplicate(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class Opt(ParameterMetadata):
    multiple: bool = False
    flatten: bool = False


@dataclass(slots=True, frozen=True)
class Flag(ParameterMetadata):
    const: str | None = None
    falsey: tuple[str, ...] | None = None
    truthy: tuple[str, ...] | None = None
    negation: tuple[str, ...] | None = None
    count: bool = False


@dataclass(slots=True, frozen=True)
class Default(ParameterMetadata):
    value: "ParameterValueType"


@dataclass(slots=True, frozen=True)
class Convert(ParameterMetadata):
    func: "ConverterFunctionType"


# Help


@dataclass(slots=True, frozen=True)
class Usage(ParameterMetadata):
    text: str


@dataclass(slots=True, frozen=True)
class MetaVar(ParameterMetadata):
    name: str


# Validations


## Command-level validations


## Presence validations


@dataclass(slots=True, frozen=True)
class Required(BaseMetadata):
    required: bool = True

    @override
    def __hash__(self) -> int:
        return hash(self.required)


## String validations


## Path validations
