from enum import Enum
from typing import Final, NamedTuple, override


class AccumulationMode(Enum):
    """Defines how repeated occurrences of the same option are handled.

    When an option is specified multiple times on the command line, the
    accumulation mode determines whether to keep the first value, the last
    value, collect all values, count occurrences, or raise an error.

    Attributes:
        LAST_WINS: Keep only the last value provided. This is the default
            behavior for most options.
        FIRST_WINS: Keep only the first value provided, ignoring subsequent
            occurrences.
        COLLECT: Accumulate all values into a tuple. Each occurrence adds
            its value(s) to the collection.
        COUNT: Count the number of times the option was specified. The
            value becomes an integer count (useful for verbosity flags like -vvv).
        ERROR: Raise an exception if the option is specified more than once.
    """

    LAST_WINS = "last_wins"
    FIRST_WINS = "first_wins"
    COLLECT = "collect"
    COUNT = "count"
    ERROR = "error"


class Arity(NamedTuple):
    """Defines the number of values an option or positional parameter accepts.

    Arity specifies both a minimum and maximum number of values. A maximum
    of None indicates unbounded arity (accepts unlimited values).

    Attributes:
        min: The minimum number of values required.
        max: The maximum number of values allowed, or None for unbounded.

    Examples:
        Arity(1, 1): Exactly one value (the most common case)
        Arity(0, 0): No values (flag options)
        Arity(0, None): Zero or more values (optional variadic)
        Arity(1, None): One or more values (required variadic)
        Arity(2, 5): Between 2 and 5 values (specific range)
    """

    min: int
    max: int | None

    @override
    def __repr__(self) -> str:
        return f"Arity(min={self.min!r}, max={self.max!r})"


# Common arity patterns as constants for convenience
EXACTLY_ONE_ARITY: Final = Arity(1, 1)
"""Exactly one value required. The most common arity for options and positionals."""

ONE_OR_MORE_ARITY: Final = Arity(1, None)
"""One or more values required. Used for required variadic parameters."""

ZERO_ARITY: Final = Arity(0, 0)
"""No values accepted. Used for boolean flag options."""

ZERO_OR_MORE_ARITY: Final = Arity(0, None)
"""Zero or more values accepted. Used for optional variadic parameters."""

ZERO_OR_ONE_ARITY: Final = Arity(0, 1)
"""Zero or one value accepted. Used for optional single-value parameters."""
