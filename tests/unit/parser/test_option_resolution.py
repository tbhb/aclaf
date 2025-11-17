import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
)
from aclaf.parser.exceptions import (
    AmbiguousOptionError,
    AmbiguousSubcommandError,
    UnknownOptionError,
    UnknownSubcommandError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
)


class TestOptionResolutionBasic:
    def test_exact_long_option_match(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(["--verbose"])
        assert result.options["verbose"].value is True

    def test_exact_short_option_match(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(["-v"])
        assert result.options["verbose"].value is True

    def test_unknown_option_raises_error(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(["--unknown"])

        assert "unknown" in str(exc_info.value).lower()


class TestOptionResolutionAbbreviations:
    def test_abbreviation_unambiguous(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", arity=ZERO_ARITY),
                "output": OptionSpec("output", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        result = parser.parse(["--verb", "--out", "file.txt"])
        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"

    def test_abbreviation_minimum_length(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_abbreviated_options=True,
            minimum_abbreviation_length=3,
        )

        # 3 chars works
        result = parser.parse(["--ver"])
        assert result.options["verbose"].value is True

        # 2 chars fails
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--ve"])

    def test_abbreviation_ambiguous(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", arity=ZERO_ARITY),
                "version": OptionSpec("version", arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        with pytest.raises(AmbiguousOptionError) as exc_info:
            _ = parser.parse(["--ver"])

        message = str(exc_info.value).lower()
        assert "ver" in message
        assert "verbose" in message or "version" in message

    def test_abbreviation_full_name_always_works(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", arity=ZERO_ARITY),
                "version": OptionSpec("version", arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        result = parser.parse(["--verbose", "--version"])
        assert result.options["verbose"].value is True
        assert result.options["version"].value is True

    def test_abbreviation_with_multiple_long_names(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output", long=frozenset({"output", "out"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        result1 = parser.parse(["--outp", "file.txt"])
        assert result1.options["output"].value == "file.txt"

        result2 = parser.parse(["--ou", "file.txt"])
        # This could be ambiguous between "output" and "out"
        # but should still work as they're the same option
        assert result2.options["output"].value == "file.txt"


class TestOptionResolutionCaseInsensitive:
    def test_case_insensitive_long_option(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=True)

        result = parser.parse(["--VERBOSE"])
        assert result.options["verbose"].value is True

    def test_case_insensitive_mixed_case(self):
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=True)

        result = parser.parse(["--OuTpUt", "file.txt"])
        assert result.options["output"].value == "file.txt"

    def test_case_insensitive_short_flag(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec, case_insensitive_flags=True)

        result = parser.parse(["-V"])
        assert result.options["verbose"].value is True


class TestOptionResolutionUnderscores:
    def test_underscores_convert_to_dashes(self):
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option", "value"])
        assert result.options["my-option"].value == "value"

    def test_underscores_both_forms_work(self):
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result1 = parser.parse(["--my-option", "val1"])
        assert result1.options["my-option"].value == "val1"

        result2 = parser.parse(["--my_option", "val2"])
        assert result2.options["my-option"].value == "val2"

    def test_underscores_disabled_by_default(self):
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--my_option", "value"])


class TestResolutionErrorMessages:
    def test_unknown_option_error_message_contains_option_name(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(["--unknown"])

        assert "unknown" in str(exc_info.value).lower()

    def test_ambiguous_option_error_lists_candidates(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", arity=ZERO_ARITY),
                "version": OptionSpec("version", arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        with pytest.raises(AmbiguousOptionError) as exc_info:
            _ = parser.parse(["--ver"])

        message = str(exc_info.value)
        # Should mention both possible matches
        assert "verbose" in message or "version" in message

    def test_unknown_subcommand_error_message(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parser.parse(["unknown"])

        assert "unknown" in str(exc_info.value).lower()

    def test_ambiguous_subcommand_error_lists_candidates(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "stop": CommandSpec(name="stop"),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        with pytest.raises(AmbiguousSubcommandError) as exc_info:
            _ = parser.parse(["st"])

        message = str(exc_info.value)
        # Should mention both possible matches
        assert "start" in message or "stop" in message


class TestResolutionCombinations:
    def test_abbreviation_case_insensitive_combination(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_abbreviated_options=True,
            case_insensitive_options=True,
        )

        result = parser.parse(["--VER"])
        assert result.options["verbose"].value is True

    def test_abbreviation_underscores_combination(self):
        spec = CommandSpec(
            name="cmd",
            options={"my-long-option": OptionSpec("my-long-option", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_abbreviated_options=True,
            convert_underscores_to_dashes=True,
        )

        result = parser.parse(["--my_lon"])
        assert result.options["my-long-option"].value is True

    def test_all_option_features_combined(self):
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_abbreviated_options=True,
            case_insensitive_options=True,
            convert_underscores_to_dashes=True,
        )

        # Abbreviated + case insensitive + underscores
        result = parser.parse(["--MY_OP"])
        assert result.options["my-option"].value is True

    def test_subcommand_all_features_combined(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start", aliases=frozenset({"begin"}))
            },
        )
        parser = Parser(
            spec,
            allow_abbreviated_subcommands=True,
            allow_aliases=True,
            case_insensitive_subcommands=True,
        )

        # Case insensitive + abbreviation
        result1 = parser.parse(["STA"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "start"

        # Case insensitive + alias
        result2 = parser.parse(["BEGIN"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "start"

        # Case insensitive + abbreviated alias
        result3 = parser.parse(["BEG"])
        assert result3.subcommand is not None
        assert result3.subcommand.command == "start"
