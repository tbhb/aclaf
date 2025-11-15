import re
from typing import Final

COMMAND_NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9-_]*$")

DEFAULT_TRUTHY_VALUES = ("true", "1", "yes", "on")
DEFAULT_FALSEY_VALUES = ("false", "0", "no", "off")

DEFAULT_NEGATIVE_NUMBER_PATTERN: Final[str] = (
    r"^-\d+\.?\d*([eE][+-]?\d+)?([+-]\d+\.?\d*([eE][+-]?\d+)?j|j)?$"
)
"""Default regex pattern for matching negative numbers including complex numbers.

Matches:
    - Integers: -1, -42, -999
    - Decimals: -3.14, -0.5, -100.0
    - Scientific notation: -1e5, -2.5E-10, -6.022e23
    - Complex numbers: -3+4j, -3-4j, -4j, -1.5+2.5j
    - Complex with scientific: -1e5+2e3j, -2.5E-10-3.14E-5j

Does NOT match:
    - Leading decimal: -.5 (use custom pattern)
    - Long options: --1
    - Non-numeric: -abc
    - Positive complex: 3+4j (handled as normal value, no special treatment needed)

Note: Complex numbers are treated as strings by the parser. The application is
responsible for parsing and validating complex number values.
"""
