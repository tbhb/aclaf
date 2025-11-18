"""Mapping domain validators for parameter-scoped validation.

This module provides validators for dictionary/mapping values:
- RequiredKeys: Specific keys must be present
- ForbiddenKeys: Specific keys must not be present
- KeyPattern: Keys must match regex pattern
- ValuePattern: Values must match regex pattern (string values)
- ValueType: Values must be of specified type(s)
- MinKeys: Minimum number of keys
- MaxKeys: Maximum number of keys
"""

import re
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from annotated_types import BaseMetadata

if TYPE_CHECKING:
    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validation._registry import ValidatorMetadataType

MAX_ERROR_DISPLAY_ITEMS = 5


@dataclass(slots=True, frozen=True)
class RequiredKeys(BaseMetadata):
    """Specific keys must be present in mapping."""

    keys: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ForbiddenKeys(BaseMetadata):
    """Specific keys must not be present in mapping."""

    keys: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class KeyPattern(BaseMetadata):
    """Keys must match regex pattern."""

    pattern: str


@dataclass(slots=True, frozen=True)
class ValuePattern(BaseMetadata):
    """String values must match regex pattern."""

    pattern: str


@dataclass(slots=True, frozen=True)
class ValueType(BaseMetadata):
    """Values must be of specified type(s)."""

    types: tuple[type, ...]


@dataclass(slots=True, frozen=True)
class MinKeys(BaseMetadata):
    """Minimum number of keys."""

    min_keys: int


@dataclass(slots=True, frozen=True)
class MaxKeys(BaseMetadata):
    """Maximum number of keys."""

    max_keys: int


def validate_required_keys(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate required keys are present."""
    required_meta = cast("RequiredKeys", metadata)

    if value is None:
        return None

    if not isinstance(value, MappingABC):
        return ("must be a mapping (dict).",)

    missing = [key for key in required_meta.keys if key not in value]

    if missing:
        missing_str = ", ".join(repr(m) for m in missing)
        return (f"missing required keys: {missing_str}.",)

    return None


def validate_forbidden_keys(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate forbidden keys are not present."""
    forbidden_meta = cast("ForbiddenKeys", metadata)

    if value is None:
        return None

    if not isinstance(value, MappingABC):
        return ("must be a mapping (dict).",)

    present = [key for key in forbidden_meta.keys if key in value]

    if present:
        present_str = ", ".join(repr(p) for p in present)
        return (f"forbidden keys present: {present_str}.",)

    return None


def validate_key_pattern(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate keys match regex pattern."""
    pattern_meta = cast("KeyPattern", metadata)

    if value is None:
        return None

    if not isinstance(value, MappingABC):
        return ("must be a mapping (dict).",)

    try:
        compiled_pattern = re.compile(pattern_meta.pattern)
    except re.error as e:
        return (f"invalid regex pattern: {e}",)

    invalid_keys = [
        key for key in value
        if not isinstance(key, str) or not compiled_pattern.match(key)
    ]

    if invalid_keys:
        invalid_str = ", ".join(
            repr(k) for k in invalid_keys[:MAX_ERROR_DISPLAY_ITEMS]
        )
        count = len(invalid_keys)
        if count > MAX_ERROR_DISPLAY_ITEMS:
            return (
                (
                    f"{count} keys do not match pattern '{pattern_meta.pattern}'. "
                    f"First 5: {invalid_str}..."
                ),
            )
        return (
            (
                f"keys must match pattern '{pattern_meta.pattern}'. "
                f"Invalid: {invalid_str}."
            ),
        )

    return None


def validate_value_pattern(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate string values match regex pattern."""
    pattern_meta = cast("ValuePattern", metadata)

    if value is None:
        return None

    if not isinstance(value, MappingABC):
        return ("must be a mapping (dict).",)

    try:
        compiled_pattern = re.compile(pattern_meta.pattern)
    except re.error as e:
        return (f"invalid regex pattern: {e}",)

    invalid_values: list[tuple[object, object]] = []
    for k, v in value.items():
        if isinstance(v, str) and not compiled_pattern.match(v):
            invalid_values.append((k, v))

    if invalid_values:
        invalid_str = ", ".join(
            f"{k!r}={v!r}" for k, v in invalid_values[:MAX_ERROR_DISPLAY_ITEMS]
        )
        count = len(invalid_values)
        if count > MAX_ERROR_DISPLAY_ITEMS:
            return (
                (
                    f"{count} values do not match pattern '{pattern_meta.pattern}'. "
                    f"First 5: {invalid_str}..."
                ),
            )
        return (
            (
                f"values must match pattern '{pattern_meta.pattern}'. "
                f"Invalid: {invalid_str}."
            ),
        )

    return None


def validate_value_type(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate values are of specified type(s)."""
    value_type_meta = cast("ValueType", metadata)

    if value is None:
        return None

    if not isinstance(value, MappingABC):
        return ("must be a mapping (dict).",)

    invalid_values: list[tuple[object, object]] = []
    for k, v in value.items():
        if not isinstance(v, value_type_meta.types):
            invalid_values.append((k, v))

    if invalid_values:
        type_names = ", ".join(t.__name__ for t in value_type_meta.types)
        invalid_str = ", ".join(
            f"{k!r}={v!r} ({type(v).__name__})"
            for k, v in invalid_values[:MAX_ERROR_DISPLAY_ITEMS]
        )
        count = len(invalid_values)
        if count > MAX_ERROR_DISPLAY_ITEMS:
            return (
                (
                    f"{count} values are not of type {type_names}. "
                    f"First 5: {invalid_str}..."
                ),
            )
        return (
            (
                f"all values must be of type {type_names}. "
                f"Invalid: {invalid_str}."
            ),
        )

    return None


def validate_min_keys(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate minimum number of keys."""
    min_meta = cast("MinKeys", metadata)

    if value is None:
        return None

    if not isinstance(value, MappingABC):
        return ("must be a mapping (dict).",)

    if len(value) < min_meta.min_keys:
        return (
            f"must have at least {min_meta.min_keys} keys, got {len(value)}.",
        )

    return None


def validate_max_keys(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate maximum number of keys."""
    max_meta = cast("MaxKeys", metadata)

    if value is None:
        return None

    if not isinstance(value, MappingABC):
        return ("must be a mapping (dict).",)

    if len(value) > max_meta.max_keys:
        return (
            f"must have at most {max_meta.max_keys} keys, got {len(value)}.",
        )

    return None
