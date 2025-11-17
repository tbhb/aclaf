from annotated_types import Ge, Gt, Le, Lt, MaxLen, MinLen, MultipleOf, Predicate

from aclaf.validators._registry import ValidatorRegistry
from aclaf.validators._shared import validate_predicate

from ._comparison import (
    validate_ge,
    validate_gt,
    validate_le,
    validate_lt,
    validate_max_len,
    validate_min_len,
)
from ._numeric import validate_multiple_of
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
from ._string import (
    Alpha,
    Alphanumeric,
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
    "Alpha",
    "Alphanumeric",
    "Contains",
    "EndsWith",
    "HasExtensions",
    "IsDirectory",
    "IsExecutable",
    "IsFile",
    "IsReadable",
    "IsWritable",
    "Lowercase",
    "NotBlank",
    "Numeric",
    "PathExists",
    "Pattern",
    "Printable",
    "StartsWith",
    "StringValidations",
    "StringValidations",
    "Uppercase",
    "validate_alpha",
    "validate_alphanumeric",
    "validate_contains",
    "validate_ends_with",
    "validate_ge",
    "validate_gt",
    "validate_has_extensions",
    "validate_is_directory",
    "validate_is_executable",
    "validate_is_file",
    "validate_is_readable",
    "validate_is_writable",
    "validate_le",
    "validate_lowercase",
    "validate_lt",
    "validate_multiple_of",
    "validate_not_blank",
    "validate_numeric",
    "validate_path_exists",
    "validate_pattern",
    "validate_printable",
    "validate_starts_with",
    "validate_uppercase",
]


def default_parameter_validators() -> ValidatorRegistry:
    registry = ValidatorRegistry()

    # Shared validators
    registry.register(Predicate, validate_predicate)

    # Comparison validators
    registry.register(Gt, validate_gt)
    registry.register(Ge, validate_ge)
    registry.register(Lt, validate_lt)
    registry.register(Le, validate_le)
    registry.register(MinLen, validate_min_len)
    registry.register(MaxLen, validate_max_len)

    # Numeric validators
    registry.register(MultipleOf, validate_multiple_of)

    # String validators
    registry.register(NotBlank, validate_not_blank)
    registry.register(Pattern, validate_pattern)
    registry.register(Printable, validate_printable)
    registry.register(StartsWith, validate_starts_with)
    registry.register(EndsWith, validate_ends_with)
    registry.register(Contains, validate_contains)
    registry.register(Lowercase, validate_lowercase)
    registry.register(Uppercase, validate_uppercase)
    registry.register(Alphanumeric, validate_alphanumeric)
    registry.register(Alpha, validate_alpha)
    registry.register(Numeric, validate_numeric)

    # Path validators
    registry.register(PathExists, validate_path_exists)
    registry.register(IsFile, validate_is_file)
    registry.register(IsDirectory, validate_is_directory)
    registry.register(IsReadable, validate_is_readable)
    registry.register(IsWritable, validate_is_writable)
    registry.register(IsExecutable, validate_is_executable)
    registry.register(HasExtensions, validate_has_extensions)

    return registry
