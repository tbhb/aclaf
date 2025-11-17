from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from annotated_types import BaseMetadata

if TYPE_CHECKING:
    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validators._registry import ValidatorMetadataType


@dataclass(slots=True, frozen=True)
class Requires(BaseMetadata):
    parameter_names: tuple[str, ...]


def validate_requires(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Requires", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class Forbids(BaseMetadata):
    parameter_names: tuple[str, ...]


def validate_forbids(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Forbids", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None
