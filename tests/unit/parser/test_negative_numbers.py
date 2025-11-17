import re

import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
    PositionalSpec,
)
from aclaf.parser.constants import DEFAULT_NEGATIVE_NUMBER_PATTERN
from aclaf.parser.exceptions import ParserConfigurationError, UnknownOptionError
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    Arity,
)


class TestNegativeNumbersDisabled:
    def test_negative_integer_treated_as_option(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-1"])

    def test_negative_decimal_treated_as_option_with_value(self):
        spec = CommandSpec(
            name="cmd",
            options={"3": OptionSpec("3", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=False)

        result = parser.parse(["-3.14"])
        assert result.options["3"].value == ".14"

    def test_default_behavior_is_disabled(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec)

        # Should fail because -1 is treated as unknown option
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-1"])


class TestNegativeNumbersEnabled:
    def test_negative_integer_as_positional(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1"])
        assert result.positionals["value"].value == "-1"

    def test_negative_decimal_as_positional(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-3.14"])
        assert result.positionals["value"].value == "-3.14"

    def test_negative_number_as_option_value(self):
        spec = CommandSpec(
            name="cmd",
            options={"threshold": OptionSpec("threshold", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--threshold", "-5"])
        assert result.options["threshold"].value == "-5"

    def test_option_takes_precedence_over_negative_number(self):
        spec = CommandSpec(
            name="cmd",
            options={"1": OptionSpec("1", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1"])
        assert result.options["1"].value is True

    def test_negative_zero(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-0"])
        assert result.positionals["value"].value == "-0"

    def test_multiple_negative_numbers(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1", "-2", "-3"])
        assert result.positionals["values"].value == ("-1", "-2", "-3")

    def test_negative_after_delimiter(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--", "-1", "-2"])
        assert result.extra_args == ("-1", "-2")

    def test_scientific_notation(self):
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
        spec = CommandSpec(
            name="cmd",
            options={"value": OptionSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--value", "-6.022e23"])
        assert result.options["value"].value == "-6.022e23"

    def test_negative_number_with_multiple_option_values(self):
        spec = CommandSpec(
            name="cmd",
            options={"range": OptionSpec("range", arity=Arity(2, 2))},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--range", "-10", "10"])
        assert result.options["range"].value == ("-10", "10")

    def test_mixed_positive_and_negative_numbers(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["5", "-3", "10", "-7"])
        assert result.positionals["values"].value == ("5", "-3", "10", "-7")


class TestNegativeNumberCustomPattern:
    def test_leading_decimal_with_custom_pattern(self):
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
        spec = CommandSpec(name="cmd")

        with pytest.raises(ParserConfigurationError, match="Invalid regex pattern"):
            _ = Parser(
                spec,
                allow_negative_numbers=True,
                negative_number_pattern=r"[",  # Invalid regex
            )

    def test_custom_pattern_validation_matches_empty(self):
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
        spec = CommandSpec(name="cmd")

        with pytest.raises(ParserConfigurationError, match="nested quantifiers"):
            _ = Parser(
                spec,
                allow_negative_numbers=True,
                negative_number_pattern=r"^(-\d+)+$",  # Nested quantifiers
            )


class TestNegativeNumberEdgeCases:
    def test_just_minus_sign_not_negative_number(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-"])
        assert result.positionals["file"].value == "-"

    def test_long_option_with_number_not_negative(self):
        spec = CommandSpec(
            name="cmd",
            options={"1": OptionSpec("1", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--1"])
        assert result.options["1"].value is True

    def test_negative_with_non_digit_not_number(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=True)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-abc"])

    def test_option_with_inline_negative_value(self):
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
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-999999999999"])
        assert result.positionals["value"].value == "-999999999999"

    def test_trailing_decimal_point(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-100.0"])
        assert result.positionals["value"].value == "-100.0"

    def test_scientific_notation_uppercase_e(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1.5E10"])
        assert result.positionals["value"].value == "-1.5E10"

    def test_scientific_notation_positive_exponent(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1e+5"])
        assert result.positionals["value"].value == "-1e+5"


class TestNegativeComplexNumbers:
    def test_negative_real_positive_imaginary(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-3+4j"])
        assert result.positionals["value"].value == "-3+4j"

    def test_negative_real_negative_imaginary(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-3-4j"])
        assert result.positionals["value"].value == "-3-4j"

    def test_negative_pure_imaginary(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-4j"])
        assert result.positionals["value"].value == "-4j"

    def test_complex_with_decimals(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1.5+2.5j"])
        assert result.positionals["value"].value == "-1.5+2.5j"

    def test_complex_with_scientific_notation(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1e5+2e3j"])
        assert result.positionals["value"].value == "-1e5+2e3j"

    def test_complex_as_option_value(self):
        spec = CommandSpec(
            name="cmd",
            options={"value": OptionSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--value", "-3+4j"])
        assert result.options["value"].value == "-3+4j"

    def test_multiple_complex_numbers(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-3+4j", "-1-2j", "-5j"])
        assert result.positionals["values"].value == ("-3+4j", "-1-2j", "-5j")

    def test_positive_complex_works_without_flag(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=False)

        # Positive complex doesn't start with -, so it's just a normal value
        result = parser.parse(["3+4j"])
        assert result.positionals["value"].value == "3+4j"

    def test_complex_disabled_treats_as_option(self):
        spec = CommandSpec(
            name="cmd",
            options={"3": OptionSpec("3", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=False)

        # -3+4j → option "-3" with inline value "+4j"
        result = parser.parse(["-3+4j"])
        assert result.options["3"].value == "+4j"

    def test_negative_zero_imaginary(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-0j"])
        assert result.positionals["value"].value == "-0j"

    def test_complex_with_both_scientific_notation(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-2.5E-10-3.14E-5j"])
        assert result.positionals["value"].value == "-2.5E-10-3.14E-5j"


class TestComplexNumberPattern:
    def test_pattern_matches_negative_complex(self):
        pattern = re.compile(DEFAULT_NEGATIVE_NUMBER_PATTERN)

        # Should match
        assert pattern.match("-3+4j")
        assert pattern.match("-3-4j")
        assert pattern.match("-4j")
        assert pattern.match("-0j")
        assert pattern.match("-1.5+2.5j")
        assert pattern.match("-1e5+2e3j")
        assert pattern.match("-2.5E-10-3.14E-5j")

    def test_pattern_rejects_invalid_complex(self):
        pattern = re.compile(DEFAULT_NEGATIVE_NUMBER_PATTERN)

        # Should NOT match
        assert not pattern.match("3+4j")  # Positive real
        assert not pattern.match("1-3j")  # Positive real
        assert not pattern.match("-3i")  # Wrong imaginary unit
        assert not pattern.match("-3+j")  # Missing coefficient
        assert not pattern.match("-")  # Just minus

    def test_pattern_backwards_compatible(self):
        pattern = re.compile(DEFAULT_NEGATIVE_NUMBER_PATTERN)

        # Existing formats still work
        assert pattern.match("-1")
        assert pattern.match("-42")
        assert pattern.match("-3.14")
        assert pattern.match("-1e5")
        assert pattern.match("-2.5E-10")
