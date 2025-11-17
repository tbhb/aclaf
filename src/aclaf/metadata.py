from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias
from typing_extensions import override

from annotated_types import BaseMetadata

if TYPE_CHECKING:
    from aclaf._conversion import ConverterFunctionType
    from aclaf._types import ParameterValueType

__all__ = [
    "Arg",
    "AtLeastOne",
    "AtMostOne",
    "Collect",
    "Default",
    "ErrorOnDuplicate",
    "ExactlyOne",
    "FirstWins",
    "Flag",
    "LastWins",
    "MetadataType",
    "Opt",
    "ParameterMetadata",
    "Usage",
    "ZeroOrMore",
]

MetadataType: TypeAlias = BaseMetadata | str | int

MetadataByType: TypeAlias = MappingProxyType[type[BaseMetadata], BaseMetadata]


class ParameterMetadata(BaseMetadata):
    pass


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


@dataclass(slots=True, frozen=True)
class Usage(ParameterMetadata):
    text: str


@dataclass(slots=True, frozen=True)
class MetaVar(ParameterMetadata):
    name: str


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
