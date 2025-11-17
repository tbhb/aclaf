from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from annotated_types import Predicate

    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validators._registry import ValidatorMetadataType


def validate_predicate(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("Predicate", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None
