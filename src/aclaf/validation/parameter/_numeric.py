from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from annotated_types import MultipleOf

    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validators._registry import ValidatorMetadataType


def validate_multiple_of(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    multiple_meta = cast("MultipleOf", metadata)
    errors: list[str] = []
    try:
        if (value % multiple_meta.multiple_of) != 0:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be a multiple of {multiple_meta.multiple_of}.")
    except TypeError:
        errors.append(f"cannot be divided by {multiple_meta.multiple_of}.")

    if errors:
        return tuple(errors)
    return None
