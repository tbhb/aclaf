from typing import Final

DEFAULT_TRUTHY_VALUES = ("true", "1", "yes", "on")
DEFAULT_FALSEY_VALUES = ("false", "0", "no", "off")

DEFAULT_NEGATIVE_NUMBER_PATTERN: Final[str] = r"^-\d+\.?\d*([eE][+-]?\d+)?$"
"""Default regex pattern for matching negative numbers.

Matches:
    - Integers: -1, -42, -999
    - Decimals: -3.14, -0.5, -100.0
    - Scientific notation: -1e5, -2.5E-10, -6.022e23

Does NOT match:
    - Leading decimal: -.5 (use custom pattern)
    - Long options: --1
    - Non-numeric: -abc
"""
