"""Tests for negative number handling in the parser.

This module tests the allow_negative_numbers parser flag and related functionality
for disambiguating between short options and negative numeric values.
"""

import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
    PositionalSpec,
)
from aclaf.parser.exceptions import ParserConfigurationError, UnknownOptionError
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    Arity,
)


class TestNegativeNumbersDisabled:
    """Tests with allow_negative_numbers=False (default behavior)."""

    def test_negative_integer_treated_as_option(self):
        """When disabled, -1 is treated as short option."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-1"])

    def test_negative_decimal_treated_as_option_with_value(self):
        """When disabled, -3.14 is short option '3' with inline value '.14'."""
        spec = CommandSpec(
            name="cmd",
            options={"3": OptionSpec("3", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=False)

        result = parser.parse(["-3.14"])
        assert result.options["3"].value == ".14"

    def test_default_behavior_is_disabled(self):
        """By default, negative number parsing is disabled."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec)

        # Should fail because -1 is treated as unknown option
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-1"])


class TestNegativeNumbersEnabled:
    """Tests with allow_negative_numbers=True."""

    def test_negative_integer_as_positional(self):
        """Negative integer accepted as positional value."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1"])
        assert result.positionals["value"].value == "-1"

    def test_negative_decimal_as_positional(self):
        """Negative decimal accepted as positional value."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-3.14"])
        assert result.positionals["value"].value == "-3.14"

    def test_negative_number_as_option_value(self):
        """Negative number consumed as option value."""
        spec = CommandSpec(
            name="cmd",
            options={"threshold": OptionSpec("threshold", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--threshold", "-5"])
        assert result.options["threshold"].value == "-5"

    def test_option_takes_precedence_over_negative_number(self):
        """When option -1 is defined, it takes precedence."""
        spec = CommandSpec(
            name="cmd",
            options={"1": OptionSpec("1", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1"])
        assert result.options["1"].value is True

    def test_negative_zero(self):
        """-0 is valid negative number."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-0"])
        assert result.positionals["value"].value == "-0"

    def test_multiple_negative_numbers(self):
        """Multiple negative numbers as positionals."""
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1", "-2", "-3"])
        assert result.positionals["values"].value == ("-1", "-2", "-3")

    def test_negative_after_delimiter(self):
        """Negative numbers after -- are literals."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--", "-1", "-2"])
        assert result.extra_args == ("-1", "-2")

    def test_scientific_notation(self):
        """Scientific notation is supported by default."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1e5"])
        assert result.positionals["value"].value == "-1e5"

        _ = result
        result = parser.parse(["-2.5E-10"])
        assert result.positionals["value"].value == "-2.5E-10"

    def test_scientific_notation_as_option_value(self):
        """Scientific notation works as option values."""
        spec = CommandSpec(
            name="cmd",
            options={"value": OptionSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--value", "-6.022e23"])
        assert result.options["value"].value == "-6.022e23"

    def test_negative_number_with_multiple_option_values(self):
        """Negative numbers work with options requiring multiple values."""
        spec = CommandSpec(
            name="cmd",
            options={"range": OptionSpec("range", arity=Arity(2, 2))},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--range", "-10", "10"])
        assert result.options["range"].value == ("-10", "10")

    def test_mixed_positive_and_negative_numbers(self):
        """Mix of positive and negative numbers as positionals."""
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["5", "-3", "10", "-7"])
        assert result.positionals["values"].value == ("5", "-3", "10", "-7")


class TestNegativeNumberCustomPattern:
    """Tests with custom negative_number_pattern."""

    def test_leading_decimal_with_custom_pattern(self):
        """Custom pattern can match leading decimal point."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(
            spec,
            allow_negative_numbers=True,
            negative_number_pattern=r"^-\d*\.?\d+$",
        )

        result = parser.parse(["-.5"])
        assert result.positionals["value"].value == "-.5"

    def test_custom_pattern_validation_invalid_regex(self):
        """Invalid regex pattern raises ParserConfigurationError."""
        spec = CommandSpec(name="cmd")

        with pytest.raises(ParserConfigurationError, match="Invalid regex pattern"):
            _ = Parser(
                spec,
                allow_negative_numbers=True,
                negative_number_pattern=r"[",  # Invalid regex
            )

    def test_custom_pattern_validation_matches_empty(self):
        """Pattern matching empty string raises ParserConfigurationError."""
        spec = CommandSpec(name="cmd")

        with pytest.raises(
            ParserConfigurationError, match="must not match empty string"
        ):
            _ = Parser(
                spec,
                allow_negative_numbers=True,
                negative_number_pattern=r"^-?\d*$",  # Matches empty string
            )

    def test_custom_pattern_validation_nested_quantifiers(self):
        """Pattern with nested quantifiers raises ParserConfigurationError."""
        spec = CommandSpec(name="cmd")

        with pytest.raises(ParserConfigurationError, match="nested quantifiers"):
            _ = Parser(
                spec,
                allow_negative_numbers=True,
                negative_number_pattern=r"^(-\d+)+$",  # Nested quantifiers
            )


class TestNegativeNumberEdgeCases:
    """Edge cases and error conditions."""

    def test_just_minus_sign_not_negative_number(self):
        """Single - alone is not a negative number."""
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-"])
        assert result.positionals["file"].value == "-"

    def test_long_option_with_number_not_negative(self):
        """--1 is long option, never negative number."""
        spec = CommandSpec(
            name="cmd",
            options={"1": OptionSpec("1", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--1"])
        assert result.options["1"].value is True

    def test_negative_with_non_digit_not_number(self):
        """-abc is not a negative number."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=True)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-abc"])

    def test_option_with_inline_negative_value(self):
        """Short option with inline negative value."""
        spec = CommandSpec(
            name="cmd",
            options={
                "offset": OptionSpec(
                    "offset", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-o-5"])
        assert result.options["offset"].value == "-5"

    def test_negative_number_not_in_value_context_fails(self):
        """Negative number without value context raises error."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec, allow_negative_numbers=True)

        # No positionals defined, -1 is not in value-consuming context
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-1"])

    def test_large_negative_number(self):
        """Very large negative numbers are accepted."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-999999999999"])
        assert result.positionals["value"].value == "-999999999999"

    def test_trailing_decimal_point(self):
        """Negative number with trailing decimal point."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-100.0"])
        assert result.positionals["value"].value == "-100.0"

    def test_scientific_notation_uppercase_e(self):
        """Scientific notation with uppercase E."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1.5E10"])
        assert result.positionals["value"].value == "-1.5E10"

    def test_scientific_notation_positive_exponent(self):
        """Scientific notation with explicit positive exponent."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1e+5"])
        assert result.positionals["value"].value == "-1e+5"
