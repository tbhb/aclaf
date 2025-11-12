import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.exceptions import OptionCannotBeSpecifiedMultipleTimesError
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_OR_MORE_ARITY,
    AccumulationMode,
)


class TestStrictOptionsBeforePositionals:
    """Tests for strict_options_before_positionals configuration."""

    def test_long_option_after_positional_strict_mode(self):
        """Long option after positional treated as positional in strict mode."""
        args = ["file.txt", "--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", is_flag=True)},
            positionals={"files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=True)
        result = parser.parse(args)
        # --verbose should be treated as a positional, not an option
        assert "verbose" not in result.options
        assert result.positionals["files"].value == ("file.txt", "--verbose")

    def test_short_option_after_positional_strict_mode(self):
        """Short option after positional treated as positional in strict mode."""
        args = ["file.txt", "-v"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
            positionals={"files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=True)
        result = parser.parse(args)
        # -v should be treated as a positional, not an option
        assert "verbose" not in result.options
        assert result.positionals["files"].value == ("file.txt", "-v")

    def test_long_option_after_positional_non_strict(self):
        """Long option after positional should work normally in non-strict mode."""
        args = ["file.txt", "--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", is_flag=True)},
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=False)
        result = parser.parse(args)
        # --verbose should be parsed as an option
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"

    def test_short_option_after_positional_non_strict(self):
        """Short option after positional should work normally in non-strict mode."""
        args = ["file.txt", "-v"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=False)
        result = parser.parse(args)
        # -v should be parsed as an option
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"


class TestConstValueFlags:
    """Tests for flags with custom const_value instead of True/False."""

    def test_flag_with_const_value(self):
        """Flag with const_value should use that value instead of True."""
        args = ["--mode"]
        spec = CommandSpec(
            name="cmd",
            options={
                "mode": OptionSpec("mode", is_flag=True, const_value="production")
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["mode"].value == "production"

    def test_flag_without_const_value_uses_true(self):
        """Flag without const_value should default to True."""
        args = ["--verbose"]
        spec = CommandSpec(
            name="cmd", options={"verbose": OptionSpec("verbose", is_flag=True)}
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_const_value_with_accumulation_mode(self):
        """Multiple occurrences of const_value flag with COLLECT accumulation."""
        args = ["--mode", "--mode", "--mode"]
        spec = CommandSpec(
            name="cmd",
            options={
                "mode": OptionSpec(
                    "mode",
                    is_flag=True,
                    const_value="enabled",
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["mode"].value == ("enabled", "enabled", "enabled")


class TestNegationWordFlags:
    """Tests for flags with negation_words (e.g., --no-verbose)."""

    def test_flag_with_negation_prefix(self):
        """Flag with negation prefix should return False."""
        args = ["--no-verbose"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", is_flag=True, negation_words=frozenset({"no"})
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is False

    def test_flag_without_negation_prefix(self):
        """Flag without negation prefix should return True."""
        args = ["--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", is_flag=True, negation_words=frozenset({"no"})
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_flag_with_multiple_negation_words(self):
        """Flag with multiple negation words should recognize all."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    is_flag=True,
                    negation_words=frozenset({"no", "disable", "without"}),
                )
            },
        )
        parser = Parser(spec)

        # Test --no-verbose
        result = parser.parse(["--no-verbose"])
        assert result.options["verbose"].value is False

        # Test --disable-verbose
        result = parser.parse(["--disable-verbose"])
        assert result.options["verbose"].value is False

        # Test --without-verbose
        result = parser.parse(["--without-verbose"])
        assert result.options["verbose"].value is False

    def test_negation_with_accumulation(self):
        """Negation flags should work with accumulation modes."""
        args = ["--verbose", "--no-verbose", "--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    is_flag=True,
                    negation_words=frozenset({"no"}),
                    accumulation_mode=AccumulationMode.LAST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Last value wins, which is --verbose (True)
        assert result.options["verbose"].value is True


class TestFirstWinsAccumulation:
    """Tests for FIRST_WINS accumulation mode."""

    def test_first_wins_keeps_first_value(self):
        """FIRST_WINS mode should keep first value and ignore later ones."""
        args = ["--output", "file1.txt", "--output", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Should keep only first value
        assert result.options["output"].value == "file1.txt"

    def test_first_wins_with_multiple_occurrences(self):
        """FIRST_WINS mode with three occurrences keeps first."""
        args = ["-o", "a", "-o", "b", "-o", "c"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    short=frozenset({"o"}),
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == "a"

    def test_advanced_first_wins_with_flags(self):
        """FIRST_WINS mode with flag values."""
        args = ["--verbose", "--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    is_flag=True,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_advanced_first_wins_with_multi_value_option(self):
        """FIRST_WINS mode with multi-value arity."""
        args = ["--files", "a", "b", "--files", "c", "d"]
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=ZERO_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Should keep only first occurrence's values
        assert result.options["files"].value == ("a", "b")


class TestErrorAccumulation:
    """Tests for ERROR accumulation mode."""

    def test_advanced_error_on_duplicate(self):
        """ERROR mode should raise exception on duplicate option."""
        args = ["--output", "file1.txt", "--output", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.ERROR,
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.option_spec.name == "output"

    def test_advanced_error_allows_single_occurrence(self):
        """ERROR mode should allow single occurrence."""
        args = ["--output", "file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.ERROR,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == "file.txt"
