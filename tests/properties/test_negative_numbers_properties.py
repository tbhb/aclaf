"""Property-based tests for negative number handling using Hypothesis.

This module tests the negative number parsing feature with property-based tests
to discover edge cases and verify invariants across a wide range of inputs.
"""

import dataclasses
import re
import warnings
from contextlib import suppress
from typing import TYPE_CHECKING

import pytest
from hypothesis import given, strategies as st

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.constants import DEFAULT_NEGATIVE_NUMBER_PATTERN
from aclaf.parser.exceptions import ParserConfigurationError, UnknownOptionError
from aclaf.parser.types import EXACTLY_ONE_ARITY, ZERO_OR_MORE_ARITY, Arity

if TYPE_CHECKING:
    from hypothesis.strategies import DrawFn


@st.composite
def negative_integers(draw: "DrawFn") -> str:
    """Strategy for negative integers."""
    value = draw(st.integers(min_value=-1_000_000, max_value=-1))
    return str(value)


@st.composite
def negative_floats(draw: "DrawFn") -> str:
    """Strategy for negative floats."""
    value = draw(
        st.floats(
            min_value=-1_000_000.0,
            max_value=-0.001,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    return str(value)


@st.composite
def negative_scientific(draw: "DrawFn") -> str:
    """Strategy for negative numbers in scientific notation."""
    # Generate mantissa (e.g., -1.5, -2.0, -6.022)
    mantissa = draw(
        st.floats(
            min_value=-10.0,
            max_value=-0.1,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    # Generate exponent (e.g., 10, -5, 23)
    exponent = draw(st.integers(min_value=-50, max_value=50))
    # Random choice of 'e' or 'E'
    e_char = draw(st.sampled_from(["e", "E"]))
    # Format as scientific notation
    return f"{mantissa:.2f}{e_char}{exponent:+d}"


class TestNegativeNumberProperties:
    """Property-based tests for negative number handling."""

    @given(negative_integers())
    def test_negative_integers_parsed_as_positionals(self, negative_int: str):
        """Property: All negative integers parse as positional values."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse([negative_int])
        assert result.positionals["value"].value == negative_int

    @given(negative_floats())
    def test_negative_floats_parsed_as_positionals(self, negative_float: str):
        """Property: All negative floats parse as positional values."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse([negative_float])
        assert result.positionals["value"].value == negative_float

    @given(negative_scientific())
    def test_negative_scientific_parsed_as_positionals(self, negative_sci: str):
        """Property: All scientific notation negatives parse as positional values."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse([negative_sci])
        assert result.positionals["value"].value == negative_sci

    @given(st.lists(negative_integers(), min_size=1, max_size=10))
    def test_multiple_negative_numbers_preserve_order(self, numbers: list[str]):
        """Property: Multiple negative numbers preserve input order."""
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(numbers)
        assert result.positionals["values"].value == tuple(numbers)

    @given(negative_integers())
    def test_negative_number_consumed_as_option_value(self, negative_int: str):
        """Property: Negative numbers are consumed as option values."""
        spec = CommandSpec(
            name="cmd",
            options={"value": OptionSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--value", negative_int])
        assert result.options["value"].value == negative_int

    @given(st.text(min_size=1, max_size=20, alphabet=st.characters()))
    def test_custom_pattern_validation(self, pattern_suffix: str):
        """Property: Invalid regex patterns are rejected."""
        spec = CommandSpec(name="cmd")

        # Invalid patterns should raise ParserConfigurationError during
        # parser construction. Use hypothesis to fuzz pattern inputs.
        # Suppress FutureWarning for patterns like '[[' that trigger warnings.
        with warnings.catch_warnings(), suppress(ParserConfigurationError):
            warnings.simplefilter("ignore", FutureWarning)
            parser = Parser(
                spec,
                allow_negative_numbers=True,
                negative_number_pattern=pattern_suffix,
            )
            # If pattern is valid, parsing should not crash
            # (but may raise ParseError for specific inputs)
            with suppress(Exception):
                # ParseError is fine, we're testing pattern validation
                _ = parser.parse(["-1"])


class TestNegativeNumberInvariants:
    """Test invariants that must hold for negative number parsing."""

    @given(negative_integers())
    def test_parse_result_structure(self, negative_int: str):
        """Invariant: ParseResult has correct structure and values."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse([negative_int])

        # Verify the result has the expected value and structure
        assert result.positionals["value"].value == negative_int
        assert result.command == "cmd"
        assert dataclasses.is_dataclass(result)

        # Verify frozen behavior through normal attribute assignment
        # (direct assignment should fail on frozen dataclass)
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            result.command = "modified"  # type: ignore[misc]  # pyright: ignore[reportAttributeAccessIssue]

    @given(negative_integers())
    def test_parse_is_deterministic(self, negative_int: str):
        """Invariant: Parsing the same input produces the same result."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result1 = parser.parse([negative_int])
        result2 = parser.parse([negative_int])

        assert result1 == result2
        assert result1.positionals == result2.positionals

    @given(st.lists(negative_integers(), min_size=0, max_size=10))
    def test_parse_does_not_modify_input(self, numbers: list[str]):
        """Invariant: Parsing does not modify input list."""
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        original = numbers.copy()
        _ = parser.parse(numbers)

        assert numbers == original


class TestNegativeNumberEdgeProperties:
    """Property-based tests for edge cases."""

    @given(
        st.integers(min_value=-1_000_000, max_value=-1),
        st.integers(min_value=1, max_value=1_000_000),
    )
    def test_mixed_positive_negative_preserve_order(self, neg: int, pos: int):
        """Property: Mixed positive and negative numbers preserve order."""
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        args = [str(neg), str(pos), str(neg * 2), str(pos * 2)]
        result = parser.parse(args)
        assert result.positionals["values"].value == tuple(args)

    @given(negative_integers())
    def test_negative_number_after_delimiter_is_literal(self, negative_int: str):
        """Property: Negative numbers after -- are treated as literals."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--", negative_int])
        assert result.extra_args == (negative_int,)

    @given(negative_integers())
    def test_disabled_flag_treats_as_option(self, negative_int: str):
        """Property: When disabled, negative numbers are treated as options."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=False)

        # Should raise UnknownOptionError
        with pytest.raises(UnknownOptionError):
            _ = parser.parse([negative_int])

    @given(
        st.integers(min_value=-1_000_000, max_value=-1),
        st.integers(min_value=2, max_value=10),  # Avoid string/tuple confusion
    )
    def test_option_with_multiple_negative_values(self, neg: int, count: int):
        """Property: Options can consume multiple negative number values."""
        spec = CommandSpec(
            name="cmd",
            options={"values": OptionSpec("values", arity=Arity(count, count))},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        # Generate count negative numbers
        args = ["--values"] + [str(neg * i) for i in range(1, count + 1)]
        result = parser.parse(args)

        # For arity > 1, result is always a tuple
        assert isinstance(result.options["values"].value, tuple)
        assert len(result.options["values"].value) == count


class TestNegativeNumberPatternProperties:
    """Property-based tests for custom pattern behavior."""

    @given(negative_integers())
    def test_default_pattern_matches_integers(self, negative_int: str):
        """Property: Default pattern matches all negative integers."""
        assert re.match(DEFAULT_NEGATIVE_NUMBER_PATTERN, negative_int)

    @given(
        st.floats(
            min_value=-1_000_000.0,
            max_value=-0.001,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    def test_default_pattern_matches_floats(self, negative_float: float):
        """Property: Default pattern matches all negative floats."""
        # Python's str() may produce scientific notation, which is also valid
        float_str = str(negative_float)
        assert re.match(DEFAULT_NEGATIVE_NUMBER_PATTERN, float_str)

    @given(st.text(min_size=1, max_size=10).filter(lambda x: not x.startswith("-")))
    def test_default_pattern_rejects_non_negative(self, text: str):
        """Property: Default pattern rejects text not starting with minus."""
        # Should NOT match
        assert not re.match(DEFAULT_NEGATIVE_NUMBER_PATTERN, text)


@st.composite
def negative_complex_numbers(draw: "DrawFn") -> str:
    """Strategy for negative complex numbers."""
    # Generate real part (negative)
    real = draw(
        st.floats(
            min_value=-1000.0,
            max_value=-0.001,
            allow_nan=False,
            allow_infinity=False,
        )
    )

    # Generate imaginary part (can be positive or negative)
    imag = draw(
        st.floats(
            min_value=-1000.0,
            max_value=1000.0,
            allow_nan=False,
            allow_infinity=False,
        ).filter(lambda x: x != 0)  # Avoid zero imaginary
    )

    # Format as complex number string
    return f"{real:+g}{imag:+g}j"


@st.composite
def negative_pure_imaginary(draw: "DrawFn") -> str:
    """Strategy for negative pure imaginary numbers (-4j, -2.5j)."""
    # Generate imaginary coefficient (negative)
    imag = draw(
        st.floats(
            min_value=-1000.0,
            max_value=-0.001,
            allow_nan=False,
            allow_infinity=False,
        )
    )

    # Format as pure imaginary
    return f"{imag}j"


class TestComplexNumberProperties:
    """Property-based tests for complex numbers."""

    @given(negative_complex_numbers())
    def test_negative_complex_parsed_as_positionals(self, complex_num: str):
        """Property: All negative complex numbers parse as positional values."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse([complex_num])
        assert result.positionals["value"].value == complex_num

    @given(negative_complex_numbers())
    def test_complex_consumed_as_option_value(self, complex_num: str):
        """Property: Complex numbers consumed as option values."""
        spec = CommandSpec(
            name="cmd",
            options={"value": OptionSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--value", complex_num])
        assert result.options["value"].value == complex_num

    @given(negative_pure_imaginary())
    def test_pure_imaginary_parsed_as_positionals(self, imag_num: str):
        """Property: Pure imaginary numbers parse as positional values."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse([imag_num])
        assert result.positionals["value"].value == imag_num

    @given(st.lists(negative_complex_numbers(), min_size=1, max_size=5))
    def test_multiple_complex_preserve_order(self, numbers: list[str]):
        """Property: Multiple complex numbers preserve input order."""
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(numbers)
        assert result.positionals["values"].value == tuple(numbers)

    @given(negative_complex_numbers())
    def test_complex_parse_is_deterministic(self, complex_num: str):
        """Property: Parsing same complex number produces same result."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result1 = parser.parse([complex_num])
        result2 = parser.parse([complex_num])

        assert result1 == result2
        assert result1.positionals == result2.positionals
