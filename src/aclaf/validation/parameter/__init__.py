from annotated_types import (
    Ge,
    Gt,
    Interval,
    Le,
    Lt,
    MaxLen,
    MinLen,
    MultipleOf,
    Predicate,
)

from aclaf.validation._registry import ValidatorRegistry
from aclaf.validation._shared import validate_predicate

from ._comparison import (
    validate_ge,
    validate_gt,
    validate_le,
    validate_lt,
    validate_max_len,
    validate_min_len,
)
from ._datetime import (
    AfterDate,
    AfterDatetime,
    BeforeDate,
    BeforeDatetime,
    DateRange,
    DatetimeRange,
    MaxTimedelta,
    MinTimedelta,
    TimedeltaRange,
    validate_after_date,
    validate_after_datetime,
    validate_before_date,
    validate_before_datetime,
    validate_date_range,
    validate_datetime_range,
    validate_max_timedelta,
    validate_min_timedelta,
    validate_timedelta_range,
    validate_timezone,
)
from ._mapping import (
    ForbiddenKeys,
    KeyPattern,
    MaxKeys,
    MinKeys,
    RequiredKeys,
    ValuePattern,
    ValueType,
    validate_forbidden_keys,
    validate_key_pattern,
    validate_max_keys,
    validate_min_keys,
    validate_required_keys,
    validate_value_pattern,
    validate_value_type,
)
from ._numeric import (
    IsInteger,
    IsNegative,
    IsNonNegative,
    IsNonPositive,
    IsPositive,
    Precision,
    validate_interval,
    validate_is_integer,
    validate_is_negative,
    validate_is_non_negative,
    validate_is_non_positive,
    validate_is_positive,
    validate_multiple_of,
    validate_precision,
)
from ._path import (
    HasExtensions,
    IsDirectory,
    IsExecutable,
    IsFile,
    IsReadable,
    IsWritable,
    PathExists,
    validate_has_extensions,
    validate_is_directory,
    validate_is_executable,
    validate_is_file,
    validate_is_readable,
    validate_is_writable,
    validate_path_exists,
)
from ._sequence import (
    AllMatch,
    AnyMatch,
    ItemType,
    NoneMatch,
    SequenceContains,
    UniqueItems,
    validate_all_match,
    validate_any_match,
    validate_item_type,
    validate_none_match,
    validate_sequence_contains,
    validate_unique_items,
)
from ._string import (
    Alpha,
    Alphanumeric,
    Choices,
    Contains,
    EndsWith,
    Lowercase,
    NotBlank,
    Numeric,
    Pattern,
    Printable,
    StartsWith,
    StringValidations,
    Uppercase,
    validate_alpha,
    validate_alphanumeric,
    validate_choices,
    validate_contains,
    validate_ends_with,
    validate_lowercase,
    validate_not_blank,
    validate_numeric,
    validate_pattern,
    validate_printable,
    validate_starts_with,
    validate_uppercase,
)

__all__ = [
    "AfterDate",
    "AfterDatetime",
    "AllMatch",
    "Alpha",
    "Alphanumeric",
    "AnyMatch",
    "BeforeDate",
    "BeforeDatetime",
    "Choices",
    "Contains",
    "DateRange",
    "DatetimeRange",
    "EndsWith",
    "ForbiddenKeys",
    "HasExtensions",
    "IsDirectory",
    "IsExecutable",
    "IsFile",
    "IsInteger",
    "IsNegative",
    "IsNonNegative",
    "IsNonPositive",
    "IsPositive",
    "IsReadable",
    "IsWritable",
    "ItemType",
    "KeyPattern",
    "Lowercase",
    "MaxKeys",
    "MaxTimedelta",
    "MinKeys",
    "MinTimedelta",
    "NoneMatch",
    "NotBlank",
    "Numeric",
    "PathExists",
    "Pattern",
    "Precision",
    "Printable",
    "RequiredKeys",
    "SequenceContains",
    "StartsWith",
    "StringValidations",
    "TimedeltaRange",
    "UniqueItems",
    "Uppercase",
    "ValuePattern",
    "ValueType",
    "validate_after_date",
    "validate_after_datetime",
    "validate_all_match",
    "validate_alpha",
    "validate_alphanumeric",
    "validate_any_match",
    "validate_before_date",
    "validate_before_datetime",
    "validate_choices",
    "validate_contains",
    "validate_date_range",
    "validate_datetime_range",
    "validate_ends_with",
    "validate_forbidden_keys",
    "validate_ge",
    "validate_gt",
    "validate_has_extensions",
    "validate_interval",
    "validate_is_directory",
    "validate_is_executable",
    "validate_is_file",
    "validate_is_integer",
    "validate_is_negative",
    "validate_is_non_negative",
    "validate_is_non_positive",
    "validate_is_positive",
    "validate_is_readable",
    "validate_is_writable",
    "validate_item_type",
    "validate_key_pattern",
    "validate_le",
    "validate_lowercase",
    "validate_lt",
    "validate_max_keys",
    "validate_max_len",
    "validate_max_timedelta",
    "validate_min_keys",
    "validate_min_len",
    "validate_min_timedelta",
    "validate_multiple_of",
    "validate_none_match",
    "validate_not_blank",
    "validate_numeric",
    "validate_path_exists",
    "validate_pattern",
    "validate_precision",
    "validate_printable",
    "validate_required_keys",
    "validate_sequence_contains",
    "validate_starts_with",
    "validate_timedelta_range",
    "validate_timezone",
    "validate_unique_items",
    "validate_uppercase",
    "validate_value_pattern",
    "validate_value_type",
]


def _create_default_parameter_validators() -> ValidatorRegistry:
    """Creates default parameter validator registry.

    This function is called once at module initialization to populate
    the default validator registry. The registry is cached at module level.
    """
    registry = ValidatorRegistry()

    # Shared validators
    registry.register(Predicate, validate_predicate)

    # Comparison validators (from annotated-types)
    registry.register(Gt, validate_gt)
    registry.register(Ge, validate_ge)
    registry.register(Lt, validate_lt)
    registry.register(Le, validate_le)
    registry.register(MinLen, validate_min_len)
    registry.register(MaxLen, validate_max_len)

    # Numeric validators
    registry.register(MultipleOf, validate_multiple_of)
    registry.register(Interval, validate_interval)  # from annotated-types
    registry.register(IsInteger, validate_is_integer)
    registry.register(IsPositive, validate_is_positive)
    registry.register(IsNegative, validate_is_negative)
    registry.register(IsNonNegative, validate_is_non_negative)
    registry.register(IsNonPositive, validate_is_non_positive)
    registry.register(Precision, validate_precision)

    # Datetime validators
    # Timezone validator disabled - placeholder with no implementation
    # TODO(@maintainer): Implement using zoneinfo.available_timezones()
    # or remove entirely
    # registry.register(Timezone, validate_timezone)  # from annotated-types
    registry.register(AfterDate, validate_after_date)
    registry.register(BeforeDate, validate_before_date)
    registry.register(DateRange, validate_date_range)
    registry.register(AfterDatetime, validate_after_datetime)
    registry.register(BeforeDatetime, validate_before_datetime)
    registry.register(DatetimeRange, validate_datetime_range)
    registry.register(MinTimedelta, validate_min_timedelta)
    registry.register(MaxTimedelta, validate_max_timedelta)
    registry.register(TimedeltaRange, validate_timedelta_range)

    # Sequence validators
    registry.register(UniqueItems, validate_unique_items)
    registry.register(SequenceContains, validate_sequence_contains)
    registry.register(AllMatch, validate_all_match)
    registry.register(AnyMatch, validate_any_match)
    registry.register(NoneMatch, validate_none_match)
    registry.register(ItemType, validate_item_type)

    # Mapping validators
    registry.register(RequiredKeys, validate_required_keys)
    registry.register(ForbiddenKeys, validate_forbidden_keys)
    registry.register(KeyPattern, validate_key_pattern)
    registry.register(ValuePattern, validate_value_pattern)
    registry.register(ValueType, validate_value_type)
    registry.register(MinKeys, validate_min_keys)
    registry.register(MaxKeys, validate_max_keys)

    # String validators - DISABLED: All are placeholders with no implementation
    # TODO(@maintainer): Implement and re-enable when ready
    # registry.register(NotBlank, validate_not_blank)
    registry.register(Pattern, validate_pattern)
    # registry.register(Printable, validate_printable)
    # registry.register(StartsWith, validate_starts_with)
    # registry.register(EndsWith, validate_ends_with)
    # registry.register(Contains, validate_contains)
    # registry.register(Lowercase, validate_lowercase)
    # registry.register(Uppercase, validate_uppercase)
    # registry.register(Alphanumeric, validate_alphanumeric)
    # registry.register(Alpha, validate_alpha)
    # registry.register(Numeric, validate_numeric)

    # Path validators - DISABLED: All are placeholders with no implementation
    # TODO(@maintainer): Implement and re-enable when ready
    # registry.register(PathExists, validate_path_exists)
    # registry.register(IsFile, validate_is_file)
    # registry.register(IsDirectory, validate_is_directory)
    # registry.register(IsReadable, validate_is_readable)
    # registry.register(IsWritable, validate_is_writable)
    # registry.register(IsExecutable, validate_is_executable)
    # registry.register(HasExtensions, validate_has_extensions)

    return registry


# Module-level singleton - initialized once at import time
_DEFAULT_PARAMETER_VALIDATORS: ValidatorRegistry = (
    _create_default_parameter_validators()
)


def default_parameter_validators() -> ValidatorRegistry:
    """Returns cached default parameter validator registry.

    Note: This registry is shared across all callers. Modifications to the
    returned registry will affect all subsequent calls. This is not thread-safe
    for concurrent modifications.
    """
    return _DEFAULT_PARAMETER_VALIDATORS
