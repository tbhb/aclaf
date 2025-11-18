import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    PositionalSpec,
)
from aclaf.parser._types import Arity


class TestCommandSpecNameValidation:
    def test_valid_command_name(self):
        spec = CommandSpec(name="mycommand")
        assert spec.name == "mycommand"

    def test_valid_command_name_with_dashes(self):
        spec = CommandSpec(name="my-command")
        assert spec.name == "my-command"

    def test_valid_command_name_with_underscores(self):
        spec = CommandSpec(name="my_command")
        assert spec.name == "my_command"

    def test_valid_command_name_with_numbers(self):
        spec = CommandSpec(name="cmd123")
        assert spec.name == "cmd123"

    def test_invalid_empty_command_name(self):
        with pytest.raises(ValueError, match=r"(?i).*must not be empty.*"):
            _ = CommandSpec(name="")

    def test_invalid_command_name_starts_with_number(self):
        with pytest.raises(
            ValueError, match=r"(?i).*must start with an alphabetic character.*"
        ):
            _ = CommandSpec(name="123cmd")

    def test_invalid_command_name_starts_with_dash(self):
        with pytest.raises(
            ValueError, match=r"(?i).*must start with an alphabetic character.*"
        ):
            _ = CommandSpec(name="-command")

    def test_invalid_command_name_special_characters(self):
        with pytest.raises(ValueError, match=r".*"):
            _ = CommandSpec(name="my@command")


class TestCommandSpecAliasValidation:
    def test_valid_single_alias(self):
        spec = CommandSpec(name="remove", aliases=frozenset({"rm"}))
        assert "rm" in spec.aliases

    def test_valid_multiple_aliases(self):
        spec = CommandSpec(name="remove", aliases=frozenset({"rm", "del"}))
        assert "rm" in spec.aliases
        assert "del" in spec.aliases

    def test_invalid_alias_format(self):
        with pytest.raises(ValueError, match=r"(?i).*alias.*"):
            _ = CommandSpec(name="cmd", aliases=frozenset({"@invalid"}))


class TestCommandSpecOptionValidation:
    def test_valid_single_option(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose")},
        )
        assert "verbose" in spec.options

    def test_valid_multiple_options(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose"),
                "output": OptionSpec("output"),
            },
        )
        assert "verbose" in spec.options
        assert "output" in spec.options

    def test_duplicate_option_names(self):
        with pytest.raises(ValueError, match=r"(?i).*duplicate.*output.*"):
            _ = CommandSpec(
                name="cmd",
                options={
                    "output": OptionSpec("output", long=frozenset({"output"})),
                    "out": OptionSpec(
                        "out", long=frozenset({"output"})
                    ),  # Duplicate long name
                },
            )

    def test_duplicate_short_option_names(self):
        with pytest.raises(ValueError, match=r"(?i).*duplicate.*v.*"):
            _ = CommandSpec(
                name="cmd",
                options={
                    "verbose": OptionSpec("verbose", short=frozenset({"v"})),
                    "version": OptionSpec(
                        "version", short=frozenset({"v"})
                    ),  # Duplicate short name
                },
            )

    def test_long_short_option_collision(self):
        # This should work - they're different namespaces
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec("output", long=frozenset({"output"})),
                "o": OptionSpec("o", short=frozenset({"o"})),
            },
        )
        assert "output" in spec.options
        assert "o" in spec.options

    def test_multiple_long_names_same_option(self):
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", long=frozenset({"output", "out"}))},
        )
        assert "output" in spec.options

    def test_multiple_long_names_collision(self):
        with pytest.raises(ValueError, match=r"(?i).*duplicate.*"):
            _ = CommandSpec(
                name="cmd",
                options={
                    "output": OptionSpec("output", long=frozenset({"output", "out"})),
                    # Collides with first option's alias
                    "other": OptionSpec("other", long=frozenset({"out"})),
                },
            )


class TestCommandSpecPositionalValidation:
    def test_valid_single_positional(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=Arity(1, 1))},
        )
        assert "file" in spec.positionals

    def test_valid_multiple_positionals(self):
        spec = CommandSpec(
            name="cmd",
            positionals={
                "source": PositionalSpec("source", arity=Arity(1, 1)),
                "dest": PositionalSpec("dest", arity=Arity(1, 1)),
            },
        )
        assert "source" in spec.positionals
        assert "dest" in spec.positionals


class TestCommandSpecSubcommandValidation:
    def test_valid_single_subcommand(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        assert "start" in spec.subcommands

    def test_valid_multiple_subcommands(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "stop": CommandSpec(name="stop"),
            },
        )
        assert "start" in spec.subcommands
        assert "stop" in spec.subcommands

    def test_duplicate_subcommand_names(self):
        with pytest.raises(ValueError, match=r"(?i).*duplicate.*"):
            _ = CommandSpec(
                name="cmd",
                subcommands={
                    "start": CommandSpec(name="start"),
                    "start2": CommandSpec(name="start"),  # Duplicate name "start"
                },
            )

    def test_subcommand_alias_collision(self):
        with pytest.raises(ValueError, match=r"(?i).*duplicate.*rm.*"):
            _ = CommandSpec(
                name="cmd",
                subcommands={
                    "remove": CommandSpec(name="remove", aliases=frozenset({"rm"})),
                    "rm": CommandSpec(
                        name="rm"
                    ),  # Collides with first subcommand's alias
                },
            )

    def test_subcommand_aliases_collision(self):
        with pytest.raises(ValueError, match=r"(?i).*duplicate.*"):
            _ = CommandSpec(
                name="cmd",
                subcommands={
                    "remove": CommandSpec(name="remove", aliases=frozenset({"rm"})),
                    "delete": CommandSpec(
                        name="delete", aliases=frozenset({"rm"})
                    ),  # Duplicate alias
                },
            )


class TestOptionSpecNameValidation:
    def test_valid_option_name(self):
        opt = OptionSpec("verbose")
        assert opt.name == "verbose"

    def test_valid_option_name_with_dashes(self):
        opt = OptionSpec("my-option")
        assert opt.name == "my-option"

    def test_valid_option_name_with_underscores(self):
        opt = OptionSpec("my_option")
        assert opt.name == "my_option"

    def test_valid_single_character_option_name(self):
        opt = OptionSpec("v")
        assert opt.name == "v"

    def test_invalid_empty_option_name(self):
        with pytest.raises(ValueError, match=r"(?i).*must not be empty.*"):
            _ = OptionSpec("")

    def test_invalid_option_name_starts_with_dash(self):
        with pytest.raises(ValueError, match=r".*"):
            _ = OptionSpec("-option")

    def test_invalid_option_name_ends_with_dash(self):
        with pytest.raises(ValueError, match=r".*"):
            _ = OptionSpec("option-")


class TestOptionSpecLongNameValidation:
    def test_valid_long_name(self):
        opt = OptionSpec("opt", long=frozenset({"option"}))
        assert "option" in opt.long

    def test_valid_multiple_long_names(self):
        opt = OptionSpec("opt", long=frozenset({"option", "output"}))
        assert "option" in opt.long
        assert "output" in opt.long

    def test_auto_long_name_from_option_name(self):
        opt = OptionSpec("verbose")
        assert "verbose" in opt.long

    def test_no_auto_long_name_for_single_char(self):
        opt = OptionSpec("v")
        assert len(opt.long) == 0

    def test_invalid_long_name_too_short(self):
        with pytest.raises(ValueError, match=r"(?i).*at least two characters.*"):
            _ = OptionSpec("opt", long=frozenset({"o"}))

    def test_invalid_long_name_starts_with_dash(self):
        with pytest.raises(ValueError, match=r".*"):
            _ = OptionSpec("opt", long=frozenset({"-option"}))

    def test_invalid_long_name_ends_with_dash(self):
        with pytest.raises(ValueError, match=r".*"):
            _ = OptionSpec("opt", long=frozenset({"option-"}))


class TestOptionSpecShortNameValidation:
    def test_valid_short_name(self):
        opt = OptionSpec("verbose", short=frozenset({"v"}))
        assert "v" in opt.short

    def test_valid_multiple_short_names(self):
        opt = OptionSpec("verbose", short=frozenset({"v", "V"}))
        assert "v" in opt.short
        assert "V" in opt.short

    def test_auto_short_name_from_option_name(self):
        opt = OptionSpec("v")
        assert "v" in opt.short

    def test_no_auto_short_name_for_multi_char(self):
        opt = OptionSpec("verbose")
        assert len(opt.short) == 0

    def test_invalid_short_name_too_long(self):
        with pytest.raises(ValueError, match=r"(?i).*exactly one character.*"):
            _ = OptionSpec("opt", short=frozenset({"verb"}))

    def test_invalid_short_name_special_character(self):
        with pytest.raises(ValueError, match=r".*"):
            _ = OptionSpec("opt", short=frozenset({"@"}))


class TestOptionSpecArityValidation:
    def test_valid_arity_zero(self):
        opt = OptionSpec("verbose", arity=Arity(0, 0))
        assert opt.arity == Arity(0, 0)

    def test_valid_arity_one(self):
        opt = OptionSpec("output", arity=Arity(1, 1))
        assert opt.arity == Arity(1, 1)

    def test_valid_arity_unbounded(self):
        opt = OptionSpec("files", arity=Arity(0, None))
        assert opt.arity == Arity(0, None)

    def test_valid_arity_range(self):
        opt = OptionSpec("files", arity=Arity(2, 5))
        assert opt.arity == Arity(2, 5)

    def test_invalid_arity_negative_min(self):
        with pytest.raises(ValueError, match=r"(?i).*negative.*"):
            _ = OptionSpec("opt", arity=Arity(-1, 1))

    def test_invalid_arity_negative_max(self):
        with pytest.raises(ValueError, match=r"(?i).*negative.*"):
            _ = OptionSpec("opt", arity=Arity(0, -1))

    def test_invalid_arity_min_greater_than_max(self):
        with pytest.raises(ValueError, match=r"(?i).*less than maximum.*"):
            _ = OptionSpec("opt", arity=Arity(5, 2))


class TestOptionSpecFlagValueValidation:
    def test_valid_truthy_values(self):
        opt = OptionSpec("verbose", truthy_flag_values=frozenset({"yes", "y"}))
        assert opt.truthy_flag_values is not None
        assert "yes" in opt.truthy_flag_values
        assert "y" in opt.truthy_flag_values

    def test_valid_falsey_values(self):
        opt = OptionSpec("verbose", falsey_flag_values=frozenset({"no", "n"}))
        assert opt.falsey_flag_values is not None
        assert "no" in opt.falsey_flag_values
        assert "n" in opt.falsey_flag_values

    def test_invalid_overlapping_truthy_falsey(self):
        with pytest.raises(ValueError, match=r"(?i).*must not overlap.*maybe.*"):
            _ = OptionSpec(
                "verbose",
                truthy_flag_values=frozenset({"yes", "maybe"}),
                falsey_flag_values=frozenset({"no", "maybe"}),  # Overlap
            )


class TestOptionSpecNegationWordValidation:
    def test_valid_single_negation_word(self):
        opt = OptionSpec("verbose", negation_words=frozenset({"no"}))
        assert opt.negation_words is not None
        assert "no" in opt.negation_words

    def test_valid_multiple_negation_words(self):
        opt = OptionSpec("verbose", negation_words=frozenset({"no", "without"}))
        assert opt.negation_words is not None
        assert "no" in opt.negation_words
        assert "without" in opt.negation_words

    def test_invalid_empty_negation_word(self):
        with pytest.raises(ValueError, match=r"(?i).*at least one character.*"):
            _ = OptionSpec("verbose", negation_words=frozenset({""}))

    def test_invalid_negation_word_with_whitespace(self):
        with pytest.raises(ValueError, match=r"(?i).*must not contain whitespace.*"):
            _ = OptionSpec("verbose", negation_words=frozenset({"no space"}))


class TestPositionalSpecValidation:
    def test_valid_positional_name(self):
        pos = PositionalSpec("file", arity=Arity(1, 1))
        assert pos.name == "file"

    def test_valid_positional_arity_one(self):
        pos = PositionalSpec("file", arity=Arity(1, 1))
        assert pos.arity == Arity(1, 1)

    def test_valid_positional_arity_unbounded(self):
        pos = PositionalSpec("files", arity=Arity(0, None))
        assert pos.arity == Arity(0, None)

    def test_invalid_positional_arity_negative(self):
        with pytest.raises(ValueError, match=r".*"):
            _ = PositionalSpec("file", arity=Arity(-1, 1))


class TestComplexValidationScenarios:
    def test_deeply_nested_subcommands(self):
        spec = CommandSpec(
            name="root",
            subcommands={
                "level1": CommandSpec(
                    name="level1",
                    subcommands={
                        "level2": CommandSpec(
                            name="level2",
                            subcommands={
                                "level3": CommandSpec(name="level3"),
                            },
                        ),
                    },
                ),
            },
        )
        assert "level1" in spec.subcommands

    def test_command_with_all_features(self):
        spec = CommandSpec(
            name="tool",
            aliases=frozenset({"t"}),
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=Arity(0, 0)
                ),
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=Arity(1, 1)
                ),
            },
            positionals={
                "input": PositionalSpec("input", arity=Arity(1, 1)),
                "extras": PositionalSpec("extras", arity=Arity(0, None)),
            },
            subcommands={
                "process": CommandSpec(name="process"),
            },
        )
        assert spec.name == "tool"
        assert "t" in spec.aliases
        assert "verbose" in spec.options
        assert "input" in spec.positionals
        assert "process" in spec.subcommands
