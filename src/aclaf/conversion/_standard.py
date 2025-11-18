from pathlib import Path
from typing import TYPE_CHECKING

from ._exceptions import ConversionError

if TYPE_CHECKING:
    from annotated_types import BaseMetadata

    from aclaf.parser import ParsedParameterValue


def convert_str(
    value: "ParsedParameterValue | None",
    _metadata: tuple["BaseMetadata", ...] | None = None,
) -> str:
    """Convert a parsed value to string.

    Args:
        value: The value to convert (None returns empty string)
        _metadata: Unused metadata parameter

    Returns:
        The value as a string
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def convert_int(
    value: "ParsedParameterValue | None",
    _metadata: tuple["BaseMetadata", ...] | None = None,
) -> int:
    """Convert a parsed value to integer.

    Args:
        value: The value to convert
        _metadata: Unused metadata parameter

    Returns:
        The value as an integer

    Raises:
        ValueError: If the value cannot be converted to int or is None
    """
    if value is None:
        msg = "Cannot convert None to int"
        raise ValueError(msg)
    if isinstance(value, int):
        return value
    # Type ignore: ParsedParameterValue includes tuples, but converter registry
    # ensures this is only called for convertible values (str, bool, int)
    return int(value)  # pyright: ignore[reportArgumentType]


def convert_float(
    value: "ParsedParameterValue | None",
    _metadata: tuple["BaseMetadata", ...] | None = None,
) -> float:
    """Convert a parsed value to float.

    Args:
        value: The value to convert
        _metadata: Unused metadata parameter

    Returns:
        The value as a float

    Raises:
        ValueError: If the value cannot be converted to float or is None
    """
    if value is None:
        msg = "Cannot convert None to float"
        raise ValueError(msg)
    if isinstance(value, float):
        return value
    # Type ignore: ParsedParameterValue includes tuples, but converter registry
    # ensures this is only called for convertible values (str, bool, int, float)
    return float(value)  # pyright: ignore[reportArgumentType]


def convert_bool(
    value: "ParsedParameterValue | None",
    _metadata: tuple["BaseMetadata", ...] | None = None,
) -> bool:
    """Convert a parsed value to boolean.

    Recognizes common boolean string representations:
    - True: 'true', '1', 'yes', 'on' (case-insensitive)
    - False: 'false', '0', 'no', 'off' (case-insensitive)

    Args:
        value: The value to convert
        _metadata: Unused metadata parameter

    Returns:
        The value as a boolean

    Raises:
        ValueError: If the value cannot be recognized as a boolean or is None
    """
    if value is None:
        msg = "Cannot convert None to bool"
        raise ValueError(msg)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)  # 0 → False, non-zero → True
    if isinstance(value, str):
        val_lower = value.lower()
        if val_lower in ("true", "1", "yes", "on"):
            return True
        if val_lower in ("false", "0", "no", "off"):
            return False
    msg = f"Cannot convert '{value}' to bool."
    raise ValueError(msg)


def convert_path(
    value: "ParsedParameterValue | None",
    _metadata: tuple["BaseMetadata", ...] | None = None,
) -> Path:
    if value is None:
        raise ConversionError(None, Path, "Cannot convert None to Path")
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise ConversionError(value, Path, f"Cannot convert {type(value).__name__} to Path")
