"""Edge case tests to achieve 100% coverage of non-defensive code paths.

These tests target specific uncovered lines in the parser implementation.
"""

import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.exceptions import (
    InsufficientOptionValuesError,
    InsufficientPositionalArgumentsError,
    UnknownOptionError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    Arity,
)


class TestLongOptionEdgeCases:
    """Edge cases for long option parsing."""

    def test_flag_with_value_from_next_args(self):
        """Flag with value from next arg (not inline) with allow_equals_for_flags.

        Tests the code path where a flag option receives its value from the next
        argument (not inline with =) when the parser allows flag values. This ensures
        the value is correctly consumed from next_args.

        Example: --verbose true (instead of --verbose=true)
        """
        args = ["--verbose", "true"]
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("verbose", is_flag=True)],
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        result = parser.parse(args)
        # Should parse "true" as the flag value
        assert result.options["verbose"].value is True


class TestShortOptionEdgeCases:
    """Edge cases for short option parsing."""

    def test_inner_flag_in_combined_options(self):
        """Inner option is a flag in combined short options.

        Tests the code path where all options in a combined short option string
        (like -abc) are flags. This ensures that each flag is correctly processed
        when combined with other flags.

        Example: -abc where a, b, and c are all flags
        """
        args = ["-abc"]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("a", is_flag=True),
                OptionSpec("b", is_flag=True),
                OptionSpec("c", is_flag=True),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["c"].value is True

    def test_last_option_with_const_value_in_combined(self):
        """Last option with const_value in combined short options.

        Tests the code path where the final option in a combined short option string
        has a const_value defined. This ensures that const values are correctly applied
        when the option appears in a combined form.

        Example: -abv where v has const_value="verbose_mode"
        """
        args = ["-abv"]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("a", is_flag=True),
                OptionSpec("b", is_flag=True),
                OptionSpec("v", is_flag=True, const_value="verbose_mode"),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["v"].value == "verbose_mode"

    def test_unknown_option_at_start_raises(self):
        """Unknown option at position 0 in short options raises.

        Tests the code path where an unknown option is encountered at the very
        beginning of a short option string. This ensures that UnknownOptionError
        is properly raised when the first character doesn't match any defined option.

        Example: -x where 'x' is not a valid option
        """
        args = ["-x"]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("a", is_flag=True),
                OptionSpec("f", is_flag=True),
            ],
        )
        parser = Parser(spec)
        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.name == "x"

    def test_combined_flags_ending_with_equals(self):
        """All-flag combined options ending with '=' creates empty inline value.

        Tests the code path where all characters in a combined short option string
        are valid flags, but the argument ends with '='. This creates an empty
        inline value for the last option.

        Example: -ab= where 'a' is a flag and 'b' gets empty string as value
        """
        args = ["-ab=", "value"]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("a", is_flag=True),
                OptionSpec("b", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        # b should get "" as inline value from the '='
        assert result.options["b"].value == ""


class TestOptionValueEdgeCases:
    """Edge cases for option value parsing."""

    def test_multi_value_option_stops_early_insufficient(self):
        """Multi-value option stops consuming early, resulting in insufficient values.

        Tests the code path where a multi-value option stops consuming arguments
        early (due to encountering another option or subcommand), resulting in fewer
        values than the minimum required. This ensures InsufficientOptionValuesError
        is raised even when enough arguments exist in the input.

        Example: --files file1.txt --other where --files requires at least 2 values
        """
        args = ["--files", "file1.txt", "--other"]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "files",
                    arity=Arity(2, 3),  # Requires at least 2 values
                ),
                OptionSpec("other", is_flag=True),
            ],
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.option_spec.name == "files"


class TestPositionalEdgeCases:
    """Edge cases for positional argument parsing."""

    def test_insufficient_positionals_finds_first_unsatisfied(self):
        """When insufficient total args, error reports first unsatisfied spec.

        Tests branch 555->564: Loop to find first unsatisfied spec.
        """
        args = ["file1.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("first", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("second", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("third", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError) as exc_info:
            _ = parser.parse(args)
        # Should report "second" as the first that can't be satisfied
        assert exc_info.value.spec_name == "second"
        assert exc_info.value.expected_min == 1
        assert exc_info.value.received == 0
