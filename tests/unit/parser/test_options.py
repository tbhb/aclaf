import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
    ParseResult,
)
from aclaf.parser._constants import DEFAULT_FALSEY_VALUES, DEFAULT_TRUTHY_VALUES
from aclaf.parser._exceptions import (
    FlagWithValueError,
    InsufficientOptionValuesError,
    InvalidFlagValueError,
    OptionDoesNotAcceptValueError,
)
from aclaf.parser._types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    Arity,
)


class TestOptionEqualsSyntax:
    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--output", "output", frozenset[str]()),
            ("-o", "output", frozenset({"o"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_parses_single_value(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}=file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == "file.txt"

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_consumes_only_equals_value(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}=file.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == ("file.txt",)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_insufficient_single_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}=file1.txt", "file2.txt", "file3.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=Arity(2, None)
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--output", "output", frozenset[str]()),
            ("-o", "output", frozenset({"o"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_empty_string_satisfies_arity(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == ""

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_empty_string_satisfies_one_or_more_arity(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == ("",)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_equals_empty_value_for_flag_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(OptionDoesNotAcceptValueError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_equals_disabled_empty_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_equals_enabled_empty_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}="]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_equals_disabled_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}=true"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=False)
        with pytest.raises(FlagWithValueError):
            _ = parser.parse(args)

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_equals_enabled_parses_truthy_falsey(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        for value in DEFAULT_FALSEY_VALUES:
            result = parser.parse([f"{option_flag}={value}"])
            assert result.options[option_name].value is False

        for value in DEFAULT_TRUTHY_VALUES:
            result = parser.parse([f"{option_flag}={value}"])
            assert result.options[option_name].value is True

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_custom_flag_values_at_option_level(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name,
                    short=option_short,
                    is_flag=True,
                    falsey_flag_values=frozenset({"foo"}),
                    truthy_flag_values=frozenset({"bar"}),
                )
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse([f"{option_flag}=foo"])
        assert result.options[option_name].value is False

        result = parser.parse([f"{option_flag}=bar"])
        assert result.options[option_name].value is True

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_custom_flag_values_at_parser_level(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(
            spec,
            allow_equals_for_flags=True,
            falsey_flag_values=("foo",),
            truthy_flag_values=("bar",),
        )

        result = parser.parse([f"{option_flag}=foo"])
        assert result.options[option_name].value is False

        result = parser.parse([f"{option_flag}=bar"])
        assert result.options[option_name].value is True

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_invalid_flag_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [f"{option_flag}=invalid"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(option_name, short=option_short, is_flag=True)
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(args)

    def test_short_option_arity_min_greater_than_one_with_inline_value(
        self,
    ):
        spec = CommandSpec(
            name="test",
            options={
                "files": OptionSpec(
                    name="files",
                    short=frozenset({"f"}),
                    is_flag=False,
                    arity=Arity(min=2, max=3),
                ),
            },
        )
        parser = Parser(spec=spec)

        with pytest.raises(
            InsufficientOptionValuesError,
            match=r"Insufficient values.*'--files'.*Expected 2-3",
        ):
            _ = parser.parse(["-f=one.txt"])

    def test_short_option_arity_min_one_with_inline_value_succeeds(self):
        spec = CommandSpec(
            name="test",
            options={
                "file": OptionSpec(
                    name="file",
                    short=frozenset({"f"}),
                    is_flag=False,
                    arity=EXACTLY_ONE_ARITY,
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["-f=one.txt"])

        assert result.options["file"].value == "one.txt"

    def test_zero_arity_with_inline_value_raises_error(self):
        spec = CommandSpec(
            name="test",
            options={
                "count": OptionSpec(
                    name="count",
                    short=frozenset({"c"}),
                    is_flag=False,
                    arity=ZERO_ARITY,
                ),
            },
        )
        parser = Parser(spec=spec)

        with pytest.raises(
            OptionDoesNotAcceptValueError,
            match=r"Option '-c'.*does not accept a value",
        ):
            _ = parser.parse(["-c=5"])

    def test_zero_arity_with_const_value_no_inline_succeeds(self):
        spec = CommandSpec(
            name="test",
            options={
                "mode": OptionSpec(
                    name="mode",
                    short=frozenset({"m"}),
                    is_flag=False,
                    arity=ZERO_ARITY,
                    const_value="default",
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["-m"])

        assert result.options["mode"].value == "default"

    def test_zero_arity_without_const_value_no_inline_succeeds(self):
        spec = CommandSpec(
            name="test",
            options={
                "debug": OptionSpec(
                    name="debug",
                    short=frozenset({"d"}),
                    is_flag=False,
                    arity=ZERO_ARITY,
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["-d"])

        assert result.options["debug"].value is True


class TestShortOptionWithoutEqualsValueInArg:
    def test_attached_value_parses(self):
        args = ["-ofile.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == "file.txt"

    def test_attached_value_for_flag_raises_error(self):
        args = ["-vfoo"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(OptionDoesNotAcceptValueError):
            _ = parser.parse(args)


class TestOptionSpaceSyntax:
    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--output", "output", frozenset[str]()),
            ("-o", "output", frozenset({"o"})),
        ],
        ids=["long", "short"],
    )
    def test_space_consumes_next_argument(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [option_flag, "file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == "file.txt"

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--verbose", "verbose", frozenset[str]()),
            ("-v", "verbose", frozenset({"v"})),
        ],
        ids=["long", "short"],
    )
    def test_flag_defaults_to_true(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [option_flag]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value is True

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_space_consumes_all_following_non_option_args(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [option_flag, "file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=Arity(0, None)
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options[option_name].value == ("file1.txt", "file2.txt")

    @pytest.mark.parametrize(
        ("option_flag", "option_name", "option_short"),
        [
            ("--files", "files", frozenset[str]()),
            ("-f", "files", frozenset({"f"})),
        ],
        ids=["long", "short"],
    )
    def test_space_missing_required_value_raises_error(
        self, option_flag: str, option_name: str, option_short: frozenset[str]
    ):
        args = [option_flag]
        spec = CommandSpec(
            name="cmd",
            options={
                option_name: OptionSpec(
                    option_name, short=option_short, arity=ONE_OR_MORE_ARITY
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)


class TestOptionValueEdgeCases:
    def test_multi_value_option_stops_early_insufficient(self):
        args = ["--files", "file1.txt", "--other"]
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=Arity(2, 3),  # Requires at least 2 values
                ),
                "other": OptionSpec("other", is_flag=True),
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.option_spec.name == "files"
