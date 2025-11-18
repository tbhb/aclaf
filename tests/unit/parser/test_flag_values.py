import pytest
from hypothesis import given, strategies as st

from aclaf.parser import (
    ZERO_ARITY,
    AccumulationMode,
    CommandSpec,
    OptionSpec,
    Parser,
    ParseResult,
)
from aclaf.parser._constants import DEFAULT_FALSEY_VALUES, DEFAULT_TRUTHY_VALUES
from aclaf.parser._exceptions import (
    FlagWithValueError,
    InvalidFlagValueError,
    ParserConfigurationError,
)


class TestConstValueFlags:
    def test_flag_with_const_value(self):
        args = ["--mode"]
        spec = CommandSpec(
            name="cmd",
            options={
                "mode": OptionSpec("mode", is_flag=True, const_value="production")
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["mode"].value == "production"

    def test_flag_without_const_value_uses_true(self):
        args = ["--verbose"]
        spec = CommandSpec(
            name="cmd", options={"verbose": OptionSpec("verbose", is_flag=True)}
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_const_value_with_accumulation_mode(self):
        args = ["--mode", "--mode", "--mode"]
        spec = CommandSpec(
            name="cmd",
            options={
                "mode": OptionSpec(
                    "mode",
                    is_flag=True,
                    const_value="enabled",
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["mode"].value == ("enabled", "enabled", "enabled")

    def test_flag_with_const_value_in_short_cluster(self):
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                    const_value="enabled",
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["-v"])

        assert result.options["verbose"].value == "enabled"

    def test_flag_without_const_value_in_short_cluster(self):
        spec = CommandSpec(
            name="test",
            options={
                "verbose": OptionSpec(
                    name="verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                    const_value=None,
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["-v"])

        assert result.options["verbose"].value is True

    def test_zero_arity_with_const_value_in_short_cluster(self):
        spec = CommandSpec(
            name="test",
            options={
                "quiet": OptionSpec(
                    name="quiet",
                    short=frozenset({"q"}),
                    is_flag=False,
                    arity=ZERO_ARITY,
                    const_value="silent",
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["-q"])

        assert result.options["quiet"].value == "silent"

    def test_zero_arity_without_const_value_in_short_cluster(self):
        spec = CommandSpec(
            name="test",
            options={
                "quiet": OptionSpec(
                    name="quiet",
                    short=frozenset({"q"}),
                    is_flag=False,
                    arity=ZERO_ARITY,
                    const_value=None,
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["-q"])

        assert result.options["quiet"].value is True


class TestAllowEqualsForFlags:
    def test_equals_for_flags_disabled_by_default(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_equals_for_flags=False)

        with pytest.raises(FlagWithValueError) as exc_info:
            _ = parser.parse(["--verbose=true"])

        assert "verbose" in str(exc_info.value).lower()

    def test_equals_for_flags_enabled_truthy(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["--verbose=true"])
        assert result.options["verbose"].value is True

    def test_equals_for_flags_enabled_falsey(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["--verbose=false"])
        assert result.options["verbose"].value is False

    def test_equals_for_flags_invalid_value(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        with pytest.raises(InvalidFlagValueError) as exc_info:
            _ = parser.parse(["--verbose=maybe"])

        assert "verbose" in str(exc_info.value).lower()
        assert "maybe" in str(exc_info.value).lower()


class TestShortOptionWithoutEqualsFlagValue:
    def test_flag_values_disabled_ignores_next_arg(self):
        args = ["-v", "false"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_flag_values_disabled_attached_value_raises_error(self):
        args = ["-vfalse"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    def test_flag_values_enabled_consumes_next_arg(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        for value in DEFAULT_FALSEY_VALUES:
            result = parser.parse(["-v", value])
            assert result.options["verbose"].value is False

        for value in DEFAULT_TRUTHY_VALUES:
            result = parser.parse(["-v", value])
            assert result.options["verbose"].value is True

    def test_flag_values_enabled_parses_attached_value(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        for value in DEFAULT_FALSEY_VALUES:
            result = parser.parse([f"-v{value}"])
            assert result.options["verbose"].value is False

        for value in DEFAULT_TRUTHY_VALUES:
            result = parser.parse([f"-v{value}"])
            assert result.options["verbose"].value is True

    def test_custom_option_flag_values_from_next_arg(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                    falsey_flag_values=frozenset({"foo"}),
                    truthy_flag_values=frozenset({"bar"}),
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["-v", "foo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-v", "bar"])
        assert result.options["verbose"].value is True

    def test_custom_option_flag_values_attached(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    is_flag=True,
                    falsey_flag_values=frozenset({"foo"}),
                    truthy_flag_values=frozenset({"bar"}),
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["-vfoo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-vbar"])
        assert result.options["verbose"].value is True

    def test_custom_parser_flag_values_from_next_arg(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            falsey_flag_values=("foo",),
            truthy_flag_values=("bar",),
        )

        result = parser.parse(["-v", "foo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-v", "bar"])
        assert result.options["verbose"].value is True

    def test_custom_parser_flag_values_attached(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            falsey_flag_values=("foo",),
            truthy_flag_values=("bar",),
        )

        result = parser.parse(["-vfoo"])
        assert result.options["verbose"].value is False

        result = parser.parse(["-vbar"])
        assert result.options["verbose"].value is True

    def test_invalid_value_next_arg_not_consumed(self):
        args = ["-v", "invalid"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_invalid_value_attached_raises_error(self):
        args = ["-vinvalid"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)


class TestOptionSpecFlagValueValidation:
    def test_truthy_empty_frozenset_raises_error(self):
        with pytest.raises(
            ValueError,
            match=r"truthy_flag_values must not be empty.*at least one",
        ):
            _ = OptionSpec("verbose", truthy_flag_values=frozenset())

    def test_falsey_empty_frozenset_raises_error(self):
        with pytest.raises(
            ValueError,
            match=r"falsey_flag_values must not be empty.*at least one",
        ):
            _ = OptionSpec("verbose", falsey_flag_values=frozenset())

    def test_truthy_empty_string_raises_error(self):
        with pytest.raises(
            ValueError,
            match=r"truthy_flag_values must contain only non-empty strings.*index 0",
        ):
            _ = OptionSpec("verbose", truthy_flag_values=frozenset({""}))

    def test_falsey_empty_string_raises_error(self):
        with pytest.raises(
            ValueError,
            match=r"falsey_flag_values must contain only non-empty strings.*index 0",
        ):
            _ = OptionSpec("verbose", falsey_flag_values=frozenset({""}))

    def test_truthy_empty_string_among_valid_raises_error(self):
        with pytest.raises(
            ValueError,
            match=r"truthy_flag_values must contain only non-empty strings.*index \d+",
        ):
            _ = OptionSpec("verbose", truthy_flag_values=frozenset({"yes", ""}))

    def test_falsey_empty_string_among_valid_raises_error(self):
        with pytest.raises(
            ValueError,
            match=r"falsey_flag_values must contain only non-empty strings.*index \d+",
        ):
            _ = OptionSpec("verbose", falsey_flag_values=frozenset({"no", ""}))

    def test_truthy_none_value_accepted(self):
        opt = OptionSpec("verbose", truthy_flag_values=None)
        assert opt.truthy_flag_values is None

    def test_falsey_none_value_accepted(self):
        opt = OptionSpec("verbose", falsey_flag_values=None)
        assert opt.falsey_flag_values is None

    def test_both_valid_values_accepted(self):
        opt = OptionSpec(
            "verbose",
            truthy_flag_values=frozenset({"yes", "y", "true"}),
            falsey_flag_values=frozenset({"no", "n", "false"}),
        )
        assert opt.truthy_flag_values == frozenset({"yes", "y", "true"})
        assert opt.falsey_flag_values == frozenset({"no", "n", "false"})


class TestTruthyFalseyFlagValues:
    def test_custom_truthy_values(self):
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


class TestParserConfigurationFlagValueValidation:
    def test_truthy_none_uses_defaults(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=None)
        assert parser.config.truthy_flag_values is None

    def test_falsey_none_uses_defaults(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=None)
        assert parser.config.falsey_flag_values is None

    def test_truthy_single_value_valid(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("enabled",))
        assert parser.config.truthy_flag_values == ("enabled",)

    def test_falsey_single_value_valid(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("disabled",))
        assert parser.config.falsey_flag_values == ("disabled",)

    def test_truthy_multiple_values_valid(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("true", "yes", "1"))
        assert parser.config.truthy_flag_values == ("true", "yes", "1")

    def test_falsey_multiple_values_valid(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("false", "no", "0"))
        assert parser.config.falsey_flag_values == ("false", "no", "0")

    def test_truthy_empty_tuple_raises_error(self):
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"truthy_flag_values must not be empty",
        ):
            _ = Parser(spec, truthy_flag_values=())

    def test_falsey_empty_tuple_raises_error(self):
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=r"falsey_flag_values must not be empty",
        ):
            _ = Parser(spec, falsey_flag_values=())

    @pytest.mark.parametrize(
        ("param_value", "expected_index"),
        [
            (("", "yes"), 0),
            (("yes", "", "true"), 1),
            (("yes", "true", ""), 2),
        ],
    )
    def test_truthy_empty_string_raises_error(
        self, param_value: tuple[str, ...], expected_index: int
    ):
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=(
                rf"truthy_flag_values must contain only non-empty "
                rf"strings.*index {expected_index}"
            ),
        ):
            _ = Parser(spec, truthy_flag_values=param_value)

    @pytest.mark.parametrize(
        ("param_value", "expected_index"),
        [
            (("", "no"), 0),
            (("no", "", "false"), 1),
            (("no", "false", ""), 2),
        ],
    )
    def test_falsey_empty_string_raises_error(
        self, param_value: tuple[str, ...], expected_index: int
    ):
        spec = CommandSpec(name="cmd")
        with pytest.raises(
            ParserConfigurationError,
            match=(
                rf"falsey_flag_values must contain only non-empty "
                rf"strings.*index {expected_index}"
            ),
        ):
            _ = Parser(spec, falsey_flag_values=param_value)

    def test_truthy_whitespace_only_allowed(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("  ", "yes"))
        assert parser.config.truthy_flag_values == ("  ", "yes")

    def test_falsey_whitespace_only_allowed(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("  ", "no"))
        assert parser.config.falsey_flag_values == ("  ", "no")

    def test_truthy_duplicates_allowed(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("yes", "true", "yes"))
        assert parser.config.truthy_flag_values == ("yes", "true", "yes")

    def test_falsey_duplicates_allowed(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("no", "false", "no"))
        assert parser.config.falsey_flag_values == ("no", "false", "no")

    def test_truthy_case_variants_allowed(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, truthy_flag_values=("true", "TRUE", "True"))
        assert parser.config.truthy_flag_values == ("true", "TRUE", "True")

    def test_falsey_case_variants_allowed(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=("false", "FALSE", "False"))
        assert parser.config.falsey_flag_values == ("false", "FALSE", "False")


class TestConfigurationValidationFlagValuesOverlap:
    def test_no_overlap_both_specified(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=("true", "yes", "1"),
            falsey_flag_values=("false", "no", "0"),
        )
        assert parser.config.truthy_flag_values == ("true", "yes", "1")
        assert parser.config.falsey_flag_values == ("false", "no", "0")

    def test_both_none_skips_overlap_check(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=None,
            falsey_flag_values=None,
        )
        assert parser.config.truthy_flag_values is None
        assert parser.config.falsey_flag_values is None

    def test_truthy_none_skips_overlap_check(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=None,
            falsey_flag_values=("custom",),
        )
        assert parser.config.truthy_flag_values is None
        assert parser.config.falsey_flag_values == ("custom",)

    def test_falsey_none_skips_overlap_check(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(
            spec,
            truthy_flag_values=("custom",),
            falsey_flag_values=None,
        )
        assert parser.config.truthy_flag_values == ("custom",)
        assert parser.config.falsey_flag_values is None

    def test_single_overlap_raises_error(self):
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


class TestConfigurationValidationPropertyBased:
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
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, falsey_flag_values=values)
        assert parser.config.falsey_flag_values == values
