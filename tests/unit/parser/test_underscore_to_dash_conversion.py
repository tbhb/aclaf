import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
)
from aclaf.parser._exceptions import UnknownOptionError
from aclaf.parser._types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    AccumulationMode,
)


class TestBasicConversion:
    def test_user_underscores_spec_dashes(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option", "value"])
        assert result.options["opt"].value == "value"
        # Alias is the canonical name from spec, not user input
        assert result.options["opt"].alias == "my-option"

    def test_user_dashes_spec_underscores(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my_option"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my-option", "value"])
        assert result.options["opt"].value == "value"
        # Alias is the canonical name from spec
        assert result.options["opt"].alias == "my_option"

    def test_user_dashes_spec_dashes_no_change(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my-option", "value"])
        assert result.options["opt"].value == "value"
        assert result.options["opt"].alias == "my-option"

    def test_conversion_disabled_requires_exact_match(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=False)

        # Exact match works
        result = parser.parse(["--my-option", "value"])
        assert result.options["opt"].value == "value"

        # Different separator fails
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--my_option", "value"])

    def test_conversion_enabled_by_default(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)  # Use default

        # Both separators should work with default=True
        result1 = parser.parse(["--my-option", "value"])
        result2 = parser.parse(["--my_option", "value"])
        assert result1.options["opt"].value == "value"
        assert result2.options["opt"].value == "value"

    def test_multiple_underscores_converted(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt",
                    long=frozenset({"my-long-option-name"}),
                    arity=EXACTLY_ONE_ARITY,
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_long_option_name", "value"])
        assert result.options["opt"].value == "value"

    def test_consecutive_underscores_converted(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my--option"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my__option", "value"])
        assert result.options["opt"].value == "value"

    def test_mixed_separators_in_input(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option-name"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # Input: my_option-name → normalized: my-option-name
        result = parser.parse(["--my_option-name", "value"])
        assert result.options["opt"].value == "value"

    def test_case_preserving(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"MyOption"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # Case preserved, but won't match without case_insensitive_options
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--My_Option", "value"])


class TestConversionInteractions:
    def test_conversion_with_case_insensitive(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option"}), arity=EXACTLY_ONE_ARITY
                )
            },
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
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"MY_OPTION"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(
            spec,
            convert_underscores_to_dashes=True,
            case_insensitive_options=True,
        )

        result = parser.parse(["--my-option", "value"])
        assert result.options["opt"].value == "value"

    def test_conversion_with_abbreviation(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"verbose-mode"}), arity=EXACTLY_ONE_ARITY
                )
            },
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
        spec = CommandSpec(
            name="cmd",
            options={
                "force": OptionSpec(
                    "force",
                    long=frozenset({"force-push"}),
                    negation_words=frozenset({"no"}),
                    arity=ZERO_ARITY,
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--no-force_push"])
        assert result.options["force"].value is False

    def test_conversion_with_negation_spec_underscores(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "force": OptionSpec(
                    "force",
                    long=frozenset({"force_push"}),
                    negation_words=frozenset({"no"}),
                    arity=ZERO_ARITY,
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # User types dashes in negated form
        result = parser.parse(["--no-force-push"])
        assert result.options["force"].value is False

    def test_conversion_with_equals_syntax(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option=value"])
        assert result.options["opt"].value == "value"

    def test_conversion_with_short_options_unaffected(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt",
                    short=frozenset({"o"}),
                    long=frozenset({"option"}),
                    arity=EXACTLY_ONE_ARITY,
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["-o", "value"])
        assert result.options["opt"].value == "value"

    def test_conversion_with_aliases(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt",
                    long=frozenset({"my-option", "my-opt"}),
                    arity=EXACTLY_ONE_ARITY,
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result1 = parser.parse(["--my_option", "value"])
        result2 = parser.parse(["--my_opt", "value"])
        assert result1.options["opt"].value == "value"
        assert result2.options["opt"].value == "value"

    def test_conversion_with_subcommand_options(self):
        spec = CommandSpec(
            name="git",
            subcommands={
                "commit": CommandSpec(
                    name="commit",
                    options={
                        "all": OptionSpec(
                            "all", long=frozenset({"all-changes"}), arity=ZERO_ARITY
                        )
                    },
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["commit", "--all_changes"])
        assert result.subcommand is not None
        assert result.subcommand.options["all"].value is True

    def test_conversion_with_accumulation(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    long=frozenset({"verbose-mode"}),
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--verbose_mode", "--verbose-mode"])
        assert result.options["verbose"].value == 2


class TestConversionEdgeCases:
    def test_spec_with_mixed_separators_exact_match_only(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option_name"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # User input with all underscores → normalized to all dashes
        # Spec "my-option_name" → normalized to "my-option-name"
        # These match!
        result = parser.parse(["--my_option_name", "value"])
        assert result.options["opt"].value == "value"

    def test_very_long_option_name(self):
        long_name = "this-is-a-very-long-option-name-with-many-dashes-for-testing"
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({long_name}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # Replace all dashes with underscores in input
        long_name_underscores = long_name.replace("-", "_")
        result = parser.parse([f"--{long_name_underscores}", "value"])
        assert result.options["opt"].value == "value"

    def test_two_character_option_names(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"ab"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--ab", "value"])
        assert result.options["opt"].value == "value"

    def test_empty_option_value(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({"my-option"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option", ""])
        assert result.options["opt"].value == ""

    def test_multiple_options_mixed_styles(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt1": OptionSpec(
                    "opt1", long=frozenset({"first-option"}), arity=EXACTLY_ONE_ARITY
                ),
                "opt2": OptionSpec(
                    "opt2", long=frozenset({"second_option"}), arity=EXACTLY_ONE_ARITY
                ),
                "opt3": OptionSpec(
                    "opt3", long=frozenset({"third-option"}), arity=EXACTLY_ONE_ARITY
                ),
            },
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
    def test_conversion_with_flag_option(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", long=frozenset({"verbose-mode"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--verbose_mode"])
        assert result.options["verbose"].value is True

    def test_conversion_with_flag_equals_syntax(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "force": OptionSpec(
                    "force", long=frozenset({"force-push"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(
            spec,
            convert_underscores_to_dashes=True,
            allow_equals_for_flags=True,
        )

        result = parser.parse(["--force_push=true"])
        assert result.options["force"].value is True

    def test_conversion_with_negated_flag(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "colors": OptionSpec(
                    "colors",
                    long=frozenset({"use-colors"}),
                    negation_words=frozenset({"no"}),
                    arity=ZERO_ARITY,
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--no-use_colors"])
        assert result.options["colors"].value is False


class TestConversionNested:
    def test_nested_subcommands_with_conversion(self):
        spec = CommandSpec(
            name="tool",
            subcommands={
                "config": CommandSpec(
                    name="config",
                    subcommands={
                        "set": CommandSpec(
                            name="set",
                            options={
                                "opt": OptionSpec(
                                    "opt",
                                    long=frozenset({"my-option"}),
                                    arity=EXACTLY_ONE_ARITY,
                                )
                            },
                        )
                    },
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["config", "set", "--my_option", "value"])
        assert result.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.options["opt"].value == "value"

    def test_parent_and_subcommand_options_both_converted(self):
        spec = CommandSpec(
            name="app",
            options={
                "config": OptionSpec(
                    "config", long=frozenset({"config-file"}), arity=EXACTLY_ONE_ARITY
                )
            },
            subcommands={
                "run": CommandSpec(
                    name="run",
                    options={
                        "verbose": OptionSpec(
                            "verbose",
                            long=frozenset({"verbose-mode"}),
                            arity=ZERO_ARITY,
                        )
                    },
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--config_file", "app.conf", "run", "--verbose_mode"])
        assert result.options["config"].value == "app.conf"
        assert result.subcommand is not None
        assert result.subcommand.options["verbose"].value is True
