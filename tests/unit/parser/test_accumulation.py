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
    """Test COLLECT accumulation mode.

    Basic accumulation, single occurrence, and order preservation are covered by
    property tests. These tests focus on specific interactions and edge cases.
    """

    def test_works_with_boolean_flags(self):
        """COLLECT mode works with boolean flags."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-v", "-v", "-v"])
        assert result.options["verbose"].value == (True, True, True)

    def test_works_with_multi_value_options(self):
        """COLLECT mode with options that accept multiple values."""
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == (("a", "b"), ("c", "d"))

    def test_works_alongside_other_options(self):
        """COLLECT mode works alongside other options."""
        spec = CommandSpec(
            name="cmd",
            options={
                "collect": OptionSpec(
                    "collect", accumulation_mode=AccumulationMode.COLLECT
                ),
                "normal": OptionSpec("normal", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--collect", "v1", "--normal", "n", "--collect", "v2"])
        assert result.options["collect"].value == ("v1", "v2")
        assert result.options["normal"].value == "n"


class TestCountMode:
    """Test COUNT accumulation mode.

    Basic counting behavior (single, zero, many occurrences) is covered by
    property tests. These tests focus on short flag clustering interactions.
    """

    def test_counts_combined_short_flags(self):
        """COUNT mode works with combined short flags."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vvv"])
        assert result.options["verbose"].value == 3

    def test_counts_mixed_flag_forms(self):
        """COUNT mode with mix of separate and combined flags."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vv", "-v", "-vvv"])
        assert result.options["verbose"].value == 6


class TestFirstWinsMode:
    """Test FIRST_WINS accumulation mode.

    Basic first-wins behavior (keeping first value) is covered by property tests.
    These tests focus on interactions with flags, arity, and option forms.
    """

    def test_accumulation_first_wins_with_flags(self):
        """FIRST_WINS works with boolean flags."""
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--flag", "--flag", "--flag"])
        assert result.options["flag"].value is True

    def test_accumulation_first_wins_with_multi_value_option(self):
        """FIRST_WINS with options accepting multiple values."""
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == ("a", "b")

    def test_first_wins_different_forms(self):
        """FIRST_WINS keeps first regardless of option form used."""
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    short=frozenset({"o"}),
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--output", "long.txt", "-o", "short.txt"])
        assert result.options["output"].value == "long.txt"


class TestLastWinsMode:
    """Test LAST_WINS accumulation mode (default).

    Basic last-wins behavior (keeping last value) is covered by property tests.
    These tests document the default mode and test specific interactions.
    """

    def test_last_wins_is_default(self):
        """LAST_WINS is the default accumulation mode."""
        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt")},  # No accumulation_mode specified
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "first", "--opt", "last"])
        assert result.options["opt"].value == "last"

    def test_last_wins_with_flags(self):
        """LAST_WINS works with boolean flags."""
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.LAST_WINS,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--flag", "--flag"])
        assert result.options["flag"].value is True

    def test_last_wins_with_multi_value_option(self):
        """LAST_WINS with options accepting multiple values."""
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.LAST_WINS,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == ("c", "d")


class TestErrorMode:
    """Test ERROR accumulation mode.

    Basic error behavior (raises on duplicate, allows single) is covered by
    property tests. These tests focus on interactions with flags and option forms.
    """

    def test_error_with_flags(self):
        """ERROR mode works with flags."""
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.ERROR,
                )
            },
        )
        parser = Parser(spec)

        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError):
            _ = parser.parse(["--flag", "--flag"])

    def test_error_different_forms_still_duplicate(self):
        """ERROR mode treats different forms as duplicate."""
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    short=frozenset({"o"}),
                    accumulation_mode=AccumulationMode.ERROR,
                ),
            },
        )
        parser = Parser(spec)

        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError):
            _ = parser.parse(["--output", "file1.txt", "-o", "file2.txt"])


class TestAccumulationModeInteractions:
    """Test interactions between accumulation modes and other features."""

    def test_accumulation_mode_with_const_value(self):
        """Accumulation modes work with const_value."""
        spec = CommandSpec(
            name="cmd",
            options={
                "mode": OptionSpec(
                    "mode",
                    arity=ZERO_ARITY,
                    const_value="debug",
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--mode", "--mode", "--mode"])
        assert result.options["mode"].value == ("debug", "debug", "debug")

    def test_accumulation_with_negation(self):
        """Accumulation modes work with negation words."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    arity=ZERO_ARITY,
                    negation_words=frozenset({"no"}),
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--verbose", "--no-verbose", "--verbose"])
        assert result.options["verbose"].value == (True, False, True)

    def test_different_accumulation_modes_per_option(self):
        """Different options can have different accumulation modes."""
        spec = CommandSpec(
            name="cmd",
            options={
                "collect": OptionSpec(
                    "collect", accumulation_mode=AccumulationMode.COLLECT
                ),
                "count": OptionSpec(
                    "count", arity=ZERO_ARITY, accumulation_mode=AccumulationMode.COUNT
                ),
                "first": OptionSpec(
                    "first", accumulation_mode=AccumulationMode.FIRST_WINS
                ),
                "last": OptionSpec(
                    "last", accumulation_mode=AccumulationMode.LAST_WINS
                ),
            },
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
            options={
                "range": OptionSpec(
                    "range",
                    arity=Arity(2, 4),
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
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
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)
            },
        )
        parser = Parser(spec)

        result = parser.parse([])
        assert "opt" not in result.options

    def test_error_message_contains_option_name(self):
        """ERROR mode exception includes the option name."""
        spec = CommandSpec(
            name="cmd",
            options={
                "myoption": OptionSpec(
                    "myoption", accumulation_mode=AccumulationMode.ERROR
                )
            },
        )
        parser = Parser(spec)

        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError) as exc_info:
            _ = parser.parse(["--myoption", "v1", "--myoption", "v2"])

        assert "myoption" in str(exc_info.value).lower()
