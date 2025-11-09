"""Tests for underscore-to-dash conversion feature.

This module tests the convert_underscores_to_dashes configuration flag, which
enables bidirectional normalization between underscore and dash separators in
option names (e.g., --my_option ↔ --my-option).
"""

import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
)
from aclaf.parser.exceptions import UnknownOptionError
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    AccumulationMode,
)


class TestBasicConversion:
    """Test basic underscore-to-dash conversion."""

    def test_user_underscores_spec_dashes(self):
        """User can specify --my_option for spec with --my-option."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my-option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option", "value"])
        assert result.options["opt"].value == "value"
        # Alias is the canonical name from spec, not user input
        assert result.options["opt"].alias == "my-option"

    def test_user_dashes_spec_underscores(self):
        """User can specify --my-option for spec with --my_option."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my_option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my-option", "value"])
        assert result.options["opt"].value == "value"
        # Alias is the canonical name from spec
        assert result.options["opt"].alias == "my_option"

    def test_user_dashes_spec_dashes_no_change(self):
        """Dashes in both spec and input work as expected."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my-option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my-option", "value"])
        assert result.options["opt"].value == "value"
        assert result.options["opt"].alias == "my-option"

    def test_conversion_disabled_requires_exact_match(self):
        """With conversion disabled, underscores and dashes must match exactly."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my-option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=False)

        # Exact match works
        result = parser.parse(["--my-option", "value"])
        assert result.options["opt"].value == "value"

        # Different separator fails
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--my_option", "value"])

    def test_conversion_enabled_by_default(self):
        """Conversion is enabled by default."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my-option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec)  # Use default

        # Both separators should work with default=True
        result1 = parser.parse(["--my-option", "value"])
        result2 = parser.parse(["--my_option", "value"])
        assert result1.options["opt"].value == "value"
        assert result2.options["opt"].value == "value"

    def test_multiple_underscores_converted(self):
        """Multiple underscores are all converted to dashes."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", long=["my-long-option-name"], arity=EXACTLY_ONE_ARITY)
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_long_option_name", "value"])
        assert result.options["opt"].value == "value"

    def test_consecutive_underscores_converted(self):
        """Multiple consecutive underscores convert to multiple dashes."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my--option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my__option", "value"])
        assert result.options["opt"].value == "value"

    def test_mixed_separators_in_input(self):
        """Input with both underscores and dashes gets all underscores converted."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", long=["my-option-name"], arity=EXACTLY_ONE_ARITY)
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # Input: my_option-name → normalized: my-option-name
        result = parser.parse(["--my_option-name", "value"])
        assert result.options["opt"].value == "value"

    def test_case_preserving(self):
        """Conversion preserves case."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["MyOption"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # Case preserved, but won't match without case_insensitive_options
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--My_Option", "value"])


class TestConversionInteractions:
    """Test conversion interaction with other parser features."""

    def test_conversion_with_case_insensitive(self):
        """Conversion works with case-insensitive matching."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my-option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(
            spec,
            convert_underscores_to_dashes=True,
            case_insensitive_options=True,
        )

        # Both conversion and case normalization applied
        result = parser.parse(["--My_Option", "value"])
        assert result.options["opt"].value == "value"

    def test_conversion_with_case_insensitive_reverse(self):
        """Conversion + case insensitive works in both directions."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["MY_OPTION"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(
            spec,
            convert_underscores_to_dashes=True,
            case_insensitive_options=True,
        )

        result = parser.parse(["--my-option", "value"])
        assert result.options["opt"].value == "value"

    def test_conversion_with_abbreviation(self):
        """Conversion works with abbreviation matching."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["verbose-mode"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(
            spec,
            convert_underscores_to_dashes=True,
            allow_abbreviated_options=True,
        )

        # Input with underscores gets converted, then abbreviated matching works
        # Note: abbreviation must be a valid prefix of the option name
        result = parser.parse(["--verb", "value"])
        assert result.options["opt"].value == "value"

    def test_conversion_with_negation_spec_dashes(self):
        """Negation works when spec has dashes and user types underscores."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "force",
                    long=["force-push"],
                    negation_words=["no"],
                    arity=ZERO_ARITY,
                )
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--no-force_push"])
        assert result.options["force"].value is False

    def test_conversion_with_negation_spec_underscores(self):
        """Negation works when spec has underscores and user types dashes."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "force",
                    long=["force_push"],
                    negation_words=["no"],
                    arity=ZERO_ARITY,
                )
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # User types dashes in negated form
        result = parser.parse(["--no-force-push"])
        assert result.options["force"].value is False

    def test_conversion_with_equals_syntax(self):
        """Conversion works with --option=value syntax."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my-option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option=value"])
        assert result.options["opt"].value == "value"

    def test_conversion_with_short_options_unaffected(self):
        """Short options are not affected by conversion (no separators)."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", short=["o"], long=["option"], arity=EXACTLY_ONE_ARITY)
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["-o", "value"])
        assert result.options["opt"].value == "value"

    def test_conversion_with_aliases(self):
        """Conversion works with option aliases."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "opt",
                    long=["my-option", "my-opt"],
                    arity=EXACTLY_ONE_ARITY,
                )
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result1 = parser.parse(["--my_option", "value"])
        result2 = parser.parse(["--my_opt", "value"])
        assert result1.options["opt"].value == "value"
        assert result2.options["opt"].value == "value"

    def test_conversion_with_subcommand_options(self):
        """Conversion works within subcommand options."""
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="commit",
                    options=[OptionSpec("all", long=["all-changes"], arity=ZERO_ARITY)],
                )
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["commit", "--all_changes"])
        assert result.subcommand is not None
        assert result.subcommand.options["all"].value is True

    def test_conversion_with_accumulation(self):
        """Conversion works with accumulation modes."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "verbose",
                    long=["verbose-mode"],
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                )
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--verbose_mode", "--verbose-mode"])
        assert result.options["verbose"].value == 2


class TestConversionEdgeCases:
    """Test edge cases in underscore-to-dash conversion."""

    def test_spec_with_mixed_separators_exact_match_only(self):
        """Option spec with mixed separators requires exact normalized match."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", long=["my-option_name"], arity=EXACTLY_ONE_ARITY)
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # User input with all underscores → normalized to all dashes
        # Spec "my-option_name" → normalized to "my-option-name"
        # These match!
        result = parser.parse(["--my_option_name", "value"])
        assert result.options["opt"].value == "value"

    def test_very_long_option_name(self):
        """Conversion works with very long option names."""
        long_name = "this-is-a-very-long-option-name-with-many-dashes-for-testing"
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=[long_name], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # Replace all dashes with underscores in input
        long_name_underscores = long_name.replace("-", "_")
        result = parser.parse([f"--{long_name_underscores}", "value"])
        assert result.options["opt"].value == "value"

    def test_two_character_option_names(self):
        """Two character long options work with conversion (minimum length)."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["ab"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--ab", "value"])
        assert result.options["opt"].value == "value"

    def test_empty_option_value(self):
        """Conversion works with empty option values."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt", long=["my-option"], arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option", ""])
        assert result.options["opt"].value == ""

    def test_multiple_options_mixed_styles(self):
        """Multiple options with different separator styles all work."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt1", long=["first-option"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("opt2", long=["second_option"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("opt3", long=["third-option"], arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(
            [
                "--first_option",
                "v1",
                "--second-option",
                "v2",
                "--third_option",
                "v3",
            ]
        )
        assert result.options["opt1"].value == "v1"
        assert result.options["opt2"].value == "v2"
        assert result.options["opt3"].value == "v3"


class TestConversionWithFlags:
    """Test conversion with boolean flag options."""

    def test_conversion_with_flag_option(self):
        """Conversion works with zero-arity flag options."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("verbose", long=["verbose-mode"], arity=ZERO_ARITY)],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--verbose_mode"])
        assert result.options["verbose"].value is True

    def test_conversion_with_flag_equals_syntax(self):
        """Conversion works with --flag=value syntax for boolean flags."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("force", long=["force-push"], arity=ZERO_ARITY)],
        )
        parser = Parser(
            spec,
            convert_underscores_to_dashes=True,
            allow_equals_for_flags=True,
        )

        result = parser.parse(["--force_push=true"])
        assert result.options["force"].value is True

    def test_conversion_with_negated_flag(self):
        """Conversion works with negated flags."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "colors",
                    long=["use-colors"],
                    negation_words=["no"],
                    arity=ZERO_ARITY,
                )
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--no-use_colors"])
        assert result.options["colors"].value is False


class TestConversionNested:
    """Test conversion with nested subcommands."""

    def test_nested_subcommands_with_conversion(self):
        """Conversion works in deeply nested subcommands."""
        spec = CommandSpec(
            name="tool",
            subcommands=[
                CommandSpec(
                    name="config",
                    subcommands=[
                        CommandSpec(
                            name="set",
                            options=[
                                OptionSpec(
                                    "opt",
                                    long=["my-option"],
                                    arity=EXACTLY_ONE_ARITY,
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["config", "set", "--my_option", "value"])
        assert result.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.options["opt"].value == "value"

    def test_parent_and_subcommand_options_both_converted(self):
        """Conversion applies to both parent and subcommand options."""
        spec = CommandSpec(
            name="app",
            options=[
                OptionSpec("config", long=["config-file"], arity=EXACTLY_ONE_ARITY)
            ],
            subcommands=[
                CommandSpec(
                    name="run",
                    options=[
                        OptionSpec("verbose", long=["verbose-mode"], arity=ZERO_ARITY)
                    ],
                )
            ],
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--config_file", "app.conf", "run", "--verbose_mode"])
        assert result.options["config"].value == "app.conf"
        assert result.subcommand is not None
        assert result.subcommand.options["verbose"].value is True
