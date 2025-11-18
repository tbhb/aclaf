import pytest

from aclaf.parser import (
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    CommandSpec,
    OptionSpec,
    Parser,
    ParseResult,
)
from aclaf.parser._exceptions import DuplicateOptionError
from aclaf.parser._types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    AccumulationMode,
    Arity,
)


class TestCollectMode:
    def test_works_with_boolean_flags(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    short=frozenset({"v"}),
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-v", "-v", "-v"])
        assert result.options["verbose"].value == (True, True, True)

    def test_works_with_multi_value_options(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == (("a", "b"), ("c", "d"))

    def test_works_alongside_other_options(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "collect": OptionSpec(
                    "collect", accumulation_mode=AccumulationMode.COLLECT
                ),
                "normal": OptionSpec("normal", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--collect", "v1", "--normal", "n", "--collect", "v2"])
        assert result.options["collect"].value == ("v1", "v2")
        assert result.options["normal"].value == "n"


class TestCountMode:
    def test_counts_combined_short_flags(self):
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

    def test_counts_mixed_flag_forms(self):
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

        result = parser.parse(["-vv", "-v", "-vvv"])
        assert result.options["verbose"].value == 6


class TestFirstWinsMode:
    def test_accumulation_first_wins_with_flags(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--flag", "--flag", "--flag"])
        assert result.options["flag"].value is True

    def test_accumulation_first_wins_with_multi_value_option(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == ("a", "b")

    def test_first_wins_different_forms(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    short=frozenset({"o"}),
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--output", "long.txt", "-o", "short.txt"])
        assert result.options["output"].value == "long.txt"

    def test_first_wins_keeps_first_value(self):
        args = ["--output", "file1.txt", "--output", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Should keep only first value
        assert result.options["output"].value == "file1.txt"

    def test_first_wins_with_multiple_occurrences(self):
        args = ["-o", "a", "-o", "b", "-o", "c"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    short=frozenset({"o"}),
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == "a"

    def test_advanced_first_wins_with_flags(self):
        args = ["--verbose", "--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    is_flag=True,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_advanced_first_wins_with_multi_value_option(self):
        args = ["--files", "a", "b", "--files", "c", "d"]
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=ZERO_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Should keep only first occurrence's values
        assert result.options["files"].value == ("a", "b")


class TestLastWinsMode:
    def test_last_wins_is_default(self):
        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt")},  # No accumulation_mode specified
        )
        parser = Parser(spec)

        result = parser.parse(["--opt", "first", "--opt", "last"])
        assert result.options["opt"].value == "last"

    def test_last_wins_with_flags(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.LAST_WINS,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--flag", "--flag"])
        assert result.options["flag"].value is True

    def test_last_wins_with_multi_value_option(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    "files",
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.LAST_WINS,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--files", "a", "b", "--files", "c", "d"])
        assert result.options["files"].value == ("c", "d")


class TestErrorMode:
    def test_allows_single_occurrence(self):
        args = ["--output", "file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.ERROR,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["output"].value == "file.txt"

    def test_error_with_flags(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag",
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.ERROR,
                )
            },
        )
        parser = Parser(spec)

        with pytest.raises(DuplicateOptionError):
            _ = parser.parse(["--flag", "--flag"])

    def test_error_with_values(self):
        args = ["--output", "file1.txt", "--output", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.ERROR,
                )
            },
        )
        parser = Parser(spec)
        with pytest.raises(DuplicateOptionError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.option_spec.name == "output"

    def test_error_different_forms_still_duplicate(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "output": OptionSpec(
                    "output",
                    short=frozenset({"o"}),
                    accumulation_mode=AccumulationMode.ERROR,
                ),
            },
        )
        parser = Parser(spec)

        with pytest.raises(DuplicateOptionError):
            _ = parser.parse(["--output", "file1.txt", "-o", "file2.txt"])


class TestAccumulationModeInteractions:
    def test_accumulation_mode_with_const_value(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "mode": OptionSpec(
                    "mode",
                    arity=ZERO_ARITY,
                    const_value="debug",
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--mode", "--mode", "--mode"])
        assert result.options["mode"].value == ("debug", "debug", "debug")

    def test_accumulation_with_negation(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    arity=ZERO_ARITY,
                    negation_words=frozenset({"no"}),
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--verbose", "--no-verbose", "--verbose"])
        assert result.options["verbose"].value == (True, False, True)

    def test_different_accumulation_modes_per_option(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "collect": OptionSpec(
                    "collect", accumulation_mode=AccumulationMode.COLLECT
                ),
                "count": OptionSpec(
                    "count", arity=ZERO_ARITY, accumulation_mode=AccumulationMode.COUNT
                ),
                "first": OptionSpec(
                    "first", accumulation_mode=AccumulationMode.FIRST_WINS
                ),
                "last": OptionSpec(
                    "last", accumulation_mode=AccumulationMode.LAST_WINS
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "--collect",
                "c1",
                "--count",
                "--first",
                "f1",
                "--last",
                "l1",
                "--collect",
                "c2",
                "--count",
                "--first",
                "f2",
                "--last",
                "l2",
            ]
        )
        assert result.options["collect"].value == ("c1", "c2")
        assert result.options["count"].value == 2
        assert result.options["first"].value == "f1"
        assert result.options["last"].value == "l2"

    def test_accumulation_with_arity_range(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "range": OptionSpec(
                    "range",
                    arity=Arity(2, 4),
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--range", "a", "b", "--range", "c", "d", "e"])
        assert result.options["range"].value == (("a", "b"), ("c", "d", "e"))


class TestAccumulationEdgeCases:
    def test_collect_empty_when_not_provided(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)
            },
        )
        parser = Parser(spec)

        result = parser.parse([])
        assert "opt" not in result.options

    def test_error_message_contains_option_name(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "myoption": OptionSpec(
                    "myoption", accumulation_mode=AccumulationMode.ERROR
                )
            },
        )
        parser = Parser(spec)

        with pytest.raises(DuplicateOptionError) as exc_info:
            _ = parser.parse(["--myoption", "v1", "--myoption", "v2"])

        assert "myoption" in str(exc_info.value).lower()


class TestFlattenNestedTuples:
    def test_non_tuple_value_early_return(self):
        spec = CommandSpec(
            name="test",
            options={
                "name": OptionSpec(
                    name="name",
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["--name", "value"])

        # Single value option returns scalar, not tuple
        assert result.options["name"].value == "value"
        assert not isinstance(result.options["name"].value, tuple)

    def test_flat_tuple_value_early_return(self):
        spec = CommandSpec(
            name="test",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=ZERO_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.FIRST_WINS,
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["--files", "a.txt", "b.txt"])

        # Multiple values with FIRST_WINS return flat tuple
        assert isinstance(result.options["files"].value, tuple)
        assert result.options["files"].value == ("a.txt", "b.txt")

    def test_nested_tuple_value_gets_flattened(self):
        spec = CommandSpec(
            name="test",
            options={
                "items": OptionSpec(
                    name="items",
                    arity=ZERO_OR_ONE_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["--items", "a", "--items", "b"])

        # COLLECT mode with multiple invocations creates nested tuples
        # that get flattened
        assert isinstance(result.options["items"].value, tuple)
        assert result.options["items"].value == ("a", "b")
