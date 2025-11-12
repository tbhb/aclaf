"""Error path tests for _parser.py.

This test module focuses on error conditions and edge cases in the parser's
main logic, including malformed input, insufficient values, and validation
failures.

Target coverage:
- Malformed argument handling (lines with error raises)
- Arity violation errors
- Value validation errors
- Edge case error conditions
"""

import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.exceptions import (
    FlagWithValueError,
    InsufficientOptionValuesError,
    InsufficientPositionalArgumentsError,
    InvalidFlagValueError,
    OptionCannotBeSpecifiedMultipleTimesError,
    OptionDoesNotAcceptValueError,
    UnexpectedPositionalArgumentError,
    UnknownOptionError,
    UnknownSubcommandError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    AccumulationMode,
    Arity,
)


class TestFlagWithValueErrors:
    """Test FlagWithValueError raised when flags receive unexpected values."""

    def test_flag_with_inline_value_not_allowed(self):
        """Flag with inline value raises error when flag values not allowed.

        Tests line 169 in _parser.py where a flag receives an inline value
        via = syntax but allow_equals_for_flags is False.
        """
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        with pytest.raises(
            FlagWithValueError,
            match=r"Flag option '--verbose'.* does not accept a value",
        ):
            _ = parser.parse(["--verbose=true"])

    def test_flag_with_inline_value_short_option_not_allowed(self):
        """Flag with inline value via short option raises error when not allowed.

        Tests line 614-616 in _parser.py for short option flag with inline
        value when allow_equals_for_flags is False.
        """
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        with pytest.raises(
            FlagWithValueError,
            match=r"Flag option '--verbose'.* does not accept a value",
        ):
            _ = parser.parse(["-v=true"])

    def test_zero_arity_non_flag_with_non_empty_inline_value(self):
        """Zero-arity non-flag with non-empty inline value raises FlagWithValueError.

        Tests line 284 in _parser.py where a zero-arity non-flag option
        receives a non-empty inline value.
        """
        spec = CommandSpec(
            name="test",
            options={
                "count": OptionSpec(
                    name="count",
                    arity=ZERO_ARITY,
                    is_flag=False,
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        with pytest.raises(
            FlagWithValueError,
            match=r"Flag option '--count'.* does not accept a value",
        ):
            _ = parser.parse(["--count=5"])


class TestOptionDoesNotAcceptValueErrors:
    """Test OptionDoesNotAcceptValueError for options that reject values."""

    def test_zero_arity_with_empty_inline_value(self):
        """Zero-arity option with empty inline value raises error.

        Tests line 279-281 in _parser.py where a zero-arity non-flag
        option receives an empty string via = syntax.
        """
        spec = CommandSpec(
            name="test",
            options={
                "count": OptionSpec(
                    name="count",
                    arity=ZERO_ARITY,
                    is_flag=False,
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        with pytest.raises(
            OptionDoesNotAcceptValueError,
            match=r"Option '--count'.* does not accept a value",
        ):
            _ = parser.parse(["--count="])

    def test_zero_arity_short_option_with_value_attempt(self):
        """Zero-arity short option followed by unknown chars raises error.

        Tests line 432-435 in _parser.py where a zero-arity option is
        followed by characters that look like a value attempt.
        """
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    is_flag=False,
                ),
                "extra": OptionSpec(
                    name="extra",
                    short=frozenset({"x"}),
                    arity=ZERO_ARITY,
                    is_flag=False,
                ),
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        # -vxabc: v and x are zero-arity, 'abc' are unknown chars
        # but length check ensures this is a value attempt
        with pytest.raises(
            OptionDoesNotAcceptValueError,
            match=r"Option '-x'.* does not accept a value",
        ):
            _ = parser.parse(["-vxabc"])

    def test_zero_arity_short_option_with_equals_not_allowed(self):
        """Zero-arity short option with = raises error when not allowed.

        Tests line 457-459 in _parser.py where a zero-arity option is
        followed by = but allow_equals_for_flags is False.
        """
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    is_flag=False,
                ),
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        with pytest.raises(
            OptionDoesNotAcceptValueError,
            match=r"Option '-v'.* does not accept a value",
        ):
            _ = parser.parse(["-v=value"])

    def test_zero_arity_non_flag_short_with_inline_value(self):
        """Zero-arity non-flag short option with inline value raises error.

        Tests line 657-659 in _parser.py for zero-arity non-flag as last
        short option with inline value when flag values not allowed.
        """
        spec = CommandSpec(
            name="test",
            options={
                "count": OptionSpec(
                    name="count",
                    short=frozenset({"c"}),
                    arity=ZERO_ARITY,
                    is_flag=False,
                ),
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        with pytest.raises(
            OptionDoesNotAcceptValueError,
            match=r"Option '-c'.* does not accept a value",
        ):
            _ = parser.parse(["-c=5"])


class TestInsufficientOptionValuesErrors:
    """Test InsufficientOptionValuesError for options requiring values."""

    def test_arity_requires_multiple_but_only_inline_value(self):
        """Option requiring multiple values with only inline value raises error.

        Tests line 237-239 in _parser.py where an option with arity.min > 1
        receives only an inline value via = syntax.
        """
        spec = CommandSpec(
            name="test",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(min=2, max=None),
                )
            },
        )
        parser = Parser(spec)

        with pytest.raises(
            InsufficientOptionValuesError,
            match=r"Insufficient values provided for option '--files'",
        ):
            _ = parser.parse(["--files=single.txt"])

    def test_inner_short_option_requires_values(self):
        """Inner short option requiring values consumes remaining chars as value.

        Tests line 508-509 in _parser.py where a non-flag short option
        with arity.min > 0 appears before the last position. The parser
        treats remaining characters as the inline value for that option.
        """
        spec = CommandSpec(
            name="test",
            options={
                "file": OptionSpec(
                    name="file",
                    short=frozenset({"f"}),
                    arity=EXACTLY_ONE_ARITY,
                ),
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                ),
            },
        )
        parser = Parser(spec)

        # -fv: f requires a value, consumes 'v' as its value (not an error)
        result = parser.parse(["-fv"])
        assert result.options["file"].value == "v"

    def test_short_option_with_known_option_following(self):
        """Short option requiring values with known option following raises error.

        Tests line 504-506 in _parser.py where an option requiring values
        is followed by a known option character with only 1 remaining char.
        """
        spec = CommandSpec(
            name="test",
            options={
                "alpha": OptionSpec(
                    name="alpha",
                    short=frozenset({"a"}),
                    is_flag=True,
                ),
                "file": OptionSpec(
                    name="file",
                    short=frozenset({"f"}),
                    arity=EXACTLY_ONE_ARITY,
                ),
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                ),
            },
        )
        parser = Parser(spec)

        # -afv: a is flag (OK), f requires value, v is known option (only 1 char)
        with pytest.raises(
            InsufficientOptionValuesError,
            match=r"Insufficient values provided for option '-f'",
        ):
            _ = parser.parse(["-afv"])

    def test_option_insufficient_values_from_args(self):
        """Option cannot get required values from next_args.

        Tests line 1058-1059 in _parser.py where an option cannot find
        enough values in next_args to satisfy its arity.min.
        """
        spec = CommandSpec(
            name="test",
            options={
                "output": OptionSpec(
                    name="output",
                    arity=Arity(min=2, max=3),
                )
            },
        )
        parser = Parser(spec)

        with pytest.raises(
            InsufficientOptionValuesError,
            match=r"Insufficient values provided for option '--output'",
        ):
            _ = parser.parse(["--output", "single.txt"])

    def test_short_option_inline_value_from_equals_arity_min_gt_1(self):
        """Short option with = value but arity.min > 1 raises error.

        Tests line 686-689 in _parser.py where the last short option has
        an inline value from = but requires multiple values.
        """
        spec = CommandSpec(
            name="test",
            options={
                "files": OptionSpec(
                    name="files",
                    short=frozenset({"f"}),
                    arity=Arity(min=2, max=None),
                )
            },
        )
        parser = Parser(spec)

        with pytest.raises(
            InsufficientOptionValuesError,
            match=r"Insufficient values provided for option '--files'",
        ):
            _ = parser.parse(["-f=single.txt"])

    def test_short_option_inline_not_equals_arity_min_gt_1(self):
        """Short option with inline value (not =) requires multiple values.

        Tests line 718-721 in _parser.py where the last short option has
        a direct inline value but arity.min > 1.
        """
        spec = CommandSpec(
            name="test",
            options={
                "files": OptionSpec(
                    name="files",
                    short=frozenset({"f"}),
                    arity=Arity(min=2, max=None),
                )
            },
        )
        parser = Parser(spec)

        # -fvalue: inline value without =, but needs 2+ values
        with pytest.raises(
            InsufficientOptionValuesError,
            match=r"Insufficient values provided for option '--files'",
        ):
            _ = parser.parse(["-fvalue"])

    def test_option_cannot_consume_enough_values_after_inline(self):
        """Option with inline start value cannot find remaining required values.

        Tests line 1138-1139 in _parser.py where an option has an inline
        start value but cannot find enough additional values in next_args.
        """
        spec = CommandSpec(
            name="test",
            options={
                "files": OptionSpec(
                    name="files",
                    short=frozenset({"f"}),
                    arity=Arity(min=3, max=None),
                )
            },
        )
        parser = Parser(spec)

        # -fvalue1 value2: has inline + 1 arg, but needs 3
        with pytest.raises(
            InsufficientOptionValuesError,
            match=r"Insufficient values provided for option '--files'",
        ):
            _ = parser.parse(["-fvalue1", "value2"])


class TestInvalidFlagValueErrors:
    """Test InvalidFlagValueError for invalid flag value strings."""

    def test_flag_with_empty_inline_value(self):
        """Flag with empty inline value raises InvalidFlagValueError.

        Tests line 989-992 in _parser.py where a flag receives an empty
        string via = syntax (e.g., --flag=).
        """
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    is_flag=True,
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        with pytest.raises(
            InvalidFlagValueError,
            match=r"Invalid value '' for option '--verbose'",
        ):
            _ = parser.parse(["--verbose="])

    def test_flag_with_invalid_inline_value(self):
        """Flag with invalid inline value raises InvalidFlagValueError.

        Tests line 1007-1009 in _parser.py where a flag receives an
        inline value that's not in truthy or falsey sets.
        """
        spec = CommandSpec(
            name="test",
            options={
                "debug": OptionSpec(
                    name="debug",
                    is_flag=True,
                    truthy_flag_values=frozenset({"yes", "true"}),
                    falsey_flag_values=frozenset({"no", "false"}),
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        with pytest.raises(
            InvalidFlagValueError,
            match=r"Invalid value 'maybe' for option '--debug'",
        ):
            _ = parser.parse(["--debug=maybe"])


class TestOptionAccumulationErrors:
    """Test errors related to option accumulation modes."""

    def test_error_accumulation_mode_duplicate_option(self):
        """Option with ERROR accumulation mode specified twice raises error.

        Tests line 1235-1237 in _parser.py where an option with
        AccumulationMode.ERROR is specified multiple times.
        """
        spec = CommandSpec(
            name="test",
            options={
                "output": OptionSpec(
                    name="output",
                    arity=ZERO_OR_ONE_ARITY,
                    accumulation_mode=AccumulationMode.ERROR,
                )
            },
        )
        parser = Parser(spec)

        with pytest.raises(
            OptionCannotBeSpecifiedMultipleTimesError,
            match=r"Option '--output'.* cannot be specified multiple times",
        ):
            _ = parser.parse(["--output", "file1.txt", "--output", "file2.txt"])


class TestPositionalErrors:
    """Test errors related to positional argument handling."""

    def test_insufficient_positional_arguments(self):
        """Insufficient positional arguments for required positionals raises error.

        Tests line 893-895 in _parser.py where not enough positional
        arguments are provided to satisfy positional specs.
        """
        spec = CommandSpec(
            name="test",
            positionals={
                "source": PositionalSpec(name="source", arity=EXACTLY_ONE_ARITY),
                "dest": PositionalSpec(name="dest", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)

        with pytest.raises(
            InsufficientPositionalArgumentsError,
            match=r"Positional argument 'dest' requires at least 1 value",
        ):
            _ = parser.parse(["source.txt"])

    def test_unexpected_positional_in_strict_mode(self):
        """Extra positional arguments in strict mode raise error.

        Tests line 933-936 in _parser.py where leftover positionals
        remain after grouping in strict_options_before_positionals mode.
        """
        spec = CommandSpec(
            name="test",
            positionals={
                "file": PositionalSpec(name="file", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec, strict_options_before_positionals=True)

        with pytest.raises(
            UnexpectedPositionalArgumentError,
            match=r"Unexpected positional argument 'extra.txt'",
        ):
            _ = parser.parse(["file.txt", "extra.txt"])


class TestUnknownOptionErrors:
    """Test UnknownOptionError for unrecognized option names."""

    def test_unknown_long_option(self):
        """Unknown long option raises UnknownOptionError.

        Tests error path when long option cannot be resolved via
        current_spec.resolve_option() call at line 152-154.
        """
        spec = CommandSpec(name="test", options={})
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError, match=r"Unknown option '--verbose'"):
            _ = parser.parse(["--verbose"])

    def test_unknown_short_option_first_character(self):
        """Unknown short option as first character raises error.

        Tests line 410-414 in _parser.py where the first character
        in a short option string cannot be resolved.
        """
        spec = CommandSpec(name="test", options={})
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError, match=r"Unknown option '-x'"):
            _ = parser.parse(["-x"])

    def test_unknown_short_option_middle_character(self):
        """Unknown character after flag treated as inline value raises error.

        Tests line 614-616 in _parser.py where a flag is followed by
        unknown characters, which are treated as an inline value attempt.
        """
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                )
            },
        )
        parser = Parser(spec)

        # -vx: v is flag, x treated as inline value (not allowed)
        with pytest.raises(
            FlagWithValueError,
            match=r"Flag option '--verbose'.* does not accept a value",
        ):
            _ = parser.parse(["-vx"])


class TestUnknownSubcommandErrors:
    """Test UnknownSubcommandError for unrecognized subcommands."""

    def test_unknown_subcommand_with_no_positionals(self):
        """Unknown subcommand when spec has subcommands but no positionals raises error.

        Tests line 812-814 in _parser.py where an argument cannot be
        resolved as a subcommand and the spec defines subcommands but
        no positionals.
        """
        sub_spec = CommandSpec(name="init")
        spec = CommandSpec(
            name="git",
            subcommands={
                "init": sub_spec,
            },
        )
        parser = Parser(spec)

        with pytest.raises(
            UnknownSubcommandError,
            match=r"Unknown subcommand 'unknowncmd'",
        ):
            _ = parser.parse(["unknowncmd"])


class TestEdgeCaseErrors:
    """Test edge cases and boundary conditions for error handling."""

    def test_multiple_insufficient_value_errors(self):
        """When insufficient values provided to second occurrence, raises error.

        This tests that the parser fails fast and reports insufficient
        values for options even on duplicate occurrences.
        """
        spec = CommandSpec(
            name="test",
            options={
                "output": OptionSpec(
                    name="output",
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)

        # Second --output has no value
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(["--output", "file1.txt", "--output"])

    def test_option_value_consumption_respects_positional_requirements(self):
        """Option value consumption stops to preserve required positionals.

        Tests that line 1128-1133 correctly prevents options from consuming
        values needed by required positionals.
        """
        spec = CommandSpec(
            name="test",
            options={
                "include": OptionSpec(
                    name="include",
                    short=frozenset({"i"}),
                    arity=ZERO_OR_MORE_ARITY,
                )
            },
            positionals={
                "source": PositionalSpec(name="source", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)

        # --include should not consume "source.txt" as it's required by positional
        result = parser.parse(["--include", "a.txt", "b.txt", "source.txt"])
        assert result.options["include"].value == ("a.txt", "b.txt")
        assert result.positionals["source"].value == "source.txt"

    def test_flag_value_from_next_args_not_in_value_sets(self):
        """Flag checks next arg value but doesn't consume if invalid.

        Tests line 1010-1014 in _parser.py where a flag checks the next
        argument but finds it's not in truthy/falsey sets, so returns
        True without consuming.
        """
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    is_flag=True,
                    truthy_flag_values=frozenset({"yes"}),
                    falsey_flag_values=frozenset({"no"}),
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        # --verbose followed by "maybe" (not in value sets)
        # Should default to True and not consume "maybe"
        result = parser.parse(["--verbose", "maybe"])
        assert result.options["verbose"].value is True
        assert result.positionals["args"].value == ("maybe",)
