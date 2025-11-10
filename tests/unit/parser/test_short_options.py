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


class TestShortOptionWithEquals:
    """Test short options using the -o=value syntax."""

    def test_parses_single_value(self):
        """Test short option with equals syntax requiring exactly one value.

        Verifies that a short option with arity=1 correctly parses the value
        when provided using the -o=value syntax.

        Example: -o=file.txt
        """
        args = ["-o=file.txt"]
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

    def test_consumes_only_equals_value(self):
        """Test short option with equals syntax requiring one or more values.

        Verifies that when an option with arity=1+ uses equals syntax, only the
        value after '=' is consumed, not subsequent arguments.

        Example: -f=file.txt file2.txt (only captures "file.txt")
        """
        args = ["-f=file.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files", short=frozenset({"f"}), arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["files"].value == ("file.txt",)

    def test_insufficient_single_value_raises_error(self):
        """Test short option with equals syntax requiring at least two values.

        Verifies that when an option requires 2+ values, using equals syntax
        provides only one value and raises InsufficientOptionValuesError.

        Example: -f=file1.txt file2.txt file3.txt (equals provides only 1 value)
        """
        args = ["-f=file1.txt", "file2.txt", "file3.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files", short=frozenset({"f"}), arity=Arity(2, None)
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)

    def test_empty_string_satisfies_arity(self):
        """Test short option with empty string value using equals syntax.

        Verifies that -o= (with nothing after equals) is treated as an empty
        string value, which satisfies arity=1 requirement.

        Example: -o= (value is empty string "")
        """
        args = ["-o="]
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
        assert result.options["output"].value == ""

    def test_empty_string_satisfies_one_or_more_arity(self):
        """Test short option with empty string for arity requiring one or more values.

        Verifies that -f= (empty string) satisfies arity=1+ by providing a single
        empty string value.

        Example: -f= (value is tuple containing empty string: ("",))
        """
        args = ["-f="]
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files", short=frozenset({"f"}), arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["files"].value == ("",)

    def test_empty_value_for_flag_raises_error(self):
        """Test short option flag with empty value using equals syntax.

        Verifies that flags (arity=0) cannot accept values, even empty strings.
        Using -v= raises OptionDoesNotAcceptValueError.

        Example: -v= (error: flags don't accept values)
        """
        args = ["-v="]
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

    def test_value_for_flag_raises_error(self):
        """Test short option flag with a value using equals syntax.

        Verifies that flags (arity=0) cannot accept values. Using -v=true
        raises OptionDoesNotAcceptValueError.

        Example: -v=true (error: flags don't accept values)
        """
        args = ["-v=true"]
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

    def test_flag_equals_disabled_empty_value_raises_error(
        self,
    ):
        """Test flag with equals and empty value when flag values are disabled.

        Verifies that when allow_equals_for_flags=False, flags cannot accept
        values even with equals syntax. Raises FlagWithValueError.

        Example: -v= (error: flags cannot have values when disabled)
        """
        args = ["-v="]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    def test_flag_equals_enabled_empty_value_raises_error(self):
        """Test flag with equals and empty value when flag values are enabled.

        Verifies that when allow_equals_for_flags=True, an empty value after
        equals is invalid. Raises InvalidFlagValueError because empty string
        is not in truthy or falsey values.

        Example: -v= (error: empty string is not a valid flag value)
        """
        args = ["-v="]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)

    def test_flag_equals_disabled_value_raises_error(self):
        """Test flag with value using equals when flag values are disabled.

        Verifies that when allow_equals_for_flags=False, providing any value
        to a flag raises FlagWithValueError.

        Example: -v=true (error: flags cannot have values)
        """
        args = ["-v=true"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    def test_flag_equals_enabled_parses_truthy_falsey(self):
        """Test flag with valid truthy/falsey values when flag values are enabled.

        Verifies that when allow_equals_for_flags=True, flags can accept values
        from the default truthy and falsey value sets, correctly parsing them
        as True or False.

        Examples: -v=true, -v=false, -v=1, -v=0, etc.
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        for value in DEFAULT_FALSEY_VALUES:
            result = parser.parse([f"-v={value}"])
            assert result.options["verbose"].value is False

        for value in DEFAULT_TRUTHY_VALUES:
            result = parser.parse([f"-v={value}"])
            assert result.options["verbose"].value is True

    def test_custom_flag_values_at_option_level(self):
        """Test flag with custom truthy/falsey values defined at option level.

        Verifies that options can define custom truthy and falsey values that
        override the parser defaults. Tests with custom values "foo" (falsey)
        and "bar" (truthy).

        Examples: -v=foo (False), -v=bar (True)
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

        result = parser.parse(["-v=foo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-v=bar"])
        assert result.options["verbose"].value is True

    def test_custom_flag_values_at_parser_level(self):
        """Test flag with custom truthy/falsey values defined at parser level.

        Verifies that parsers can define default custom truthy and falsey values
        that apply to all flags. Tests with custom values "foo" (falsey) and
        "bar" (truthy).

        Examples: -v=foo (False), -v=bar (True)
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

        result = parser.parse(["-v=foo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-v=bar"])
        assert result.options["verbose"].value is True

    def test_invalid_flag_value_raises_error(self):
        """Test flag with value not in truthy or falsey value sets.

        Verifies that when allow_equals_for_flags=True and a value is provided
        that isn't in the truthy or falsey sets, InvalidFlagValueError is raised.

        Example: -v=invalid (error: "invalid" is not a valid flag value)
        """
        args = ["-v=invalid"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)


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


class TestShortOptionWithoutEquals:
    """Test short options using the -o value syntax (without equals)."""

    def test_consumes_next_argument(self):
        """Test short option requiring exactly one value from next argument.

        Verifies that a short option with arity=1 correctly consumes the next
        argument as its value when not using equals syntax.

        Example: -o file.txt
        """
        args = ["-o", "file.txt"]
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

    def test_flag_defaults_to_true(self):
        """Test short option flag that takes no arguments.

        Verifies that a flag (arity=0) can be used without providing any value
        and defaults to True.

        Example: -v (sets verbose to True)
        """
        args = ["-v"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_consumes_all_following_non_option_args(self):
        """Test short option that accepts zero or more values.

        Verifies that an option with arity=0+ consumes all following arguments
        that don't start with a dash, collecting them into a tuple.

        Example: -f file1.txt file2.txt (captures both files)
        """
        args = ["-f", "file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files", short=frozenset({"f"}), arity=Arity(0, None)
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["files"].value == ("file1.txt", "file2.txt")

    def test_missing_required_value_raises_error(self):
        """Test short option with insufficient values provided.

        Verifies that when an option requires 1+ values but none are provided,
        InsufficientOptionValuesError is raised.

        Example: -f (error: requires at least 1 value)
        """
        args = ["-f"]
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files", short=frozenset({"f"}), arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)


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
