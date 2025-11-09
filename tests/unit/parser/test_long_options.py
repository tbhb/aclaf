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


class TestLongOptionWithEquals:
    """Test long options using the --option=value syntax."""

    def test_parses_single_value(self):
        """Test long option with equals syntax requiring exactly one value.

        Verifies that a long option with arity=1 correctly parses the value
        when provided using the --option=value syntax.

        Example: --output=file.txt
        """
        args = ["--output=file.txt"]
        spec = CommandSpec(
            name="cmd", options=OptionSpec("output", arity=EXACTLY_ONE_ARITY)
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == "file.txt"

    def test_consumes_only_equals_value(self):
        """Test long option with equals syntax requiring one or more values.

        Verifies that when an option with arity=1+ uses equals syntax, only the
        value after '=' is consumed, not subsequent arguments.

        Example: --files=file.txt file2.txt (only captures "file.txt")
        """
        args = ["--files=file.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd", options=OptionSpec("files", arity=ONE_OR_MORE_ARITY)
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["files"].value == ("file.txt",)

    def test_insufficient_single_value_raises_error(self):
        """Test long option with equals syntax requiring at least two values.

        Verifies that when an option requires 2+ values, using equals syntax
        provides only one value and raises InsufficientOptionValuesError.

        Example: --files=file1.txt file2.txt file3.txt (equals provides only 1)
        """
        args = ["--files=file1.txt", "file2.txt", "file3.txt"]
        spec = CommandSpec(
            name="cmd", options=OptionSpec("files", arity=Arity(2, None))
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)

    def test_empty_string_satisfies_arity(self):
        """Test long option with empty string value using equals syntax.

        Verifies that --output= (with nothing after equals) is treated as an
        empty string value, which satisfies arity=1 requirement.

        Example: --output= (value is empty string "")
        """
        args = ["--output="]
        spec = CommandSpec(
            name="cmd", options=OptionSpec("output", arity=EXACTLY_ONE_ARITY)
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == ""

    def test_empty_string_satisfies_one_or_more_arity(self):
        """Test long option with empty string for arity requiring one or more values.

        Verifies that --files= (empty string) satisfies arity=1+ by providing
        a single empty string value.

        Example: --files= (value is tuple containing empty string: ("",))
        """
        args = ["--files="]
        spec = CommandSpec(
            name="cmd", options=OptionSpec("files", arity=ONE_OR_MORE_ARITY)
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["files"].value == ("",)

    def test_empty_value_for_flag_raises_error(self):
        """Test long option flag with empty value using equals syntax.

        Verifies that flags (arity=0) cannot accept values, even empty strings.
        Using --verbose= raises OptionDoesNotAcceptValueError.

        Example: --verbose= (error: flags don't accept values)
        """
        args = ["--verbose="]
        spec = CommandSpec(name="cmd", options=OptionSpec("verbose", arity=ZERO_ARITY))
        parser = Parser(spec)
        with pytest.raises(OptionDoesNotAcceptValueError):
            _ = parser.parse(args)

    def test_value_for_flag_raises_error(self):
        """Test long option flag with a value using equals syntax.

        Verifies that flags (arity=0) cannot accept values. Using --verbose=true
        raises FlagWithValueError.

        Example: --verbose=true (error: flags don't accept values)
        """
        args = ["--verbose=true"]
        spec = CommandSpec(name="cmd", options=OptionSpec("verbose", arity=ZERO_ARITY))
        parser = Parser(spec)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    def test_flag_equals_disabled_empty_value_raises_error(
        self,
    ):
        """Test flag with equals and empty value when flag values are disabled.

        Verifies that when allow_equals_for_flags=False, flags cannot accept
        values even with equals syntax. Raises FlagWithValueError.

        Example: --verbose= (error: flags cannot have values when disabled)
        """
        args = ["--verbose="]
        spec = CommandSpec(name="cmd", options=OptionSpec("verbose", is_flag=True))
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    def test_flag_equals_enabled_empty_value_raises_error(self):
        """Test flag with equals and empty value when flag values are enabled.

        Verifies that when allow_equals_for_flags=True, an empty value after
        equals is invalid. Raises InvalidFlagValueError because empty string
        is not in truthy or falsey values.

        Example: --verbose= (error: empty string is not a valid flag value)
        """
        args = ["--verbose="]
        spec = CommandSpec(name="cmd", options=OptionSpec("verbose", is_flag=True))
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)

    def test_flag_equals_disabled_value_raises_error(self):
        """Test flag with value using equals when flag values are disabled.

        Verifies that when allow_equals_for_flags=False, providing any value
        to a flag raises FlagWithValueError.

        Example: --verbose=true (error: flags cannot have values)
        """
        args = ["--verbose=true"]
        spec = CommandSpec(name="cmd", options=OptionSpec("verbose", is_flag=True))
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    def test_flag_equals_enabled_parses_truthy_falsey(self):
        """Test flag with valid truthy/falsey values when flag values are enabled.

        Verifies that when allow_equals_for_flags=True, flags can accept values
        from the default truthy and falsey value sets, correctly parsing them
        as True or False.

        Examples: --verbose=true, --verbose=false, --verbose=1, --verbose=0
        """
        spec = CommandSpec(name="cmd", options=OptionSpec("verbose", is_flag=True))
        parser = Parser(spec, allow_equals_for_flags=True)

        for value in DEFAULT_FALSEY_VALUES:
            result = parser.parse([f"--verbose={value}"])
            assert result.options["verbose"].value is False

        for value in DEFAULT_TRUTHY_VALUES:
            result = parser.parse([f"--verbose={value}"])
            assert result.options["verbose"].value is True

    def test_custom_flag_values_at_option_level(self):
        """Test flag with custom truthy/falsey values defined at option level.

        Verifies that options can define custom truthy and falsey values that
        override the parser defaults. Tests with custom values "foo" (falsey)
        and "bar" (truthy).

        Examples: --verbose=foo (False), --verbose=bar (True)
        """
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                "verbose",
                short="v",
                is_flag=True,
                falsey_flag_values=("foo"),
                truthy_flag_values=("bar"),
            ),
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["--verbose=foo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["--verbose=bar"])
        assert result.options["verbose"].value is True

    def test_custom_flag_values_at_parser_level(self):
        """Test flag with custom truthy/falsey values defined at parser level.

        Verifies that parsers can define default custom truthy and falsey values
        that apply to all flags. Tests with custom values "foo" (falsey) and
        "bar" (truthy).

        Examples: --verbose=foo (False), --verbose=bar (True)
        """
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec("verbose", is_flag=True),
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            falsey_flag_values=("foo",),
            truthy_flag_values=("bar",),
        )

        result = parser.parse(["--verbose=foo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["--verbose=bar"])
        assert result.options["verbose"].value is True

    def test_invalid_flag_value_raises_error(self):
        """Test flag with value not in truthy or falsey value sets.

        Verifies that when allow_equals_for_flags=True and a value is provided
        that isn't in the truthy or falsey sets, InvalidFlagValueError is raised.

        Example: --verbose=invalid (error: "invalid" is not a valid flag value)
        """
        args = ["--verbose=invalid"]
        spec = CommandSpec(name="cmd", options=OptionSpec("verbose", is_flag=True))
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)


class TestLongOptionWithoutEquals:
    """Test long options using the --option value syntax (without equals)."""

    def test_consumes_next_argument(self):
        """Test long option requiring exactly one value from next argument.

        Verifies that a long option with arity=1 correctly consumes the next
        argument as its value when not using equals syntax.

        Example: --output file.txt
        """
        args = ["--output", "file.txt"]
        spec = CommandSpec(
            name="cmd", options=OptionSpec("output", arity=EXACTLY_ONE_ARITY)
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == "file.txt"

    def test_flag_defaults_to_true(self):
        """Test long option flag that takes no arguments.

        Verifies that a flag (arity=0) can be used without providing any value
        and defaults to True.

        Example: --verbose (sets verbose to True)
        """
        args = ["--verbose"]
        spec = CommandSpec(name="cmd", options=OptionSpec("verbose", arity=ZERO_ARITY))
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_consumes_all_following_non_option_args(self):
        """Test long option that accepts zero or more values.

        Verifies that an option with arity=0+ consumes all following arguments
        that don't start with a dash, collecting them into a tuple.

        Example: --files file1.txt file2.txt (captures both files)
        """
        args = ["--files", "file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd", options=OptionSpec("files", arity=Arity(0, None))
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["files"].value == ("file1.txt", "file2.txt")

    def test_missing_required_value_raises_error(self):
        """Test long option with insufficient values provided.

        Verifies that when an option requires 1+ values but none are provided,
        InsufficientOptionValuesError is raised.

        Example: --files (error: requires at least 1 value)
        """
        args = ["--files"]
        spec = CommandSpec(
            name="cmd", options=OptionSpec("files", arity=ONE_OR_MORE_ARITY)
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)
