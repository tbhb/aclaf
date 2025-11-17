from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from typing_extensions import override

from annotated_types import BaseMetadata, GroupedMetadata

from aclaf.metadata import ParameterMetadata

if TYPE_CHECKING:
    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validators._registry import ValidatorMetadataType


@dataclass(slots=True, frozen=True)
class NotBlank(BaseMetadata):
    not_blank: bool = True

    @override
    def __hash__(self) -> int:
        return hash(self.not_blank)


def validate_not_blank(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("NotBlank", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Pattern(ParameterMetadata):
    pattern: str


def validate_pattern(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Pattern", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Choices(ParameterMetadata):
    choices: tuple[str, ...]


def validate_choices(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Choices", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class StartsWith(ParameterMetadata):
    prefix: str


def validate_starts_with(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("StartsWith", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class EndsWith(ParameterMetadata):
    suffix: str


def validate_ends_with(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("EndsWith", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Contains(ParameterMetadata):
    substring: str


def validate_contains(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Contains", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Lowercase(ParameterMetadata):
    pass


def validate_lowercase(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Lowercase", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Uppercase(ParameterMetadata):
    pass


def validate_uppercase(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Uppercase", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Alphanumeric(ParameterMetadata):
    pass


def validate_alphanumeric(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Alphanumeric", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Alpha(ParameterMetadata):
    pass


def validate_alpha(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Alpha", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Numeric(ParameterMetadata):
    pass


def validate_numeric(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Numeric", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Printable(ParameterMetadata):
    pass


def validate_printable(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Printable", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class StringValidations(GroupedMetadata):
    not_blank: bool = False
    pattern: str | None = None
    choices: tuple[str, ...] | None = None
    starts_with: str | None = None
    ends_with: str | None = None
    contains: str | None = None
    lowercase: bool = False
    uppercase: bool = False
    alphanumeric: bool = False
    alpha: bool = False
    numeric: bool = False
    printable: bool = False

    def __iter__(self) -> Iterator[BaseMetadata]:
        if self.not_blank:
            yield NotBlank()
        if self.pattern is not None:
            yield Pattern(pattern=self.pattern)
        if self.choices is not None:
            yield Choices(choices=self.choices)
        if self.starts_with is not None:
            yield StartsWith(prefix=self.starts_with)
        if self.ends_with is not None:
            yield EndsWith(suffix=self.ends_with)
        if self.contains is not None:
            yield Contains(substring=self.contains)
        if self.lowercase:
            yield Lowercase()
        if self.uppercase:
            yield Uppercase()
        if self.alphanumeric:
            yield Alphanumeric()
        if self.alpha:
            yield Alpha()
        if self.numeric:
            yield Numeric()
        if self.printable:
            yield Printable()
