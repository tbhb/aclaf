from collections.abc import Iterable
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias
from typing_extensions import override

from annotated_types import BaseMetadata

if TYPE_CHECKING:
    from aclaf._conversion import ConverterFunctionType
    from aclaf.types import ParameterValueType

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


# Help


@dataclass(slots=True, frozen=True)
class Usage(ParameterMetadata):
    text: str


@dataclass(slots=True, frozen=True)
class MetaVar(ParameterMetadata):
    name: str


# Validations


@dataclass(slots=True, frozen=True)
class Required(BaseMetadata):
    required: bool = True

    @override
    def __hash__(self) -> int:
        return hash(self.required)


## String validations


@dataclass(slots=True, frozen=True)
class NotBlank(BaseMetadata):
    not_blank: bool = True

    @override
    def __hash__(self) -> int:
        return hash(self.not_blank)


@dataclass(slots=True, frozen=True)
class Pattern(ParameterMetadata):
    pattern: str


@dataclass(slots=True, frozen=True)
class Choices(ParameterMetadata):
    choices: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class StartsWith(ParameterMetadata):
    prefix: str


@dataclass(slots=True, frozen=True)
class EndsWith(ParameterMetadata):
    suffix: str


@dataclass(slots=True, frozen=True)
class Contains(ParameterMetadata):
    substring: str


@dataclass(slots=True, frozen=True)
class Lowercase(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class Uppercase(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class Alphanumeric(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class Alpha(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class Numeric(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class Printable(ParameterMetadata):
    pass


## Path validations


@dataclass(slots=True, frozen=True)
class PathExists(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class IsFile(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class IsDirectory(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class IsReadable(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class IsWritable(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class IsExecutable(ParameterMetadata):
    pass


@dataclass(slots=True, frozen=True)
class HasExtensions(ParameterMetadata):
    extensions: str | Iterable[str]
