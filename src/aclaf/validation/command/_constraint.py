from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from annotated_types import BaseMetadata

if TYPE_CHECKING:
    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validators._registry import ValidatorMetadataType


@dataclass(slots=True, frozen=True)
class MutuallyExclusive(BaseMetadata):
    parameter_names: tuple[str, ...]


def validate_mutually_exclusive(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("MutuallyExclusive", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class ExactlyOneOf(BaseMetadata):
    parameter_names: tuple[str, ...]


def validate_exactly_one_of(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("ExactlyOneOf", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class AtLeastOneOf(BaseMetadata):
    parameter_names: tuple[str, ...]


def validate_at_least_one_of(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("AtLeastOneOf", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class AtMostOneOf(BaseMetadata):
    parameter_names: tuple[str, ...]


def validate_at_most_one_of(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("AtMostOneOf", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None
