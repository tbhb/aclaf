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
from hypothesis import given, strategies as st

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
    ParserConfigurationError,
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

    def test_minimum_abbreviation_length_validation_zero_raises_error(self):
        """Zero minimum abbreviation length raises ParserConfigurationError."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"minimum_abbreviation_length must be at least 1.*got 0",
        ):
            _ = Parser(spec, minimum_abbreviation_length=0)

    def test_minimum_abbreviation_length_validation_negative_raises_error(self):
        """Negative minimum abbreviation length raises ParserConfigurationError."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"minimum_abbreviation_length must be at least 1.*got -1",
        ):
            _ = Parser(spec, minimum_abbreviation_length=-1)

    def test_minimum_abbreviation_length_validation_large_negative_raises_error(self):
        """Large negative abbreviation length raises ParserConfigurationError."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"minimum_abbreviation_length must be at least 1.*got -100",
        ):
            _ = Parser(spec, minimum_abbreviation_length=-100)

    def test_minimum_abbreviation_length_validation_valid_values(self):
        """Valid minimum abbreviation length values are accepted."""
        spec = CommandSpec(name="cmd")

        # Test a range of valid values
        for valid_value in [1, 2, 3, 5, 10, 100]:
            parser = Parser(spec, minimum_abbreviation_length=valid_value)
            # If we get here without exception, validation passed
            assert parser.config.minimum_abbreviation_length == valid_value


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


class TestConfigurationValidationTruthyValues:
    """Test truthy_flag_values configuration validation."""

    def test_truthy_none_uses_defaults(self):
        """None for truthy values uses defaults."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=None)
        assert parser.config.truthy_flag_values is None

    def test_truthy_single_value_valid(self):
        """Single truthy value is valid."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("enabled",))
        assert parser.config.truthy_flag_values == ("enabled",)

    def test_truthy_multiple_values_valid(self):
        """Multiple truthy values are valid."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("true", "yes", "1"))
        assert parser.config.truthy_flag_values == ("true", "yes", "1")

    def test_truthy_empty_tuple_raises_error(self):
        """Empty truthy tuple raises error."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"truthy_flag_values must not be empty",
        ):
            _ = Parser(spec, truthy_flag_values=())

    def test_truthy_empty_string_first_raises_error(self):
        """Empty string at start raises error with correct index."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"truthy_flag_values must contain only non-empty strings.*index 0",
        ):
            _ = Parser(spec, truthy_flag_values=("", "yes"))

    def test_truthy_empty_string_middle_raises_error(self):
        """Empty string in middle raises error with correct index."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"truthy_flag_values must contain only non-empty strings.*index 1",
        ):
            _ = Parser(spec, truthy_flag_values=("yes", "", "true"))

    def test_truthy_empty_string_last_raises_error(self):
        """Empty string at end raises error with correct index."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"truthy_flag_values must contain only non-empty strings.*index 2",
        ):
            _ = Parser(spec, truthy_flag_values=("yes", "true", ""))

    def test_truthy_whitespace_only_allowed(self):
        """Whitespace-only string is allowed (edge case)."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("  ", "yes"))
        assert parser.config.truthy_flag_values == ("  ", "yes")

    def test_truthy_duplicates_allowed(self):
        """Duplicate values are allowed (harmless)."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("yes", "true", "yes"))
        assert parser.config.truthy_flag_values == ("yes", "true", "yes")

    def test_truthy_case_variants_allowed(self):
        """Multiple case variants are allowed."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("true", "TRUE", "True"))
        assert parser.config.truthy_flag_values == ("true", "TRUE", "True")


class TestConfigurationValidationFalseyValues:
    """Test falsey_flag_values configuration validation."""

    def test_falsey_none_uses_defaults(self):
        """None for falsey values uses defaults."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=None)
        assert parser.config.falsey_flag_values is None

    def test_falsey_single_value_valid(self):
        """Single falsey value is valid."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("disabled",))
        assert parser.config.falsey_flag_values == ("disabled",)

    def test_falsey_multiple_values_valid(self):
        """Multiple falsey values are valid."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("false", "no", "0"))
        assert parser.config.falsey_flag_values == ("false", "no", "0")

    def test_falsey_empty_tuple_raises_error(self):
        """Empty falsey tuple raises error."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"falsey_flag_values must not be empty",
        ):
            _ = Parser(spec, falsey_flag_values=())

    def test_falsey_empty_string_first_raises_error(self):
        """Empty string at start raises error with correct index."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"falsey_flag_values must contain only non-empty strings.*index 0",
        ):
            _ = Parser(spec, falsey_flag_values=("", "no"))

    def test_falsey_empty_string_middle_raises_error(self):
        """Empty string in middle raises error with correct index."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"falsey_flag_values must contain only non-empty strings.*index 1",
        ):
            _ = Parser(spec, falsey_flag_values=("no", "", "false"))

    def test_falsey_empty_string_last_raises_error(self):
        """Empty string at end raises error with correct index."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"falsey_flag_values must contain only non-empty strings.*index 2",
        ):
            _ = Parser(spec, falsey_flag_values=("no", "false", ""))

    def test_falsey_whitespace_only_allowed(self):
        """Whitespace-only string is allowed (edge case)."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("  ", "no"))
        assert parser.config.falsey_flag_values == ("  ", "no")

    def test_falsey_duplicates_allowed(self):
        """Duplicate values are allowed (harmless)."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("no", "false", "no"))
        assert parser.config.falsey_flag_values == ("no", "false", "no")

    def test_falsey_case_variants_allowed(self):
        """Multiple case variants are allowed."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("false", "FALSE", "False"))
        assert parser.config.falsey_flag_values == ("false", "FALSE", "False")


class TestConfigurationValidationFlagValuesOverlap:
    """Test truthy/falsey overlap validation."""

    def test_no_overlap_both_specified(self):
        """No overlap when both explicitly set."""
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=("true", "yes", "1"),
            falsey_flag_values=("false", "no", "0"),
        )
        assert parser.config.truthy_flag_values == ("true", "yes", "1")
        assert parser.config.falsey_flag_values == ("false", "no", "0")

    def test_both_none_skips_overlap_check(self):
        """Both None skips overlap validation."""
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=None,
            falsey_flag_values=None,
        )
        assert parser.config.truthy_flag_values is None
        assert parser.config.falsey_flag_values is None

    def test_truthy_none_skips_overlap_check(self):
        """Truthy None skips overlap validation."""
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=None,
            falsey_flag_values=("custom",),
        )
        assert parser.config.truthy_flag_values is None
        assert parser.config.falsey_flag_values == ("custom",)

    def test_falsey_none_skips_overlap_check(self):
        """Falsey None skips overlap validation."""
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=("custom",),
            falsey_flag_values=None,
        )
        assert parser.config.truthy_flag_values == ("custom",)
        assert parser.config.falsey_flag_values is None

    def test_single_overlap_raises_error(self):
        """Single overlapping value raises error."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"truthy_flag_values and falsey_flag_values must not overlap.*'yes'",
        ):
            _ = Parser(
                spec,
                truthy_flag_values=("yes", "true"),
                falsey_flag_values=("no", "yes"),
            )

    def test_multiple_overlaps_raise_error(self):
        """Multiple overlapping values raise error with all listed."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=(
                r"truthy_flag_values and falsey_flag_values must not "
                r"overlap.*'1'.*'yes'"
            ),
        ):
            _ = Parser(
                spec,
                truthy_flag_values=("yes", "true", "1"),
                falsey_flag_values=("no", "yes", "1"),
            )

    def test_case_sensitive_no_overlap(self):
        """Different case is not considered overlap."""
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=("YES", "TRUE"),
            falsey_flag_values=("yes", "true"),
        )
        # No error - "YES" != "yes", "TRUE" != "true"
        assert parser.config.truthy_flag_values == ("YES", "TRUE")
        assert parser.config.falsey_flag_values == ("yes", "true")

    def test_exact_duplicate_raises_error(self):
        """Exact string in both sets raises error."""
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"truthy_flag_values and falsey_flag_values must not overlap.*'yes'",
        ):
            _ = Parser(
                spec,
                truthy_flag_values=("yes",),
                falsey_flag_values=("yes",),
            )


class TestConfigurationValidationEdgeCases:
    """Test edge cases in configuration validation."""

    def test_very_large_minimum_abbreviation_length(self):
        """Very large abbreviation length is allowed."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, minimum_abbreviation_length=1000)
        assert parser.config.minimum_abbreviation_length == 1000

    def test_all_boolean_flags_true(self):
        """All boolean flags can be True."""
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            allow_abbreviated_options=True,
            allow_abbreviated_subcommands=True,
            allow_equals_for_flags=True,
            allow_aliases=True,
            allow_negative_numbers=True,
            case_insensitive_flags=True,
            case_insensitive_options=True,
            case_insensitive_subcommands=True,
            convert_underscores_to_dashes=True,
            flatten_option_values=True,
            strict_options_before_positionals=True,
        )
        assert parser.config.allow_abbreviated_options is True
        assert parser.config.allow_abbreviated_subcommands is True
        assert parser.config.allow_equals_for_flags is True
        assert parser.config.allow_aliases is True
        assert parser.config.allow_negative_numbers is True
        assert parser.config.case_insensitive_flags is True
        assert parser.config.case_insensitive_options is True
        assert parser.config.case_insensitive_subcommands is True
        assert parser.config.convert_underscores_to_dashes is True
        assert parser.config.flatten_option_values is True
        assert parser.config.strict_options_before_positionals is True

    def test_all_boolean_flags_false(self):
        """All boolean flags can be False."""
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            allow_abbreviated_options=False,
            allow_abbreviated_subcommands=False,
            allow_equals_for_flags=False,
            allow_aliases=False,
            allow_negative_numbers=False,
            case_insensitive_flags=False,
            case_insensitive_options=False,
            case_insensitive_subcommands=False,
            convert_underscores_to_dashes=False,
            flatten_option_values=False,
            strict_options_before_positionals=False,
        )
        assert parser.config.allow_abbreviated_options is False
        assert parser.config.allow_abbreviated_subcommands is False
        assert parser.config.allow_equals_for_flags is False
        assert parser.config.allow_aliases is False
        assert parser.config.allow_negative_numbers is False
        assert parser.config.case_insensitive_flags is False
        assert parser.config.case_insensitive_options is False
        assert parser.config.case_insensitive_subcommands is False
        assert parser.config.convert_underscores_to_dashes is False
        assert parser.config.flatten_option_values is False
        assert parser.config.strict_options_before_positionals is False

    def test_ignored_configuration_combination(self):
        """Ignored configuration doesn't raise error."""
        spec = CommandSpec(name="cmd")
        # abbreviation_length ignored when abbreviations disabled
        parser = Parser(
            spec,
            allow_abbreviated_options=False,
            minimum_abbreviation_length=10,
        )
        assert parser.config.allow_abbreviated_options is False
        assert parser.config.minimum_abbreviation_length == 10


class TestConfigurationValidationPropertyBased:
    """Property-based tests for configuration validation."""

    @given(
        truthy=st.one_of(
            st.none(),
            st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10).map(
                tuple
            ),
        ),
        falsey=st.one_of(
            st.none(),
            st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10).map(
                tuple
            ),
        ),
    )
    def test_property_no_overlap_if_both_specified(
        self, truthy: tuple[str, ...] | None, falsey: tuple[str, ...] | None
    ) -> None:
        """Property: If both truthy and falsey are specified, they must not overlap."""
        spec = CommandSpec(name="cmd")

        if truthy is not None and falsey is not None:
            truthy_set = set(truthy)
            falsey_set = set(falsey)
            overlap = truthy_set & falsey_set

            if overlap:
                with pytest.raises(ParserConfigurationError):
                    _ = Parser(
                        spec,
                        truthy_flag_values=truthy,
                        falsey_flag_values=falsey,
                    )
            else:
                parser = Parser(
                    spec,
                    truthy_flag_values=truthy,
                    falsey_flag_values=falsey,
                )
                assert parser.config.truthy_flag_values == truthy
                assert parser.config.falsey_flag_values == falsey
        else:
            # At least one is None - should always succeed
            parser = Parser(
                spec,
                truthy_flag_values=truthy,
                falsey_flag_values=falsey,
            )
            assert parser.config.truthy_flag_values == truthy
            assert parser.config.falsey_flag_values == falsey

    @given(
        values=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10).map(
            tuple
        )
    )
    def test_property_truthy_non_empty_strings_always_valid(
        self, values: tuple[str, ...]
    ) -> None:
        """Property: Truthy values with non-empty strings are always valid."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=values)
        assert parser.config.truthy_flag_values == values

    @given(
        values=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10).map(
            tuple
        )
    )
    def test_property_falsey_non_empty_strings_always_valid(
        self, values: tuple[str, ...]
    ) -> None:
        """Property: Falsey values with non-empty strings are always valid."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=values)
        assert parser.config.falsey_flag_values == values

    @given(min_length=st.integers(min_value=1, max_value=1000))
    def test_property_minimum_abbreviation_length_positive_always_valid(
        self, min_length: int
    ) -> None:
        """Property: Any positive minimum abbreviation length is valid."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, minimum_abbreviation_length=min_length)
        assert parser.config.minimum_abbreviation_length == min_length
