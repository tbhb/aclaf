"""Tests for option accumulation modes.

This module comprehensively tests all 5 accumulation modes:
- COLLECT: Collect all values into a tuple
- COUNT: Count number of occurrences
- FIRST_WINS: Keep only the first value
- LAST_WINS: Keep only the last value (default)
- ERROR: Raise error on duplicate occurrences
"""

import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser
from aclaf.parser.exceptions import OptionCannotBeSpecifiedMultipleTimesError
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    AccumulationMode,
    Arity,
)


class TestCollectMode:
    """Test COLLECT accumulation mode."""

    def test_accumulates_all_values_as_tuple(self):
        """COLLECT mode collects all values into a tuple."""
        args = ["--opt", "val1", "--opt", "val2", "--opt", "val3"]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["opt"].value == ("val1", "val2", "val3")

    def test_single_occurrence_returns_tuple(self):
        """COLLECT with single occurrence returns tuple of one."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)],
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "value"])
        assert result.options["opt"].value == ("value",)

    def test_preserves_insertion_order(self):
        """COLLECT mode preserves insertion order."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)],
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "first", "--opt", "second", "--opt", "third"])
        assert result.options["opt"].value == ("first", "second", "third")

    def test_works_with_boolean_flags(self):
        """COLLECT mode works with boolean flags."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "verbose",
                    short=["v"],
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-v", "-v", "-v"])
        assert result.options["verbose"].value == (True, True, True)

    def test_works_with_multi_value_options(self):
        """COLLECT mode with options that accept multiple values."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == (("a", "b"), ("c", "d"))

    def test_works_alongside_other_options(self):
        """COLLECT mode works alongside other options."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("collect", accumulation_mode=AccumulationMode.COLLECT),
                OptionSpec("normal", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--collect", "v1", "--normal", "n", "--collect", "v2"])
        assert result.options["collect"].value == ("v1", "v2")
        assert result.options["normal"].value == "n"


class TestCountMode:
    """Test COUNT accumulation mode."""

    def test_counts_occurrences(self):
        """COUNT mode counts number of occurrences."""
        args = ["--flag", "--flag", "--flag"]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "flag", is_flag=True, accumulation_mode=AccumulationMode.COUNT
                ),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["flag"].value == 3

    def test_single_occurrence_returns_one(self):
        """COUNT with single occurrence returns 1."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "flag", arity=ZERO_ARITY, accumulation_mode=AccumulationMode.COUNT
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--flag"])
        assert result.options["flag"].value == 1

    def test_zero_occurrences_option_absent(self):
        """COUNT with no occurrences means option not in result."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "flag", arity=ZERO_ARITY, accumulation_mode=AccumulationMode.COUNT
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse([])
        assert "flag" not in result.options

    def test_counts_many_occurrences(self):
        """COUNT mode counts many occurrences."""
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

        result = parser.parse(["-v"] * 10)
        assert result.options["verbose"].value == 10

    def test_counts_combined_short_flags(self):
        """COUNT mode works with combined short flags."""
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

    def test_counts_mixed_flag_forms(self):
        """COUNT mode with mix of separate and combined flags."""
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

        result = parser.parse(["-vv", "-v", "-vvv"])
        assert result.options["verbose"].value == 6


class TestFirstWinsMode:
    """Test FIRST_WINS accumulation mode."""

    def test_first_wins_basic(self):
        """FIRST_WINS keeps the first value."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.FIRST_WINS)],
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "first", "--opt", "second", "--opt", "third"])
        assert result.options["opt"].value == "first"

    def test_first_wins_single_occurrence(self):
        """FIRST_WINS with single occurrence."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.FIRST_WINS)],
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "only"])
        assert result.options["opt"].value == "only"

    def test_first_wins_with_flags(self):
        """FIRST_WINS works with boolean flags."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--flag", "--flag", "--flag"])
        assert result.options["flag"].value is True

    def test_first_wins_with_multi_value_option(self):
        """FIRST_WINS with options accepting multiple values."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == ("a", "b")

    def test_first_wins_different_forms(self):
        """FIRST_WINS keeps first regardless of option form used."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "output",
                    short=["o"],
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--output", "long.txt", "-o", "short.txt"])
        assert result.options["output"].value == "long.txt"


class TestLastWinsMode:
    """Test LAST_WINS accumulation mode (default)."""

    def test_last_wins_basic(self):
        """LAST_WINS keeps the last value."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.LAST_WINS)],
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "first", "--opt", "second", "--opt", "last"])
        assert result.options["opt"].value == "last"

    def test_last_wins_is_default(self):
        """LAST_WINS is the default accumulation mode."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt")],  # No accumulation_mode specified
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "first", "--opt", "last"])
        assert result.options["opt"].value == "last"

    def test_last_wins_single_occurrence(self):
        """LAST_WINS with single occurrence."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.LAST_WINS)],
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "only"])
        assert result.options["opt"].value == "only"

    def test_last_wins_with_flags(self):
        """LAST_WINS works with boolean flags."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.LAST_WINS,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--flag", "--flag"])
        assert result.options["flag"].value is True

    def test_last_wins_with_multi_value_option(self):
        """LAST_WINS with options accepting multiple values."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.LAST_WINS,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == ("c", "d")


class TestErrorMode:
    """Test ERROR accumulation mode."""

    def test_error_on_duplicate(self):
        """ERROR mode raises on duplicate occurrence."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.ERROR)],
        )
        parser = Parser(spec)

        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError) as exc_info:
            _ = parser.parse(["--opt", "first", "--opt", "second"])

        assert "opt" in str(exc_info.value).lower()

    def test_error_allows_single_occurrence(self):
        """ERROR mode allows single occurrence."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.ERROR)],
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "value"])
        assert result.options["opt"].value == "value"

    def test_error_with_flags(self):
        """ERROR mode works with flags."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.ERROR,
                ),
            ],
        )
        parser = Parser(spec)

        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError):
            _ = parser.parse(["--flag", "--flag"])

    def test_error_different_forms_still_duplicate(self):
        """ERROR mode treats different forms as duplicate."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "output",
                    short=["o"],
                    accumulation_mode=AccumulationMode.ERROR,
                ),
            ],
        )
        parser = Parser(spec)

        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError):
            _ = parser.parse(["--output", "file1.txt", "-o", "file2.txt"])


class TestAccumulationModeInteractions:
    """Test interactions between accumulation modes and other features."""

    def test_accumulation_with_const_value(self):
        """Accumulation modes work with const_value."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "mode",
                    arity=ZERO_ARITY,
                    const_value="debug",
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--mode", "--mode", "--mode"])
        assert result.options["mode"].value == ("debug", "debug", "debug")

    def test_accumulation_with_negation(self):
        """Accumulation modes work with negation words."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "verbose",
                    arity=ZERO_ARITY,
                    negation_words=["no"],
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--verbose", "--no-verbose", "--verbose"])
        assert result.options["verbose"].value == (True, False, True)

    def test_different_accumulation_modes_per_option(self):
        """Different options can have different accumulation modes."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("collect", accumulation_mode=AccumulationMode.COLLECT),
                OptionSpec(
                    "count", arity=ZERO_ARITY, accumulation_mode=AccumulationMode.COUNT
                ),
                OptionSpec("first", accumulation_mode=AccumulationMode.FIRST_WINS),
                OptionSpec("last", accumulation_mode=AccumulationMode.LAST_WINS),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "--collect",
                "c1",
                "--count",
                "--first",
                "f1",
                "--last",
                "l1",
                "--collect",
                "c2",
                "--count",
                "--first",
                "f2",
                "--last",
                "l2",
            ]
        )
        assert result.options["collect"].value == ("c1", "c2")
        assert result.options["count"].value == 2
        assert result.options["first"].value == "f1"
        assert result.options["last"].value == "l2"

    def test_accumulation_with_arity_range(self):
        """Accumulation modes work with complex arity."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "range",
                    arity=Arity(2, 4),
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--range", "a", "b", "--range", "c", "d", "e"])
        assert result.options["range"].value == (("a", "b"), ("c", "d", "e"))


class TestAccumulationEdgeCases:
    """Test edge cases with accumulation modes."""

    def test_collect_empty_when_not_provided(self):
        """Option not in result when not provided (all modes)."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)],
        )
        parser = Parser(spec)

        result = parser.parse([])
        assert "opt" not in result.options

    def test_count_with_zero_arity_only(self):
        """COUNT mode is typically used with zero-arity flags."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "verbose",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--verbose"] * 5)
        assert result.options["verbose"].value == 5

    def test_error_message_contains_option_name(self):
        """ERROR mode exception includes the option name."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("myoption", accumulation_mode=AccumulationMode.ERROR)],
        )
        parser = Parser(spec)

        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError) as exc_info:
            _ = parser.parse(["--myoption", "v1", "--myoption", "v2"])

        assert "myoption" in str(exc_info.value).lower()
