from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from annotated_types import (
        Ge,
        Gt,
        Le,
        Lt,
        MaxLen,
        MinLen,
    )

    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validators._registry import ValidatorMetadataType


def validate_gt(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    gt_meta = cast("Gt", metadata)
    errors: list[str] = []
    try:
        if not value > gt_meta.gt:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be greater than {gt_meta.gt}.")
    except TypeError:
        errors.append(f"cannot be compared with {gt_meta.gt}.")

    if errors:
        return tuple(errors)
    return None


def validate_ge(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    ge_meta = cast("Ge", metadata)
    errors: list[str] = []
    try:
        if not value >= ge_meta.ge:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be greater than or equal to {ge_meta.ge}.")
    except TypeError:
        errors.append(f"cannot be compared with {ge_meta.ge}.")

    if errors:
        return tuple(errors)
    return None


def validate_lt(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    lt_meta = cast("Lt", metadata)
    errors: list[str] = []
    try:
        if not value < lt_meta.lt:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be less than {lt_meta.lt}.")
    except TypeError:
        errors.append(f"cannot be compared with {lt_meta.lt}.")

    if errors:
        return tuple(errors)
    return None


def validate_le(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    le_meta = cast("Le", metadata)
    errors: list[str] = []
    try:
        if not value <= le_meta.le:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be less than or equal to {le_meta.le}.")
    except TypeError:
        errors.append(f"cannot be compared with {le_meta.le}.")

    if errors:
        return tuple(errors)
    return None


def validate_min_len(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    min_len_meta = cast("MinLen", metadata)
    errors: list[str] = []
    try:
        if len(value) < min_len_meta.min_length:  # pyright: ignore[reportArgumentType]
            errors.append(f"length must be at least {min_len_meta.min_length}.")
    except TypeError:
        errors.append("length cannot be determined.")

    if errors:
        return tuple(errors)
    return None


def validate_max_len(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    max_len_meta = cast("MaxLen", metadata)
    errors: list[str] = []
    try:
        if len(value) > max_len_meta.max_length:  # pyright: ignore[reportArgumentType]
            errors.append(f"length must be at most {max_len_meta.max_length}.")
    except TypeError:
        errors.append("length cannot be determined.")

    if errors:
        return tuple(errors)
    return None
