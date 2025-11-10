"""Tests for parser configuration flags.

This module comprehensively tests all 12 parser configuration flags:
1. allow_abbreviated_options
2. allow_abbreviated_subcommands
3. allow_equals_for_flags
4. allow_aliases
5. case_insensitive_flags
6. case_insensitive_options
7. case_insensitive_subcommands
8. convert_underscores_to_dashes
9. minimum_abbreviation_length
10. strict_options_before_positionals
11. truthy_flag_values
12. falsey_flag_values

Both individual flag behavior and flag interactions are tested.
"""

import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
    PositionalSpec,
)
from aclaf.parser.exceptions import (
    AmbiguousOptionError,
    AmbiguousSubcommandError,
    FlagWithValueError,
    InvalidFlagValueError,
    UnexpectedPositionalArgumentError,
    UnknownOptionError,
    UnknownSubcommandError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
)


class TestAllowAbbreviatedOptions:
    """Test the allow_abbreviated_options configuration flag."""

    def test_abbreviated_options_disabled_by_default(self):
        """Options cannot be abbreviated when flag is disabled (default)."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", arity=ZERO_ARITY),
                "version": OptionSpec("version", arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec, allow_abbreviated_options=False)

        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(["--verb"])

        assert "verb" in str(exc_info.value).lower()

    def test_abbreviated_options_enabled(self):
        """Options can be abbreviated when flag is enabled."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", arity=ZERO_ARITY),
                "version": OptionSpec("version", arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        result = parser.parse(["--verb"])
        assert "verbose" in result.options
        assert result.options["verbose"].value is True

    def test_abbreviated_options_unambiguous_match(self):
        """Abbreviations work when there's no ambiguity."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", arity=ZERO_ARITY),
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                ),
            },
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        result = parser.parse(["--ver", "--out", "file.txt"])
        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"

    def test_abbreviated_options_ambiguous_match(self):
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

        assert "ver" in str(exc_info.value).lower()
        assert "verbose" in str(exc_info.value).lower()
        assert "version" in str(exc_info.value).lower()

    def test_abbreviated_short_options_not_supported(self):
        """Short options cannot be abbreviated (single char only)."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        # -v works
        result = parser.parse(["-v"])
        assert result.options["verbose"].value is True

        # But abbreviating would be nonsensical for single chars
        # (This is just demonstrating the expected behavior)


class TestAllowAbbreviatedSubcommands:
    """Test the allow_abbreviated_subcommands configuration flag."""

    def test_abbreviated_subcommands_disabled_by_default(self):
        """Subcommands cannot be abbreviated when flag is disabled (default)."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "stop": CommandSpec(name="stop"),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=False)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parser.parse(["sta"])

        assert "sta" in str(exc_info.value).lower()

    def test_abbreviated_subcommands_enabled(self):
        """Subcommands can be abbreviated when flag is enabled."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "stop": CommandSpec(name="stop"),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        result = parser.parse(["star"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_abbreviated_subcommands_unambiguous(self):
        """Abbreviations work when there's no ambiguity."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "remove": CommandSpec(name="remove"),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        result1 = parser.parse(["sta"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "start"

        result2 = parser.parse(["rem"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "remove"

    def test_abbreviated_subcommands_ambiguous(self):
        """Ambiguous abbreviations raise AmbiguousSubcommandError."""
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
        assert "start" in message or "status" in message


class TestAllowEqualsForFlags:
    """Test the allow_equals_for_flags configuration flag."""

    def test_equals_for_flags_disabled_by_default(self):
        """Flag options reject --flag=value syntax when disabled (default)."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        with pytest.raises(FlagWithValueError) as exc_info:
            _ = parser.parse(["--verbose=true"])

        assert "verbose" in str(exc_info.value).lower()

    def test_equals_for_flags_enabled_truthy(self):
        """Flag options accept --flag=true syntax when enabled."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["--verbose=true"])
        assert result.options["verbose"].value is True

    def test_equals_for_flags_enabled_falsey(self):
        """Flag options accept --flag=false syntax when enabled."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["--verbose=false"])
        assert result.options["verbose"].value is False

    def test_equals_for_flags_invalid_value(self):
        """Invalid flag values raise InvalidFlagValueError."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        with pytest.raises(InvalidFlagValueError) as exc_info:
            _ = parser.parse(["--verbose=maybe"])

        assert "verbose" in str(exc_info.value).lower()
        assert "maybe" in str(exc_info.value).lower()


class TestAllowAliases:
    """Test the allow_aliases configuration flag."""

    def test_aliases_enabled_by_default(self):
        """Aliases work when flag is enabled (default)."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(spec, allow_aliases=True)

        result = parser.parse(["rm"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remove"
        assert result.subcommand.alias == "rm"

    def test_aliases_disabled(self):
        """Aliases are ignored when flag is disabled."""
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(spec, allow_aliases=False)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parser.parse(["rm"])

        assert "rm" in str(exc_info.value).lower()

    def test_aliases_primary_name_still_works(self):
        """Primary name works even when aliases are disabled."""
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
        assert result.subcommand.alias is None


class TestCaseInsensitiveFlags:
    """Test the case_insensitive_flags configuration flag."""

    def test_case_sensitive_flags_by_default(self):
        """Flags are case-sensitive when flag is disabled (default)."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec, case_insensitive_flags=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["-V"])  # Capital V not recognized

    def test_case_insensitive_flags_enabled(self):
        """Flags match case-insensitively when flag is enabled."""
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


class TestCaseInsensitiveOptions:
    """Test the case_insensitive_options configuration flag."""

    def test_case_sensitive_options_by_default(self):
        """Options are case-sensitive when flag is disabled (default)."""
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--OUTPUT", "file.txt"])

    def test_case_insensitive_options_enabled(self):
        """Options match case-insensitively when flag is enabled."""
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=True)

        result = parser.parse(["--OUTPUT", "file.txt"])
        assert result.options["output"].value == "file.txt"

    def test_case_insensitive_options_mixed_case(self):
        """Options match with any case combination."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=True)

        result1 = parser.parse(["--Verbose"])
        assert result1.options["verbose"].value is True

        result2 = parser.parse(["--VERBOSE"])
        assert result2.options["verbose"].value is True

        result3 = parser.parse(["--VeRbOsE"])
        assert result3.options["verbose"].value is True


class TestCaseInsensitiveSubcommands:
    """Test the case_insensitive_subcommands configuration flag."""

    def test_case_sensitive_subcommands_by_default(self):
        """Subcommands are case-sensitive when flag is disabled (default)."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=False)

        with pytest.raises(UnknownSubcommandError):
            _ = parser.parse(["START"])

    def test_case_insensitive_subcommands_enabled(self):
        """Subcommands match case-insensitively when flag is enabled."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=True)

        result = parser.parse(["START"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_case_insensitive_subcommands_mixed_case(self):
        """Subcommands match with any case combination."""
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=True)

        result1 = parser.parse(["Start"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "start"

        result2 = parser.parse(["StArT"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "start"


class TestConvertUnderscoresToDashes:
    """Test the convert_underscores_to_dashes configuration flag."""

    def test_underscores_not_converted_by_default(self):
        """Underscores are not converted when flag is disabled (default)."""
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--my_option", "value"])

    def test_underscores_converted_to_dashes(self):
        """Underscores convert to dashes when flag is enabled."""
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option", "value"])
        assert result.options["my-option"].value == "value"

    def test_underscores_and_dashes_both_work(self):
        """Both underscores and dashes match when conversion is enabled."""
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result1 = parser.parse(["--my-option", "val1"])
        assert result1.options["my-option"].value == "val1"

        result2 = parser.parse(["--my_option", "val2"])
        assert result2.options["my-option"].value == "val2"

    def test_multiple_underscores_converted(self):
        """Multiple underscores are all converted."""
        spec = CommandSpec(
            name="cmd",
            options={
                "my-long-option-name": OptionSpec(
                    "my-long-option-name", arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_long_option_name", "value"])
        assert result.options["my-long-option-name"].value == "value"


class TestMinimumAbbreviationLength:
    """Test the minimum_abbreviation_length configuration flag."""

    def test_minimum_abbreviation_length_default_three(self):
        """Default minimum abbreviation length is 3."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        # 3 chars works
        result = parser.parse(["--ver"])
        assert result.options["verbose"].value is True

    def test_minimum_abbreviation_length_too_short(self):
        """Abbreviations shorter than minimum are rejected."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_abbreviated_options=True,
            minimum_abbreviation_length=3,
        )

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--ve"])  # Only 2 chars

    def test_minimum_abbreviation_length_custom(self):
        """Custom minimum abbreviation length is respected."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_abbreviated_options=True,
            minimum_abbreviation_length=5,
        )

        # 5 chars works
        result = parser.parse(["--verbo"])
        assert result.options["verbose"].value is True

        # 4 chars fails
        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--verb"])

    def test_minimum_abbreviation_length_one(self):
        """Minimum abbreviation length can be set to 1."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_abbreviated_options=True,
            minimum_abbreviation_length=1,
        )

        result = parser.parse(["--v"])
        assert result.options["verbose"].value is True


class TestStrictOptionsBeforePositionals:
    """Test the strict_options_before_positionals configuration flag."""

    def test_gnu_style_by_default(self):
        """Options can appear anywhere when flag is disabled (default GNU style)."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=False)

        # Option after positional works
        result = parser.parse(["file.txt", "-v"])
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"

    def test_posix_style_strict_ordering(self):
        """Options must come before positionals when flag is enabled (POSIX style)."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=True)

        # Option before positional works
        result1 = parser.parse(["-v", "file.txt"])
        assert result1.options["verbose"].value is True
        assert result1.positionals["file"].value == "file.txt"

        # Option after positional is treated as another positional
        # This should raise an error for unexpected positional
        with pytest.raises(UnexpectedPositionalArgumentError):
            _ = parser.parse(["file.txt", "-v"])


class TestTruthyFalseyFlagValues:
    """Test the truthy_flag_values and falsey_flag_values configuration flags."""

    def test_custom_truthy_values(self):
        """Custom truthy values are recognized."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            truthy_flag_values=("yes", "y", "1", "true"),
        )

        result1 = parser.parse(["--verbose=yes"])
        assert result1.options["verbose"].value is True

        result2 = parser.parse(["--verbose=y"])
        assert result2.options["verbose"].value is True

        result3 = parser.parse(["--verbose=1"])
        assert result3.options["verbose"].value is True

    def test_custom_falsey_values(self):
        """Custom falsey values are recognized."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            falsey_flag_values=("no", "n", "0", "false"),
        )

        result1 = parser.parse(["--verbose=no"])
        assert result1.options["verbose"].value is False

        result2 = parser.parse(["--verbose=n"])
        assert result2.options["verbose"].value is False

        result3 = parser.parse(["--verbose=0"])
        assert result3.options["verbose"].value is False

    def test_custom_values_reject_others(self):
        """Values not in custom truthy/falsey lists are rejected."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            truthy_flag_values=("yes",),
            falsey_flag_values=("no",),
        )

        # "true" not in custom truthy list
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(["--verbose=true"])


class TestConfigurationFlagInteractions:
    """Test interactions between multiple configuration flags."""

    def test_abbreviation_with_case_insensitive(self):
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

    def test_aliases_with_case_insensitive(self):
        """Aliases work with case-insensitive matching."""
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

    def test_underscores_with_case_insensitive(self):
        """Underscore conversion works with case-insensitive matching."""
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(
            spec,
            convert_underscores_to_dashes=True,
            case_insensitive_options=True,
        )

        result = parser.parse(["--MY_OPTION", "value"])
        assert result.options["my-option"].value == "value"

    def test_abbreviation_with_underscores(self):
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

    def test_all_case_flags_together(self):
        """All case-insensitive flags can work together."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                ),
            },
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(
            spec,
            case_insensitive_flags=True,
            case_insensitive_options=True,
            case_insensitive_subcommands=True,
        )

        result = parser.parse(["-V", "--OUTPUT", "file.txt", "START"])
        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_strict_posix_with_abbreviated_options(self):
        """POSIX strict mode works with abbreviated options."""
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(
            spec,
            strict_options_before_positionals=True,
            allow_abbreviated_options=True,
        )

        result = parser.parse(["--ver", "file.txt"])
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"
