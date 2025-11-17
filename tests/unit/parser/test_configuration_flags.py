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
    def test_abbreviated_options_disabled_by_default(self):
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
    def test_abbreviated_subcommands_disabled_by_default(self):
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


class TestAllowAliases:
    def test_aliases_enabled_by_default(self):
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
    def test_case_sensitive_flags_by_default(self):
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
    def test_case_sensitive_options_by_default(self):
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--OUTPUT", "file.txt"])

    def test_case_insensitive_options_enabled(self):
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, case_insensitive_options=True)

        result = parser.parse(["--OUTPUT", "file.txt"])
        assert result.options["output"].value == "file.txt"

    def test_case_insensitive_options_mixed_case(self):
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
    def test_case_sensitive_subcommands_by_default(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=False)

        with pytest.raises(UnknownSubcommandError):
            _ = parser.parse(["START"])

    def test_case_insensitive_subcommands_enabled(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=True)

        result = parser.parse(["START"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_case_insensitive_subcommands_mixed_case(self):
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
    def test_underscores_not_converted_by_default(self):
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=False)

        with pytest.raises(UnknownOptionError):
            _ = parser.parse(["--my_option", "value"])

    def test_underscores_converted_to_dashes(self):
        spec = CommandSpec(
            name="cmd",
            options={"my-option": OptionSpec("my-option", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        result = parser.parse(["--my_option", "value"])
        assert result.options["my-option"].value == "value"

    def test_underscores_and_dashes_both_work(self):
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
    def test_minimum_abbreviation_length_default_three(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_abbreviated_options=True)

        # 3 chars works
        result = parser.parse(["--ver"])
        assert result.options["verbose"].value is True

    def test_minimum_abbreviation_length_too_short(self):
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
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"minimum_abbreviation_length must be at least 1.*got 0",
        ):
            _ = Parser(spec, minimum_abbreviation_length=0)

    def test_minimum_abbreviation_length_validation_negative_raises_error(self):
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"minimum_abbreviation_length must be at least 1.*got -1",
        ):
            _ = Parser(spec, minimum_abbreviation_length=-1)

    def test_minimum_abbreviation_length_validation_large_negative_raises_error(self):
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"minimum_abbreviation_length must be at least 1.*got -100",
        ):
            _ = Parser(spec, minimum_abbreviation_length=-100)

    def test_minimum_abbreviation_length_validation_valid_values(self):
        spec = CommandSpec(name="cmd")

        # Test a range of valid values
        for valid_value in [1, 2, 3, 5, 10, 100]:
            parser = Parser(spec, minimum_abbreviation_length=valid_value)
            # If we get here without exception, validation passed
            assert parser.config.minimum_abbreviation_length == valid_value


class TestStrictOptionsBeforePositionals:
    def test_gnu_style_by_default(self):
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


class TestConfigurationFlagInteractions:
    def test_abbreviation_with_case_insensitive(self):
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


class TestConfigurationValidationEdgeCases:
    def test_very_large_minimum_abbreviation_length(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, minimum_abbreviation_length=1000)
        assert parser.config.minimum_abbreviation_length == 1000

    def test_all_boolean_flags_true(self):
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
    @given(min_length=st.integers(min_value=1, max_value=1000))
    def test_property_minimum_abbreviation_length_positive_always_valid(
        self, min_length: int
    ) -> None:
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, minimum_abbreviation_length=min_length)
        assert parser.config.minimum_abbreviation_length == min_length
