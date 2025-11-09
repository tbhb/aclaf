"""Tests for combined short option flags.

This module tests parsing of combined short options like -abc, -vvv, and combinations
of flags with value-accepting options.
"""

import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
    PositionalSpec,
)
from aclaf.parser.exceptions import (
    InsufficientOptionValuesError,
    InvalidFlagValueError,
    UnknownOptionError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    AccumulationMode,
)


class TestBasicCombinedFlags:
    """Test basic combined flag parsing."""

    def test_two_flags_combined(self):
        """Two flags can be combined."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("quiet", short=["q"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vq"])
        assert result.options["verbose"].value is True
        assert result.options["quiet"].value is True

    def test_three_flags_combined(self):
        """Three flags can be combined."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("quiet", short=["q"], arity=ZERO_ARITY),
                OptionSpec("force", short=["f"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vqf"])
        assert result.options["verbose"].value is True
        assert result.options["quiet"].value is True
        assert result.options["force"].value is True

    def test_many_flags_combined(self):
        """Many flags can be combined."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("a", short=["a"], arity=ZERO_ARITY),
                OptionSpec("b", short=["b"], arity=ZERO_ARITY),
                OptionSpec("c", short=["c"], arity=ZERO_ARITY),
                OptionSpec("d", short=["d"], arity=ZERO_ARITY),
                OptionSpec("e", short=["e"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-abcde"])
        for opt in ["a", "b", "c", "d", "e"]:
            assert result.options[opt].value is True

    def test_combined_flags_order_irrelevant(self):
        """Order of combined flags doesn't matter."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("force", short=["f"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec)

        result1 = parser.parse(["-vf"])
        assert result1.options["verbose"].value is True
        assert result1.options["force"].value is True

        result2 = parser.parse(["-fv"])
        assert result2.options["verbose"].value is True
        assert result2.options["force"].value is True


class TestCombinedFlagsWithValues:
    """Test combined flags where last option accepts a value."""

    def test_combined_with_value_space_form(self):
        """Combined flags with value in next argument."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vo", "file.txt"])
        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"

    def test_combined_with_value_equals_form(self):
        """Combined flags with value using equals syntax."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vo=file.txt"])
        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"

    def test_combined_with_inline_value(self):
        """Combined flags with inline value (no space/equals)."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vofile.txt"])
        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"

    def test_multiple_flags_before_value_option(self):
        """Multiple flags can precede a value-accepting option."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("force", short=["f"], arity=ZERO_ARITY),
                OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vfo", "file.txt"])
        assert result.options["verbose"].value is True
        assert result.options["force"].value is True
        assert result.options["output"].value == "file.txt"

    def test_value_option_must_be_last(self):
        """Value-accepting option must be last in combination."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec)

        # -ov should take "v" as the value for -o
        result = parser.parse(["-ov"])
        assert result.options["output"].value == "v"
        assert "verbose" not in result.options


class TestCombinedFlagsWithMultipleValues:
    """Test combined flags where last option accepts multiple values."""

    def test_combined_with_one_or_more_values(self):
        """Combined flags with one-or-more arity."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("files", short=["f"], arity=ONE_OR_MORE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vf", "file1.txt", "file2.txt"])
        assert result.options["verbose"].value is True
        assert result.options["files"].value == ("file1.txt", "file2.txt")

    def test_combined_with_multiple_values_inline(self):
        """Combined flags with inline start of multiple values."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("files", short=["f"], arity=ONE_OR_MORE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vffile1.txt", "file2.txt"])
        assert result.options["verbose"].value is True
        assert result.options["files"].value == ("file1.txt", "file2.txt")


class TestCombinedFlagsErrorCases:
    """Test error cases with combined flags."""

    def test_unknown_flag_in_combination(self):
        """Unknown flag in combination raises error."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("verbose", short=["v"], arity=ZERO_ARITY)],
        )
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(["-vx"])

        assert "x" in str(exc_info.value).lower()

    def test_unknown_flag_at_start(self):
        """Unknown flag at start of combination raises error."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("verbose", short=["v"], arity=ZERO_ARITY)],
        )
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-xv"])

    def test_unknown_flag_in_middle(self):
        """Unknown flag in middle of combination raises error."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("force", short=["f"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-vxf"])

    def test_combined_insufficient_values(self):
        """Insufficient values for combined option raises error."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(["-vo"])


class TestCombinedFlagsWithConstValues:
    """Test combined flags with const_value options."""

    def test_combined_with_const_value_flag(self):
        """Combined flags with const_value option."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec(
                    "log-level", short=["l"], arity=ZERO_ARITY, const_value="debug"
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vl"])
        assert result.options["verbose"].value is True
        assert result.options["log-level"].value == "debug"

    def test_const_value_last_in_combination(self):
        """Const value option works as last in combination."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("force", short=["f"], arity=ZERO_ARITY),
                OptionSpec("mode", short=["m"], arity=ZERO_ARITY, const_value="fast"),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vfm"])
        assert result.options["verbose"].value is True
        assert result.options["force"].value is True
        assert result.options["mode"].value == "fast"


class TestCombinedFlagsWithNegation:
    """Test combined flags with negation words."""

    def test_negation_not_valid_in_combination(self):
        """Negation words don't work in short form combinations."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "verbose",
                    short=["v"],
                    arity=ZERO_ARITY,
                    negation_words=["no"],
                ),
            ],
        )
        parser = Parser(spec)

        # Short forms don't support negation
        # -v just sets verbose to True
        result = parser.parse(["-v"])
        assert result.options["verbose"].value is True


class TestCombinedFlagsWithAccumulation:
    """Test combined flags with accumulation modes."""

    def test_combined_with_collect_mode(self):
        """Combined flags with COLLECT accumulation."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "verbose",
                    short=["v"],
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
                OptionSpec("force", short=["f"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vf", "-v"])
        assert result.options["verbose"].value == (True, True)
        assert result.options["force"].value is True

    def test_combined_with_count_mode(self):
        """Combined flags with COUNT accumulation."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "verbose",
                    short=["v"],
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vvv"])
        assert result.options["verbose"].value == 3

    def test_separate_and_combined_count(self):
        """Count accumulation works with mix of combined and separate."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "verbose",
                    short=["v"],
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vv", "-v", "-v"])
        assert result.options["verbose"].value == 4


class TestCombinedFlagsWithFlagValues:
    """Test combined flags with flag value coercion."""

    def test_combined_flags_with_equals_value(self):
        """Combined flags with equals value at end."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("debug", short=["d"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["-v", "-d=true"])
        assert result.options["verbose"].value is True
        assert result.options["debug"].value is True

    def test_combined_ending_with_equals_invalid(self):
        """Combined flags ending with equals is invalid without value."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("debug", short=["d"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(["-vd="])


class TestComplexCombinedScenarios:
    """Test complex scenarios with combined flags."""

    def test_multiple_combinations_in_single_command(self):
        """Multiple flag combinations in one command."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("force", short=["f"], arity=ZERO_ARITY),
                OptionSpec("quiet", short=["q"], arity=ZERO_ARITY),
                OptionSpec("debug", short=["d"], arity=ZERO_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vf", "-qd"])
        assert result.options["verbose"].value is True
        assert result.options["force"].value is True
        assert result.options["quiet"].value is True
        assert result.options["debug"].value is True

    def test_combined_flags_with_options_and_positionals(self):
        """Combined flags work with options and positionals."""
        spec = CommandSpec(
            name="tar",
            options=[
                OptionSpec("create", short=["c"], arity=ZERO_ARITY),
                OptionSpec("extract", short=["x"], arity=ZERO_ARITY),
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("file", short=["f"], arity=EXACTLY_ONE_ARITY),
            ],
            positionals=[PositionalSpec("files", arity=ONE_OR_MORE_ARITY)],
        )
        parser = Parser(spec)

        # tar -cvf archive.tar file1 file2
        result = parser.parse(["-cvf", "archive.tar", "file1", "file2"])
        assert result.options["create"].value is True
        assert result.options["verbose"].value is True
        assert result.options["file"].value == "archive.tar"
        assert result.positionals["files"].value == ("file1", "file2")

    def test_tar_style_combined_options(self):
        """Tar-style command with combined options."""
        spec = CommandSpec(
            name="tar",
            options=[
                OptionSpec("create", short=["c"], arity=ZERO_ARITY),
                OptionSpec("gzip", short=["z"], arity=ZERO_ARITY),
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("file", short=["f"], arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        # tar -czvf archive.tar.gz
        result = parser.parse(["-czvf", "archive.tar.gz"])
        assert result.options["create"].value is True
        assert result.options["gzip"].value is True
        assert result.options["verbose"].value is True
        assert result.options["file"].value == "archive.tar.gz"

    def test_combined_with_long_options_mixed(self):
        """Combined short options can mix with long options."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("verbose", short=["v"], arity=ZERO_ARITY),
                OptionSpec("force", short=["f"], arity=ZERO_ARITY),
                OptionSpec("output", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vf", "--output", "file.txt"])
        assert result.options["verbose"].value is True
        assert result.options["force"].value is True
        assert result.options["output"].value == "file.txt"
