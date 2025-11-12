"""Consolidated tests for common option parsing behavior across long and short options.

This module contains parametrized tests that verify identical behavior for both
long (--option) and short (-o) option styles. Style-specific tests remain in
test_long_options.py and test_short_options.py.
"""

import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
)
from aclaf.parser.constants import DEFAULT_FALSEY_VALUES, DEFAULT_TRUTHY_VALUES
from aclaf.parser.exceptions import (
    FlagWithValueError,
    InsufficientOptionValuesError,
    InvalidFlagValueError,
    OptionDoesNotAcceptValueError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    Arity,
)


class TestOptionEqualsSyntax:
    """Test options using the --option=value or -o=value syntax."""

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--output", "output", frozenset[str]()),
            ("-o", "output", frozenset({"o"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_parses_single_value(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option with equals syntax requiring exactly one value.

        Verifies that an option with arity=1 correctly parses the value
        when provided using the --option=value or -o=value syntax.

        Examples: --output=file.txt, -o=file.txt
        """
        args = [f"{option_flag}=file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == "file.txt"

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_consumes_only_equals_value(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option with equals syntax requiring one or more values.

        Verifies that when an option with arity=1+ uses equals syntax, only the
        value after '=' is consumed, not subsequent arguments.

        Examples: --files=file.txt file2.txt, -f=file.txt file2.txt
        (only captures "file.txt")
        """
        args = [f"{option_flag}=file.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == ("file.txt",)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_insufficient_single_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option with equals syntax requiring at least two values.

        Verifies that when an option requires 2+ values, using equals syntax
        provides only one value and raises InsufficientOptionValuesError.

        Examples: --files=file1.txt file2.txt file3.txt, -f=file1.txt file2.txt
        (equals provides only 1 value)
        """
        args = [f"{option_flag}=file1.txt", "file2.txt", "file3.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=Arity(2, None)
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--output", "output", frozenset[str]()),
            ("-o", "output", frozenset({"o"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_empty_string_satisfies_arity(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option with empty string value using equals syntax.

        Verifies that --output= or -o= (with nothing after equals) is treated as
        an empty string value, which satisfies arity=1 requirement.

        Examples: --output=, -o= (value is empty string "")
        """
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == ""

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_empty_string_satisfies_one_or_more_arity(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option with empty string for arity requiring one or more values.

        Verifies that --files= or -f= (empty string) satisfies arity=1+ by
        providing a single empty string value.

        Examples: --files=, -f= (value is tuple containing empty string: ("",))
        """
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == ("",)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_empty_value_for_flag_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option flag with empty value using equals syntax.

        Verifies that flags (arity=0) cannot accept values, even empty strings.
        Using --verbose= or -v= raises OptionDoesNotAcceptValueError.

        Examples: --verbose=, -v= (error: flags don't accept values)
        """
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(OptionDoesNotAcceptValueError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_equals_disabled_empty_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test flag with equals and empty value when flag values are disabled.

        Verifies that when allow_equals_for_flags=False, flags cannot accept
        values even with equals syntax. Raises FlagWithValueError.

        Examples: --verbose=, -v= (error: flags cannot have values when disabled)
        """
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_equals_enabled_empty_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test flag with equals and empty value when flag values are enabled.

        Verifies that when allow_equals_for_flags=True, an empty value after
        equals is invalid. Raises InvalidFlagValueError because empty string
        is not in truthy or falsey values.

        Examples: --verbose=, -v= (error: empty string is not a valid flag value)
        """
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_equals_disabled_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test flag with value using equals when flag values are disabled.

        Verifies that when allow_equals_for_flags=False, providing any value
        to a flag raises FlagWithValueError.

        Examples: --verbose=true, -v=true (error: flags cannot have values)
        """
        args = [f"{option_flag}=true"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_equals_enabled_parses_truthy_falsey(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test flag with valid truthy/falsey values when flag values are enabled.

        Verifies that when allow_equals_for_flags=True, flags can accept values
        from the default truthy and falsey value sets, correctly parsing them
        as True or False.

        Examples: --verbose=true, --verbose=false, -v=1, -v=0
        """
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        for value in DEFAULT_FALSEY_VALUES:
            result = parser.parse([f"{option_flag}={value}"])
            assert result.options[option_name].value is False

        for value in DEFAULT_TRUTHY_VALUES:
            result = parser.parse([f"{option_flag}={value}"])
            assert result.options[option_name].value is True

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_custom_flag_values_at_option_level(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test flag with custom truthy/falsey values defined at option level.

        Verifies that options can define custom truthy and falsey values that
        override the parser defaults. Tests with custom values "foo" (falsey)
        and "bar" (truthy).

        Examples: --verbose=foo (False), --verbose=bar (True)
        Examples: -v=foo (False), -v=bar (True)
        """
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name,
                    short=option_short,
                    is_flag=True,
                    falsey_flag_values=frozenset({"foo"}),
                    truthy_flag_values=frozenset({"bar"}),
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse([f"{option_flag}=foo"])
        assert result.options[option_name].value is False

        result = parser.parse([f"{option_flag}=bar"])
        assert result.options[option_name].value is True

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_custom_flag_values_at_parser_level(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test flag with custom truthy/falsey values defined at parser level.

        Verifies that parsers can define default custom truthy and falsey values
        that apply to all flags. Tests with custom values "foo" (falsey) and
        "bar" (truthy).

        Examples: --verbose=foo (False), --verbose=bar (True)
        Examples: -v=foo (False), -v=bar (True)
        """
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            falsey_flag_values=("foo",),
            truthy_flag_values=("bar",),
        )

        result = parser.parse([f"{option_flag}=foo"])
        assert result.options[option_name].value is False

        result = parser.parse([f"{option_flag}=bar"])
        assert result.options[option_name].value is True

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_invalid_flag_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test flag with value not in truthy or falsey value sets.

        Verifies that when allow_equals_for_flags=True and a value is provided
        that isn't in the truthy or falsey sets, InvalidFlagValueError is raised.

        Examples: --verbose=invalid, -v=invalid
        (error: "invalid" is not a valid flag value)
        """
        args = [f"{option_flag}=invalid"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)


class TestOptionSpaceSyntax:
    """Test options using the --option value or -o value syntax (without equals)."""

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--output", "output", frozenset[str]()),
            ("-o", "output", frozenset({"o"})),
        ],
        ids=["long", "short"],
    )
    def test_space_consumes_next_argument(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option requiring exactly one value from next argument.

        Verifies that an option with arity=1 correctly consumes the next
        argument as its value when not using equals syntax.

        Examples: --output file.txt, -o file.txt
        """
        args = [option_flag, "file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == "file.txt"

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_defaults_to_true(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option flag that takes no arguments.

        Verifies that a flag (arity=0) can be used without providing any value
        and defaults to True.

        Examples: --verbose, -v (sets verbose to True)
        """
        args = [option_flag]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value is True

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_space_consumes_all_following_non_option_args(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option that accepts zero or more values.

        Verifies that an option with arity=0+ consumes all following arguments
        that don't start with a dash, collecting them into a tuple.

        Examples: --files file1.txt file2.txt, -f file1.txt file2.txt
        (captures both files)
        """
        args = [option_flag, "file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=Arity(0, None)
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == ("file1.txt", "file2.txt")

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_space_missing_required_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        """Test option with insufficient values provided.

        Verifies that when an option requires 1+ values but none are provided,
        InsufficientOptionValuesError is raised.

        Examples: --files, -f (error: requires at least 1 value)
        """
        args = [option_flag]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)
