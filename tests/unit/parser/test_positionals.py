import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, ParseResult, PositionalSpec
from aclaf.parser._exceptions import (
    InsufficientPositionalArgumentsError,
)
from aclaf.parser._types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    Arity,
)


class TestImplicitPositionals:
    def test_empty_args_creates_empty_tuple(self):
        spec = CommandSpec(name="cmd")
        parser = Parser(spec)
        result = parser.parse([])
        assert "args" in result.positionals
        assert result.positionals["args"].value == ()

    def test_captures_all_args_in_implicit_spec(self):
        args = ["file1.txt", "file2.txt", "file3.txt"]
        spec = CommandSpec(name="cmd")
        parser = Parser(spec)
        result = parser.parse(args)
        assert "args" in result.positionals
        assert result.positionals["args"].value == (
            "file1.txt",
            "file2.txt",
            "file3.txt",
        )


class TestExplicitEmptyPositionals:
    def test_empty_dict_behaves_like_implicit(self):
        spec = CommandSpec(name="cmd", positionals={})
        parser = Parser(spec)
        result = parser.parse([])
        # Empty dict is falsey, so triggers implicit spec
        assert "args" in result.positionals
        assert result.positionals["args"].value == ()


class TestSinglePositional:
    def test_required_single_arg_captured(self):
        args = ["file.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == "file.txt"

    def test_required_single_consumes_first_only(self):
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Should only consume one, but parser treats extra as part of implicit args
        assert result.positionals["file"].value == "file1.txt"

    def test_required_single_missing_raises_error(self):
        args: list[str] = []
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.spec_name == "file"
        assert exc_info.value.expected_min == 1
        assert exc_info.value.received == 0

    def test_one_or_more_captures_single(self):
        args = ["file.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == ("file.txt",)

    def test_one_or_more_captures_all(self):
        args = ["file1.txt", "file2.txt", "file3.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
            "file3.txt",
        )

    def test_one_or_more_missing_raises_error(self):
        args: list[str] = []
        spec = CommandSpec(
            name="cmd",
            positionals={"files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)},
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError):
            _ = parser.parse(args)

    def test_zero_or_more_arity_with_no_args(self):
        args: list[str] = []
        spec = CommandSpec(
            name="cmd",
            positionals={"files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == ()

    def test_zero_or_more_arity_with_multiple_args(self):
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == ("file1.txt", "file2.txt")

    def test_zero_or_one_arity_with_no_args(self):
        args: list[str] = []
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=ZERO_OR_ONE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # For arity (0, 1), parser returns scalar (empty string when no value)
        assert result.positionals["file"].value == ""

    def test_zero_or_one_arity_with_one_arg(self):
        args = ["file.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=ZERO_OR_ONE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == ("file.txt",)

    def test_zero_or_one_arity_with_multiple_args(self):
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=ZERO_OR_ONE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == ("file1.txt",)

    def test_fixed_arity_two(self):
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"files": PositionalSpec("files", arity=Arity(2, 2))},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == ("file1.txt", "file2.txt")

    def test_fixed_arity_two_insufficient(self):
        args = ["file1.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={"files": PositionalSpec("files", arity=Arity(2, 2))},
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.expected_min == 2
        assert exc_info.value.received == 1

    def test_range_arity(self):
        spec = CommandSpec(
            name="cmd",
            positionals={"files": PositionalSpec("files", arity=Arity(1, 3))},
        )
        parser = Parser(spec)

        # With 1 arg
        result = parser.parse(["file1.txt"])
        assert result.positionals["files"].value == ("file1.txt",)

        # With 2 args
        result = parser.parse(["file1.txt", "file2.txt"])
        assert result.positionals["files"].value == ("file1.txt", "file2.txt")

        # With 3 args
        result = parser.parse(["file1.txt", "file2.txt", "file3.txt"])
        assert result.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
            "file3.txt",
        )

        # With 4 args should only take 3
        result = parser.parse(["file1.txt", "file2.txt", "file3.txt", "file4.txt"])
        assert result.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
            "file3.txt",
        )


class TestMultiplePositionals:
    def test_two_fixed_arities(self):
        args = ["source.txt", "dest.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "source": PositionalSpec("source", arity=EXACTLY_ONE_ARITY),
                "dest": PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["source"].value == "source.txt"
        assert result.positionals["dest"].value == "dest.txt"

    def test_two_fixed_arities_insufficient(self):
        args = ["source.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "source": PositionalSpec("source", arity=EXACTLY_ONE_ARITY),
                "dest": PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.spec_name == "dest"

    def test_unbounded_first_required_second(self):
        args = ["file1.txt", "file2.txt", "dest.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "sources": PositionalSpec("sources", arity=ZERO_OR_MORE_ARITY),
                "dest": PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # First should take all except what's needed for second
        assert result.positionals["sources"].value == ("file1.txt", "file2.txt")
        assert result.positionals["dest"].value == "dest.txt"

    def test_unbounded_first_required_second_minimal_args(self):
        args = ["dest.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "sources": PositionalSpec("sources", arity=ZERO_OR_MORE_ARITY),
                "dest": PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["sources"].value == ()
        assert result.positionals["dest"].value == "dest.txt"

    def test_required_first_unbounded_second(self):
        args = ["source.txt", "file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "source": PositionalSpec("source", arity=EXACTLY_ONE_ARITY),
                "destinations": PositionalSpec(
                    "destinations", arity=ZERO_OR_MORE_ARITY
                ),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["source"].value == "source.txt"
        assert result.positionals["destinations"].value == ("file1.txt", "file2.txt")

    def test_three_positionals_mixed_arities(self):
        args = ["cmd.txt", "file1.txt", "file2.txt", "output.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "command": PositionalSpec("command", arity=EXACTLY_ONE_ARITY),
                "files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY),
                "output": PositionalSpec("output", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["command"].value == "cmd.txt"
        assert result.positionals["files"].value == ("file1.txt", "file2.txt")
        assert result.positionals["output"].value == "output.txt"

    def test_unbounded_middle_distributes_correctly(self):
        args = ["first.txt", "mid1.txt", "mid2.txt", "last.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "first": PositionalSpec("first", arity=EXACTLY_ONE_ARITY),
                "middle": PositionalSpec("middle", arity=ZERO_OR_MORE_ARITY),
                "last": PositionalSpec("last", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["first"].value == "first.txt"
        assert result.positionals["middle"].value == ("mid1.txt", "mid2.txt")
        assert result.positionals["last"].value == "last.txt"

    def test_multiple_unbounded_first_gets_none_when_later_required(self):
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "optional": PositionalSpec("optional", arity=ZERO_OR_MORE_ARITY),
                "required1": PositionalSpec("required1", arity=EXACTLY_ONE_ARITY),
                "required2": PositionalSpec("required2", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["optional"].value == ()
        assert result.positionals["required1"].value == "file1.txt"
        assert result.positionals["required2"].value == "file2.txt"

    def test_range_arity_respects_max(self):
        args = ["a", "b", "c", "d", "e"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "first": PositionalSpec("first", arity=Arity(1, 2)),
                "second": PositionalSpec("second", arity=Arity(1, 2)),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["first"].value == ("a", "b")
        assert result.positionals["second"].value == ("c", "d")

    def test_optional_followed_by_optional(self):
        spec = CommandSpec(
            name="cmd",
            positionals={
                "first": PositionalSpec("first", arity=ZERO_OR_ONE_ARITY),
                "second": PositionalSpec("second", arity=ZERO_OR_ONE_ARITY),
            },
        )
        parser = Parser(spec)

        # No args
        empty_args: list[str] = []
        result = parser.parse(empty_args)
        assert result.positionals["first"].value == ()
        assert result.positionals["second"].value == ()

        # One arg
        result = parser.parse(["a"])
        assert result.positionals["first"].value == ("a",)
        assert result.positionals["second"].value == ()

        # Two args
        result = parser.parse(["a", "b"])
        assert result.positionals["first"].value == ("a",)
        assert result.positionals["second"].value == ("b",)

    def test_sufficient_args_passes(self):
        spec = CommandSpec(
            name="test",
            positionals={
                "input": PositionalSpec(name="input", arity=EXACTLY_ONE_ARITY),
                "output": PositionalSpec(name="output", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec=spec)
        result: ParseResult = parser.parse(["input.txt", "output.txt"])

        assert result.positionals["input"].value == "input.txt"
        assert result.positionals["output"].value == "output.txt"

    def test_insufficient_args_in_loop_iteration(self):
        spec = CommandSpec(
            name="test",
            positionals={
                "input": PositionalSpec(name="input", arity=EXACTLY_ONE_ARITY),
                "output": PositionalSpec(name="output", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec=spec)

        with pytest.raises(
            InsufficientPositionalArgumentsError,
            match=r"'output'.*requires at least 1.*got 0",
        ):
            _ = parser.parse(["input.txt"])


class TestPositionalsWithOptions:
    def test_options_before_positionals(self):
        args = ["--verbose", "file.txt"]
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", is_flag=True)},
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Verify both option and positional are parsed
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"

    def test_positionals_after_double_dash(self):
        args = ["file.txt", "--", "--not-an-option"]
        spec = CommandSpec(
            name="cmd",
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == "file.txt"
        assert result.extra_args == ("--not-an-option",)


class TestPositionalEdgeCases:
    def test_insufficient_positionals_finds_first_unsatisfied(self):
        args = ["file1.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals={
                "first": PositionalSpec("first", arity=EXACTLY_ONE_ARITY),
                "second": PositionalSpec("second", arity=EXACTLY_ONE_ARITY),
                "third": PositionalSpec("third", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError) as exc_info:
            _ = parser.parse(args)
        # Should report "second" as the first that can't be satisfied
        assert exc_info.value.spec_name == "second"
        assert exc_info.value.expected_min == 1
        assert exc_info.value.received == 0
