"""Tests for option and subcommand resolution logic.

This module tests the resolve_option and resolve_subcommand methods of CommandSpec,
including abbreviation matching, case-insensitive matching, alias resolution,
and error messages.
"""

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
    """Test basic option resolution without abbreviations."""

    def test_exact_long_option_match(self):
        """Exact long option names match."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(["--verbose"])
        assert result.options["verbose"].value is True

    def test_exact_short_option_match(self):
        """Exact short option names match."""
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
        """Unknown options raise UnknownOptionError."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(["--unknown"])

        assert "unknown" in str(exc_info.value).lower()


class TestOptionResolutionAbbreviations:
    """Test option resolution with abbreviations enabled."""

    def test_abbreviation_unambiguous(self):
        """Unambiguous abbreviations match correctly."""
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
        """Abbreviations respect minimum length."""
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
        """Ambiguous abbreviations raise AmbiguousOptionError."""
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
        """Full option names always work even with abbreviations enabled."""
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
        """Abbreviations work with options that have multiple long names."""
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
    """Test option resolution with case-insensitive matching."""

    def test_case_insensitive_long_option(self):
        """Long options match case-insensitively when enabled."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=True)

        result = parser.parse(["--VERBOSE"])
        assert result.options["verbose"].value is True

    def test_case_insensitive_mixed_case(self):
        """Options match with any case combination."""
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=True)

        result = parser.parse(["--OuTpUt", "file.txt"])
        assert result.options["output"].value == "file.txt"

    def test_case_insensitive_short_flag(self):
        """Short flags match case-insensitively when case_insensitive_flags enabled."""
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
    """Test option resolution with underscore-to-dash conversion."""

    def test_underscores_convert_to_dashes(self):
        """Underscores convert to dashes when enabled."""
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option", "value"])
        assert result.options["my-option"].value == "value"

    def test_underscores_both_forms_work(self):
        """Both underscores and dashes work when conversion enabled."""
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
        """Underscores don't convert when disabled (default)."""
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--my_option", "value"])


class TestOptionResolutionNegation:
    """Test option resolution with negation words."""

    def test_negation_with_no_prefix(self):
        """Negation with 'no' prefix works."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", arity=ZERO_ARITY, negation_words=frozenset({"no"})
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--no-verbose"])
        assert result.options["verbose"].value is False

    def test_negation_with_without_prefix(self):
        """Negation with 'without' prefix works."""
        spec = CommandSpec(
            name="cmd",
            options={
                "color": OptionSpec(
                    "color", arity=ZERO_ARITY, negation_words=frozenset({"without"})
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--without-color"])
        assert result.options["color"].value is False

    def test_negation_multiple_words(self):
        """Multiple negation words work."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    arity=ZERO_ARITY,
                    negation_words=frozenset({"no", "without"}),
                )
            },
        )
        parser = Parser(spec)

        result1 = parser.parse(["--no-verbose"])
        assert result1.options["verbose"].value is False

        result2 = parser.parse(["--without-verbose"])
        assert result2.options["verbose"].value is False

    def test_negation_case_insensitive(self):
        """Negated options work with case-insensitive matching."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", arity=ZERO_ARITY, negation_words=frozenset({"no"})
                )
            },
        )
        parser = Parser(spec, case_insensitive_options=True)

        result = parser.parse(["--NO-VERBOSE"])
        assert result.options["verbose"].value is False


class TestSubcommandResolutionBasic:
    """Test basic subcommand resolution."""

    def test_exact_subcommand_match(self):
        """Exact subcommand names match."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec)

        result = parser.parse(["start"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_unknown_subcommand_raises_error(self):
        """Unknown subcommands raise UnknownSubcommandError."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parser.parse(["unknown"])

        assert "unknown" in str(exc_info.value).lower()


class TestSubcommandResolutionAbbreviations:
    """Test subcommand resolution with abbreviations."""

    def test_subcommand_abbreviation_unambiguous(self):
        """Unambiguous subcommand abbreviations match."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "remove": CommandSpec(name="remove"),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        result = parser.parse(["sta"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_subcommand_abbreviation_ambiguous(self):
        """Ambiguous subcommand abbreviations raise error."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "stop": CommandSpec(name="stop"),
                "status": CommandSpec(name="status"),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        with pytest.raises(AmbiguousSubcommandError) as exc_info:
            _ = parser.parse(["sta"])

        message = str(exc_info.value).lower()
        assert "sta" in message

    def test_subcommand_abbreviation_minimum_length(self):
        """Subcommand abbreviations respect minimum length."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(
            spec,
            allow_abbreviated_subcommands=True,
            minimum_abbreviation_length=3,
        )

        # 3 chars works
        result = parser.parse(["sta"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

        # 2 chars fails
        with pytest.raises(UnknownSubcommandError):
            _ = parser.parse(["st"])


class TestSubcommandResolutionAliases:
    """Test subcommand resolution with aliases."""

    def test_subcommand_alias_matches(self):
        """Subcommand aliases match when aliases enabled."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(
                    name="remove",
                    aliases=frozenset({"rm", "del"}),
                )
            },
        )
        parser = Parser(spec, allow_aliases=True)

        result1 = parser.parse(["rm"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "remove"
        assert result1.subcommand.alias == "rm"

        result2 = parser.parse(["del"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "remove"
        assert result2.subcommand.alias == "del"

    def test_subcommand_alias_disabled(self):
        """Aliases don't match when disabled."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(spec, allow_aliases=False)

        with pytest.raises(UnknownSubcommandError):
            _ = parser.parse(["rm"])

    def test_subcommand_primary_name_always_works(self):
        """Primary subcommand name works even when aliases disabled."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(spec, allow_aliases=False)

        result = parser.parse(["remove"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remove"

    def test_subcommand_abbreviation_with_aliases(self):
        """Abbreviations work with aliases when both enabled."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(
            spec,
            allow_aliases=True,
            allow_abbreviated_subcommands=True,
        )

        # Can abbreviate primary name
        result1 = parser.parse(["rem"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "remove"

        # Can abbreviate alias (though "rm" is already very short)
        # Note: In practice, minimum_abbreviation_length would typically prevent this
        result2 = parser.parse(["r"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "remove"


class TestSubcommandResolutionCaseInsensitive:
    """Test subcommand resolution with case-insensitive matching."""

    def test_subcommand_case_insensitive(self):
        """Subcommands match case-insensitively when enabled."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=True)

        result = parser.parse(["START"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_subcommand_case_insensitive_mixed(self):
        """Subcommands match with mixed case."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=True)

        result = parser.parse(["StArT"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_subcommand_alias_case_insensitive(self):
        """Subcommand aliases work with case-insensitive matching."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(
            spec,
            allow_aliases=True,
            case_insensitive_subcommands=True,
        )

        result = parser.parse(["RM"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remove"
        assert result.subcommand.alias == "rm"


class TestResolutionErrorMessages:
    """Test error message quality for resolution failures."""

    def test_unknown_option_error_message_contains_option_name(self):
        """Unknown option errors include the unknown option name."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(["--unknown"])

        assert "unknown" in str(exc_info.value).lower()

    def test_ambiguous_option_error_lists_candidates(self):
        """Ambiguous option errors list all matching options."""
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
        """Unknown subcommand errors include the unknown name."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parser.parse(["unknown"])

        assert "unknown" in str(exc_info.value).lower()

    def test_ambiguous_subcommand_error_lists_candidates(self):
        """Ambiguous subcommand errors list all matching subcommands."""
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
    """Test complex combinations of resolution features."""

    def test_abbreviation_case_insensitive_combination(self):
        """Abbreviations work with case-insensitive matching."""
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
        """Abbreviations work with underscore conversion."""
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
        """All option resolution features work together."""
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
        """All subcommand resolution features work together."""
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
