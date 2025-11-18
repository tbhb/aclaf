import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
    PositionalSpec,
)
from aclaf.parser._exceptions import (
    InsufficientOptionValuesError,
    InvalidFlagValueError,
    UnknownOptionError,
)
from aclaf.parser._types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    AccumulationMode,
)


class TestBasicCombinedFlags:
    def test_two_flags_bundled_together(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "quiet": OptionSpec("quiet", short=frozenset({"q"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vq"])
        assert result.options["verbose"].value is True
        assert result.options["quiet"].value is True

    def test_many_flags_bundled_together(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", short=frozenset({"a"}), arity=ZERO_ARITY),
                "b": OptionSpec("b", short=frozenset({"b"}), arity=ZERO_ARITY),
                "c": OptionSpec("c", short=frozenset({"c"}), arity=ZERO_ARITY),
                "d": OptionSpec("d", short=frozenset({"d"}), arity=ZERO_ARITY),
                "e": OptionSpec("e", short=frozenset({"e"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-abcde"])
        for opt in ["a", "b", "c", "d", "e"]:
            assert result.options[opt].value is True

    def test_bundled_flags_order_irrelevant(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "force": OptionSpec("force", short=frozenset({"f"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec)

        result1 = parser.parse(["-vf"])
        assert result1.options["verbose"].value is True
        assert result1.options["force"].value is True

        result2 = parser.parse(["-fv"])
        assert result2.options["verbose"].value is True
        assert result2.options["force"].value is True


class TestCombinedFlagsWithValues:
    @pytest.mark.parametrize(
        ("args", "expected_output"),
        [
            (["-vo", "file.txt"], "file.txt"),
            (["-vo=file.txt"], "file.txt"),
            (["-vofile.txt"], "file.txt"),
        ],
    )
    def test_bundled_flags_with_value_taking_option(
        self, args: list[str], expected_output: str
    ):
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
        )
        parser = Parser(spec)

        result = parser.parse(args)
        assert result.options["verbose"].value is True
        assert result.options["output"].value == expected_output

    def test_multiple_flags_before_value_taking_option(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "force": OptionSpec("force", short=frozenset({"f"}), arity=ZERO_ARITY),
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vfo", "file.txt"])
        assert result.options["verbose"].value is True
        assert result.options["force"].value is True
        assert result.options["output"].value == "file.txt"

    def test_value_taking_option_consumes_following_character_as_value(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                ),
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
            },
        )
        parser = Parser(spec)

        # -ov should take "v" as the value for -o
        result = parser.parse(["-ov"])
        assert result.options["output"].value == "v"
        assert "verbose" not in result.options


class TestCombinedShortOptionsWithoutEquals:
    def test_value_taking_option_in_middle_of_bundle_raises_error(self):
        args = ["-abc"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", short=frozenset({"a"}), arity=ZERO_ARITY),
                "b": OptionSpec("b", short=frozenset({"b"}), arity=EXACTLY_ONE_ARITY),
                "c": OptionSpec("c", short=frozenset({"c"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(args)


class TestCombinedFlagsWithMultipleValues:
    @pytest.mark.parametrize(
        "args",
        [
            ["-vf", "file1.txt", "file2.txt"],
            ["-vffile1.txt", "file2.txt"],
        ],
    )
    def test_bundled_flags_with_variadic_option(self, args: list[str]):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "files": OptionSpec(
                    "files", short=frozenset({"f"}), arity=ONE_OR_MORE_ARITY
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(args)
        assert result.options["verbose"].value is True
        assert result.options["files"].value == ("file1.txt", "file2.txt")


class TestCombinedFlagsErrorCases:
    def test_unknown_flag_in_bundle_raises_error(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
            },
        )
        parser = Parser(spec)

        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(["-vx"])

        assert "x" in str(exc_info.value).lower()

    def test_value_taking_option_without_value_raises_error(self):
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
        )
        parser = Parser(spec)

        with pytest.raises(InsufficientOptionValuesError):
            _ = parser.parse(["-vo"])


class TestCombinedFlagsWithConstValues:
    def test_combined_with_const_value_flag(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "log-level": OptionSpec(
                    "log-level",
                    short=frozenset({"l"}),
                    arity=ZERO_ARITY,
                    const_value="debug",
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vl"])
        assert result.options["verbose"].value is True
        assert result.options["log-level"].value == "debug"

    def test_const_value_last_in_combination(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "force": OptionSpec("force", short=frozenset({"f"}), arity=ZERO_ARITY),
                "mode": OptionSpec(
                    "mode", short=frozenset({"m"}), arity=ZERO_ARITY, const_value="fast"
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vfm"])
        assert result.options["verbose"].value is True
        assert result.options["force"].value is True
        assert result.options["mode"].value == "fast"


class TestCombinedFlagsWithAccumulation:
    def test_combined_with_collect_mode(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
                "force": OptionSpec("force", short=frozenset({"f"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vf", "-v"])
        assert result.options["verbose"].value == (True, True)
        assert result.options["force"].value is True

    def test_combined_with_count_mode(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vvv"])
        assert result.options["verbose"].value == 3

    def test_separate_and_combined_count(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vv", "-v", "-v"])
        assert result.options["verbose"].value == 4


class TestCombinedFlagsWithFlagValues:
    def test_combined_flags_with_equals_value(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "debug": OptionSpec("debug", short=frozenset({"d"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        result = parser.parse(["-v", "-d=true"])
        assert result.options["verbose"].value is True
        assert result.options["debug"].value is True

    def test_combined_ending_with_equals_invalid(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "debug": OptionSpec("debug", short=frozenset({"d"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec, allow_equals_for_flags=True)

        with pytest.raises(InvalidFlagValueError):
            _ = parser.parse(["-vd="])


class TestComplexCombinedScenarios:
    def test_multiple_bundles_in_single_command(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "force": OptionSpec("force", short=frozenset({"f"}), arity=ZERO_ARITY),
                "quiet": OptionSpec("quiet", short=frozenset({"q"}), arity=ZERO_ARITY),
                "debug": OptionSpec("debug", short=frozenset({"d"}), arity=ZERO_ARITY),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vf", "-qd"])
        assert result.options["verbose"].value is True
        assert result.options["force"].value is True
        assert result.options["quiet"].value is True
        assert result.options["debug"].value is True

    def test_bundled_flags_with_value_option_and_positionals(self):
        spec = CommandSpec(
            name="tar",
            options={
                "create": OptionSpec(
                    "create", short=frozenset({"c"}), arity=ZERO_ARITY
                ),
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "file": OptionSpec(
                    "file", short=frozenset({"f"}), arity=EXACTLY_ONE_ARITY
                ),
            },
            positionals={"files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)},
        )
        parser = Parser(spec)

        # tar -cvf archive.tar file1 file2
        result = parser.parse(["-cvf", "archive.tar", "file1", "file2"])
        assert result.options["create"].value is True
        assert result.options["verbose"].value is True
        assert result.options["file"].value == "archive.tar"
        assert result.positionals["files"].value == ("file1", "file2")

    def test_bundled_short_options_mixed_with_long_options(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "force": OptionSpec("force", short=frozenset({"f"}), arity=ZERO_ARITY),
                "output": OptionSpec("output", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-vf", "--output", "file.txt"])
        assert result.options["verbose"].value is True
        assert result.options["force"].value is True
        assert result.options["output"].value == "file.txt"
