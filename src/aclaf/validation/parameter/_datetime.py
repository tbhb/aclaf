"""Datetime domain validators for parameter-scoped validation.

This module provides validators for datetime, date, and timedelta values:
- Timezone: Timezone constraint (from annotated-types)
- AfterDate: Date must be after specified date
- BeforeDate: Date must be before specified date
- DateRange: Date within inclusive/exclusive range
- AfterDatetime: Datetime must be after specified datetime
- BeforeDatetime: Datetime must be before specified datetime
- DatetimeRange: Datetime within inclusive/exclusive range
- MinTimedelta: Timedelta >= minimum duration
- MaxTimedelta: Timedelta <= maximum duration
- TimedeltaRange: Timedelta within range
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, cast

from annotated_types import BaseMetadata

if TYPE_CHECKING:
    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validation._registry import ValidatorMetadataType


@dataclass(slots=True, frozen=True)
class AfterDate(BaseMetadata):
    """Date must be after specified date."""

    after: date


@dataclass(slots=True, frozen=True)
class BeforeDate(BaseMetadata):
    """Date must be before specified date."""

    before: date


@dataclass(slots=True, frozen=True)
class DateRange(BaseMetadata):
    """Date within inclusive/exclusive range."""

    after: date | None = None
    before: date | None = None
    inclusive_after: bool = False
    inclusive_before: bool = False


@dataclass(slots=True, frozen=True)
class AfterDatetime(BaseMetadata):
    """Datetime must be after specified datetime."""

    after: datetime


@dataclass(slots=True, frozen=True)
class BeforeDatetime(BaseMetadata):
    """Datetime must be before specified datetime."""

    before: datetime


@dataclass(slots=True, frozen=True)
class DatetimeRange(BaseMetadata):
    """Datetime within inclusive/exclusive range."""

    after: datetime | None = None
    before: datetime | None = None
    inclusive_after: bool = False
    inclusive_before: bool = False


@dataclass(slots=True, frozen=True)
class MinTimedelta(BaseMetadata):
    """Timedelta >= minimum duration."""

    min_duration: timedelta


@dataclass(slots=True, frozen=True)
class MaxTimedelta(BaseMetadata):
    """Timedelta <= maximum duration."""

    max_duration: timedelta


@dataclass(slots=True, frozen=True)
class TimedeltaRange(BaseMetadata):
    """Timedelta within range."""

    min_duration: timedelta | None = None
    max_duration: timedelta | None = None


def validate_timezone(
    _value: "ParameterValueType | ParameterValueMappingType | None",
    _metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Placeholder for timezone validation.

    TODO: Implement using zoneinfo.available_timezones() or remove from registry.
    This validator is currently registered but does no validation.
    """
    # Placeholder - always returns None (no validation)
    return None


def validate_after_date(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate date is after specified date."""
    after_meta = cast("AfterDate", metadata)

    if value is None:
        return None

    if not isinstance(value, (date, datetime)):
        return ("must be a date or datetime.",)

    # Convert datetime to date for comparison
    value_date = value.date() if isinstance(value, datetime) else value

    if not value_date > after_meta.after:
        return (f"must be after {after_meta.after.isoformat()}.",)

    return None


def validate_before_date(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate date is before specified date."""
    before_meta = cast("BeforeDate", metadata)

    if value is None:
        return None

    if not isinstance(value, (date, datetime)):
        return ("must be a date or datetime.",)

    # Convert datetime to date for comparison
    value_date = value.date() if isinstance(value, datetime) else value

    if not value_date < before_meta.before:
        return (f"must be before {before_meta.before.isoformat()}.",)

    return None


def validate_date_range(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate date is within range."""
    range_meta = cast("DateRange", metadata)
    errors: list[str] = []

    if value is None:
        return None

    if not isinstance(value, (date, datetime)):
        return ("must be a date or datetime.",)

    # Convert datetime to date for comparison
    value_date = value.date() if isinstance(value, datetime) else value

    # Check lower bound
    if range_meta.after is not None:
        if range_meta.inclusive_after:
            if not value_date >= range_meta.after:
                errors.append(f"must be on or after {range_meta.after.isoformat()}.")
        elif not value_date > range_meta.after:
            errors.append(f"must be after {range_meta.after.isoformat()}.")

    # Check upper bound
    if range_meta.before is not None:
        if range_meta.inclusive_before:
            if not value_date <= range_meta.before:
                errors.append(f"must be on or before {range_meta.before.isoformat()}.")
        elif not value_date < range_meta.before:
            errors.append(f"must be before {range_meta.before.isoformat()}.")

    if errors:
        return tuple(errors)
    return None


def validate_after_datetime(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate datetime is after specified datetime."""
    after_meta = cast("AfterDatetime", metadata)

    if value is None:
        return None

    if not isinstance(value, datetime):
        return ("must be a datetime.",)

    if not value > after_meta.after:
        return (f"must be after {after_meta.after.isoformat()}.",)

    return None


def validate_before_datetime(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate datetime is before specified datetime."""
    before_meta = cast("BeforeDatetime", metadata)

    if value is None:
        return None

    if not isinstance(value, datetime):
        return ("must be a datetime.",)

    if not value < before_meta.before:
        return (f"must be before {before_meta.before.isoformat()}.",)

    return None


def validate_datetime_range(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate datetime is within range."""
    range_meta = cast("DatetimeRange", metadata)
    errors: list[str] = []

    if value is None:
        return None

    if not isinstance(value, datetime):
        return ("must be a datetime.",)

    # Check lower bound
    if range_meta.after is not None:
        if range_meta.inclusive_after:
            if not value >= range_meta.after:
                errors.append(f"must be on or after {range_meta.after.isoformat()}.")
        elif not value > range_meta.after:
            errors.append(f"must be after {range_meta.after.isoformat()}.")

    # Check upper bound
    if range_meta.before is not None:
        if range_meta.inclusive_before:
            if not value <= range_meta.before:
                errors.append(f"must be on or before {range_meta.before.isoformat()}.")
        elif not value < range_meta.before:
            errors.append(f"must be before {range_meta.before.isoformat()}.")

    if errors:
        return tuple(errors)
    return None


def validate_min_timedelta(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate timedelta >= minimum duration."""
    min_meta = cast("MinTimedelta", metadata)

    if value is None:
        return None

    if not isinstance(value, timedelta):
        return ("must be a timedelta.",)

    if not value >= min_meta.min_duration:
        return (f"must be at least {min_meta.min_duration}.",)

    return None


def validate_max_timedelta(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate timedelta <= maximum duration."""
    max_meta = cast("MaxTimedelta", metadata)

    if value is None:
        return None

    if not isinstance(value, timedelta):
        return ("must be a timedelta.",)

    if not value <= max_meta.max_duration:
        return (f"must be at most {max_meta.max_duration}.",)

    return None


def validate_timedelta_range(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    """Validate timedelta within range."""
    range_meta = cast("TimedeltaRange", metadata)
    errors: list[str] = []

    if value is None:
        return None

    if not isinstance(value, timedelta):
        return ("must be a timedelta.",)

    if range_meta.min_duration is not None and not value >= range_meta.min_duration:
        errors.append(f"must be at least {range_meta.min_duration}.")

    if range_meta.max_duration is not None and not value <= range_meta.max_duration:
        errors.append(f"must be at most {range_meta.max_duration}.")

    if errors:
        return tuple(errors)
    return None
