"""Hypothesis strategies for property-based parser tests.

This module provides reusable Hypothesis strategies for generating test data
for parser property tests. Strategies are designed to generate valid inputs
that explore the full space of parser configurations, options, and arguments.
"""

import string

from hypothesis import strategies as st

# Valid characters for option names (ASCII alphanumeric, dash, underscore)
OPTION_NAME_ALPHABET = st.sampled_from(string.ascii_letters + string.digits + "-_")

# Valid values (any text that doesn't start with -)
VALUE_TEXT = st.text(min_size=1, max_size=20).filter(lambda x: not x.startswith("-"))


@st.composite
def option_names(draw: st.DrawFn, min_size: int = 2, max_size: int = 15) -> str:
    """Generate valid option names.

    Args:
        draw: Hypothesis draw function.
        min_size: Minimum name length (default 2 for long options).
        max_size: Maximum name length.

    Returns:
        A valid option name (alphanumeric with dashes/underscores).
    """
    return draw(
        st.text(
            alphabet=OPTION_NAME_ALPHABET,
            min_size=min_size,
            max_size=max_size,
        ).filter(
            lambda x: (
                x
                and x[0].isalpha()  # Must start with letter
                and x[-1].isalnum()  # Must end with alphanumeric
            )
        )
    )


@st.composite
def option_lists(
    draw: st.DrawFn,
    min_size: int = 1,
    max_size: int = 10,
) -> list[str]:
    """Generate lists of unique option names.

    Args:
        draw: Hypothesis draw function.
        min_size: Minimum number of options.
        max_size: Maximum number of options.

    Returns:
        A list of unique option names.
    """
    return draw(
        st.lists(
            option_names(),
            min_size=min_size,
            max_size=max_size,
            unique=True,
        )
    )


@st.composite
def option_value_pairs(
    draw: st.DrawFn,
    min_size: int = 1,
    max_size: int = 10,
) -> list[tuple[str, str]]:
    """Generate lists of (option, value) pairs.

    Args:
        draw: Hypothesis draw function.
        min_size: Minimum number of pairs.
        max_size: Maximum number of pairs.

    Returns:
        A list of (option_name, value) tuples.
    """
    names = draw(option_lists(min_size=min_size, max_size=max_size))
    values = draw(st.lists(VALUE_TEXT, min_size=len(names), max_size=len(names)))
    return list(zip(names, values, strict=True))
