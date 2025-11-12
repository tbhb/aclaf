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
    ZERO_ARITY,
    Arity,
)


class TestCombinedShortOptionsWithEquals:
    """Test combined short options like -abc with the last option using equals."""

    def test_parses_flags_and_final_value(self):
        """Test combined short flags with final option using equals for value.

        Verifies that multiple short options can be combined (e.g., -abc) and
        the last option can take a value using equals syntax.

        Example: -abco=file.txt (sets flags a, b, c and option o to "file.txt")
        """
        args = ["-abco=file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", short=frozenset({"a"}), arity=Arity(0, 0)),
                "b": OptionSpec("b", short=frozenset({"b"}), arity=Arity(0, 0)),
                "c": OptionSpec("c", short=frozenset({"c"}), arity=Arity(0, 0)),
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                ),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["c"].value is True
        assert result.options["output"].value == "file.txt"


class TestShortOptionWithoutEqualsValueInArg:
    """Test short options with value attached directly (e.g., -ovalue)."""

    def test_attached_value_parses(self):
        """Test short option with value directly attached without space or equals.

        Verifies that a short option can have its value directly attached
        (e.g., -ovalue) for options with arity=1.

        Example: -ofile.txt (same as -o file.txt or -o=file.txt)
        """
        args = ["-ofile.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == "file.txt"

    def test_attached_value_for_flag_raises_error(self):
        """Test flag with value directly attached raises error.

        Verifies that flags (arity=0) cannot have values directly attached.
        Using -vvalue raises OptionDoesNotAcceptValueError.

        Example: -vfoo (error: flag 'v' cannot have value 'foo' attached)
        """
        args = ["-vfoo"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(OptionDoesNotAcceptValueError):
            _ = parser.parse(args)


class TestShortOptionWithoutEqualsFlagValue:
    """Test flag behavior with values provided as next argument (not using equals)."""

    def test_flag_values_disabled_ignores_next_arg(self):
        """Test flag followed by value argument when flag values are disabled.

        Verifies that when allow_equals_for_flags=False, the value after a flag
        is not consumed by the flag and the flag is set to True.

        Example: -v false (flag is True, "false" becomes separate argument)
        """
        args = ["-v", "false"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_flag_values_disabled_attached_value_raises_error(self):
        """Test flag with value directly attached when flag values are disabled.

        Verifies that when allow_equals_for_flags=False, attaching a value
        directly to a flag (e.g., -vfalse) raises FlagWithValueError.

        Example: -vfalse (error: flags cannot have values when disabled)
        """
        args = ["-vfalse"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    def test_flag_values_enabled_consumes_next_arg(self):
        """Test flag with value as next argument when flag values are enabled.

        Verifies that when allow_equals_for_flags=True, a flag can accept values
        from the next argument (not just with equals syntax), parsing truthy and
        falsey values correctly.

        Examples: -v true, -v false, -v 1, -v 0
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        for value in DEFAULT_FALSEY_VALUES:
            result = parser.parse(["-v", value])
            assert result.options["verbose"].value is False

        for value in DEFAULT_TRUTHY_VALUES:
            result = parser.parse(["-v", value])
            assert result.options["verbose"].value is True

    def test_flag_values_enabled_parses_attached_value(self):
        """Test flag with value directly attached when flag values are enabled.

        Verifies that when allow_equals_for_flags=True, flags can have values
        directly attached (e.g., -vtrue, -vfalse), correctly parsing them as
        True or False.

        Examples: -vtrue, -vfalse, -v1, -v0
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        for value in DEFAULT_FALSEY_VALUES:
            result = parser.parse([f"-v{value}"])
            assert result.options["verbose"].value is False

        for value in DEFAULT_TRUTHY_VALUES:
            result = parser.parse([f"-v{value}"])
            assert result.options["verbose"].value is True

    def test_custom_option_flag_values_from_next_arg(self):
        """Test flag with custom truthy/falsey values from next argument.

        Verifies that flags can use option-level custom truthy and falsey values
        when the value is provided as the next argument.

        Examples: -v foo (False), -v bar (True)
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                    falsey_flag_values=frozenset({"foo"}),
                    truthy_flag_values=frozenset({"bar"}),
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["-v", "foo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-v", "bar"])
        assert result.options["verbose"].value is True

    def test_custom_option_flag_values_attached(self):
        """Test flag with custom truthy/falsey values directly attached.

        Verifies that flags can use option-level custom truthy and falsey values
        when the value is directly attached to the flag.

        Examples: -vfoo (False), -vbar (True)
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                    falsey_flag_values=frozenset({"foo"}),
                    truthy_flag_values=frozenset({"bar"}),
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["-vfoo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-vbar"])
        assert result.options["verbose"].value is True

    def test_custom_parser_flag_values_from_next_arg(self):
        """Test flag with parser-level custom truthy/falsey values from next argument.

        Verifies that flags can use parser-level custom truthy and falsey values
        when the value is provided as the next argument.

        Examples: -v foo (False), -v bar (True)
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            falsey_flag_values=("foo",),
            truthy_flag_values=("bar",),
        )

        result = parser.parse(["-v", "foo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-v", "bar"])
        assert result.options["verbose"].value is True

    def test_custom_parser_flag_values_attached(self):
        """Test flag with parser-level custom truthy/falsey values directly attached.

        Verifies that flags can use parser-level custom truthy and falsey values
        when the value is directly attached to the flag.

        Examples: -vfoo (False), -vbar (True)
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            falsey_flag_values=("foo",),
            truthy_flag_values=("bar",),
        )

        result = parser.parse(["-vfoo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-vbar"])
        assert result.options["verbose"].value is True

    def test_invalid_value_next_arg_not_consumed(self):
        """Test flag with invalid value as next argument when flag values enabled.

        Verifies that when an invalid flag value is provided as the next argument,
        it is not consumed and the flag defaults to True (the value remains as
        a separate argument).

        Example: -v invalid (flag is True, "invalid" is separate argument)
        """
        args = ["-v", "invalid"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_invalid_value_attached_raises_error(self):
        """Test flag with invalid value directly attached when flag values enabled.

        Verifies that when an invalid flag value is directly attached to the flag,
        InvalidFlagValueError is raised (it cannot be treated as a separate argument).

        Example: -vinvalid (error: "invalid" is not a valid flag value)
        """
        args = ["-vinvalid"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)


class TestCombinedShortOptionsWithoutEquals:
    """Test combined short options like -abc without using equals syntax."""

    def test_parses_multiple_flags(self):
        """Test multiple short flags combined in a single argument.

        Verifies that multiple short flags can be combined into a single
        argument (e.g., -abc sets flags a, b, and c).

        Example: -abc (sets all three flags to True)
        """
        args = ["-abc"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", short=frozenset({"a"}), arity=Arity(0, 0)),
                "b": OptionSpec("b", short=frozenset({"b"}), arity=Arity(0, 0)),
                "c": OptionSpec("c", short=frozenset({"c"}), arity=Arity(0, 0)),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["c"].value is True

    def test_non_flag_in_middle_raises_error(self):
        """Test combined short options with non-flag requiring value.

        Verifies that when a non-flag option (requiring a value) is placed in
        the middle of combined short options, it raises InsufficientOptionValuesError
        because it cannot consume a value.

        Example: -abc where 'b' requires a value (error: insufficient values)
        """
        args = ["-abc"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", short=frozenset({"a"}), arity=ZERO_ARITY),
                "b": OptionSpec("b", short=frozenset({"b"}), arity=EXACTLY_ONE_ARITY),
                "c": OptionSpec("c", short=frozenset({"c"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)

    def test_final_option_consumes_next_arg(self):
        """Test combined short options with last option requiring a value.

        Verifies that when the last option in a combined short options group
        requires a value, it correctly consumes the next argument.

        Example: -abo file.txt (sets flags a, b, and option o to "file.txt")
        """
        args = ["-abo", "file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", short=frozenset({"a"}), arity=Arity(0, 0)),
                "b": OptionSpec("b", short=frozenset({"b"}), arity=Arity(0, 0)),
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                ),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["output"].value == "file.txt"

    def test_final_option_with_attached_value(self):
        """Test combined short options with last option's value directly attached.

        Verifies that when combining short options, the last option can have its
        value directly attached without space or equals.

        Example: -abofile.txt (sets flags a, b, and option o to "file.txt")
        """
        args = ["-abofile.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", short=frozenset({"a"}), arity=Arity(0, 0)),
                "b": OptionSpec("b", short=frozenset({"b"}), arity=Arity(0, 0)),
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                ),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["output"].value == "file.txt"
