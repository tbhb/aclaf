import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.exceptions import (
    DuplicateOptionError,
    FlagWithValueError,
    InsufficientOptionValuesError,
    InsufficientPositionalArgumentsError,
    InvalidFlagValueError,
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
    def test_flag_with_inline_value_not_allowed(self):
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
    def test_zero_arity_with_empty_inline_value(self):
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
    def test_arity_requires_multiple_but_only_inline_value(self):
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
    def test_flag_with_empty_inline_value(self):
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
    def test_error_accumulation_mode_duplicate_option(self):
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
            DuplicateOptionError,
            match=r"Option '--output'.* cannot be specified multiple times",
        ):
            _ = parser.parse(["--output", "file1.txt", "--output", "file2.txt"])


class TestPositionalErrors:
    def test_insufficient_positional_arguments(self):
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
    def test_unknown_long_option(self):
        spec = CommandSpec(name="test", options={})
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError, match=r"Unknown option '--verbose'"):
            _ = parser.parse(["--verbose"])

    def test_unknown_short_option_first_character(self):
        spec = CommandSpec(name="test", options={})
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError, match=r"Unknown option '-x'"):
            _ = parser.parse(["-x"])

    def test_unknown_short_option_middle_character(self):
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
    def test_unknown_subcommand_with_no_positionals(self):
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
    def test_multiple_insufficient_value_errors(self):
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
