import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.exceptions import (
    InsufficientPositionalArgumentsError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    Arity,
)


class TestImplicitPositionals:
    """Tests for implicit positional spec (when no positionals defined)."""

    def test_empty_args_creates_empty_tuple(self):
        """When no positionals spec and no args, implicit args has empty tuple."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec)
        result = parser.parse([])
        assert "args" in result.positionals
        assert result.positionals["args"].value == ()

    def test_captures_all_args_in_implicit_spec(self):
        """When no positionals spec, args captured in implicit args."""
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
    """Tests for when positionals is explicitly set to empty.

    Note: Python's truthiness treats empty dict as falsey, so positionals={}
    actually triggers the implicit positionals behavior (same as None).
    To truly have no positionals accepted, the implementation would need
    to distinguish between None and {}.
    """

    def test_empty_dict_behaves_like_implicit(self):
        """When positionals={}, it behaves like implicit (creates 'args')."""
        spec = CommandSpec(name="cmd", positionals={})
        parser = Parser(spec)
        result = parser.parse([])
        # Empty dict is falsey, so triggers implicit spec
        assert "args" in result.positionals
        assert result.positionals["args"].value == ()


class TestSinglePositional:
    """Tests for a single positional argument spec."""

    def test_required_single_arg_captured(self):
        """Single positional with arity (1,1) and one arg."""
        args = ["file.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("file", arity=EXACTLY_ONE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == "file.txt"

    def test_required_single_consumes_first_only(self):
        """Single positional with arity (1,1) and multiple args should only take one."""
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("file", arity=EXACTLY_ONE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Should only consume one, but parser treats extra as part of implicit args
        assert result.positionals["file"].value == "file1.txt"

    def test_required_single_missing_raises_error(self):
        """Single positional with arity (1,1) and no args should raise error."""
        args: list[str] = []
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("file", arity=EXACTLY_ONE_ARITY)]
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.spec_name == "file"
        assert exc_info.value.expected_min == 1
        assert exc_info.value.received == 0

    def test_one_or_more_captures_single(self):
        """Single positional with arity (1, None) and one arg."""
        args = ["file.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("files", arity=ONE_OR_MORE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == ("file.txt",)

    def test_one_or_more_captures_all(self):
        """Single positional with arity (1, None) and multiple args."""
        args = ["file1.txt", "file2.txt", "file3.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("files", arity=ONE_OR_MORE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
            "file3.txt",
        )

    def test_one_or_more_missing_raises_error(self):
        """Single positional with arity (1, None) and no args should raise error."""
        args: list[str] = []
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("files", arity=ONE_OR_MORE_ARITY)]
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError):
            _ = parser.parse(args)

    def test_zero_or_more_arity_with_no_args(self):
        """Single positional with arity (0, None) and no args."""
        args: list[str] = []
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == ()

    def test_zero_or_more_arity_with_multiple_args(self):
        """Single positional with arity (0, None) and multiple args."""
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == ("file1.txt", "file2.txt")

    def test_zero_or_one_arity_with_no_args(self):
        """Single positional with arity (0, 1) and no args."""
        args: list[str] = []
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("file", arity=ZERO_OR_ONE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == ()

    def test_zero_or_one_arity_with_one_arg(self):
        """Single positional with arity (0, 1) and one arg."""
        args = ["file.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("file", arity=ZERO_OR_ONE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == ("file.txt",)

    def test_zero_or_one_arity_with_multiple_args(self):
        """Single positional with arity (0, 1) and multiple args takes one."""
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("file", arity=ZERO_OR_ONE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == ("file1.txt",)

    def test_fixed_arity_two(self):
        """Single positional with arity (2, 2) and exactly two args."""
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("files", arity=Arity(2, 2))]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["files"].value == ("file1.txt", "file2.txt")

    def test_fixed_arity_two_insufficient(self):
        """Single positional with arity (2, 2) and only one arg should raise error."""
        args = ["file1.txt"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("files", arity=Arity(2, 2))]
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.expected_min == 2
        assert exc_info.value.received == 1

    def test_range_arity(self):
        """Single positional with range arity (1, 3)."""
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("files", arity=Arity(1, 3))]
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
    """Tests for multiple positional argument specs."""

    def test_two_fixed_arities(self):
        """Two positionals with fixed arity (1,1) and (1,1)."""
        args = ["source.txt", "dest.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("source", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["source"].value == "source.txt"
        assert result.positionals["dest"].value == "dest.txt"

    def test_two_fixed_arities_insufficient(self):
        """Two positionals with fixed arity but only one arg."""
        args = ["source.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("source", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        with pytest.raises(InsufficientPositionalArgumentsError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.spec_name == "dest"

    def test_unbounded_first_required_second(self):
        """Unbounded first positional followed by required second."""
        args = ["file1.txt", "file2.txt", "dest.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("sources", arity=ZERO_OR_MORE_ARITY),
                PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # First should take all except what's needed for second
        assert result.positionals["sources"].value == ("file1.txt", "file2.txt")
        assert result.positionals["dest"].value == "dest.txt"

    def test_unbounded_first_required_second_minimal_args(self):
        """Unbounded first with only enough args for required second."""
        args = ["dest.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("sources", arity=ZERO_OR_MORE_ARITY),
                PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["sources"].value == ()
        assert result.positionals["dest"].value == "dest.txt"

    def test_required_first_unbounded_second(self):
        """Required first positional followed by unbounded second."""
        args = ["source.txt", "file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("source", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("destinations", arity=ZERO_OR_MORE_ARITY),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["source"].value == "source.txt"
        assert result.positionals["destinations"].value == ("file1.txt", "file2.txt")

    def test_three_positionals_mixed_arities(self):
        """Three positionals with mixed arity configurations."""
        args = ["cmd.txt", "file1.txt", "file2.txt", "output.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("command", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("files", arity=ONE_OR_MORE_ARITY),
                PositionalSpec("output", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["command"].value == "cmd.txt"
        assert result.positionals["files"].value == ("file1.txt", "file2.txt")
        assert result.positionals["output"].value == "output.txt"

    def test_unbounded_middle_distributes_correctly(self):
        """Unbounded middle positional should leave enough for following."""
        args = ["first.txt", "mid1.txt", "mid2.txt", "last.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("first", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("middle", arity=ZERO_OR_MORE_ARITY),
                PositionalSpec("last", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["first"].value == "first.txt"
        assert result.positionals["middle"].value == ("mid1.txt", "mid2.txt")
        assert result.positionals["last"].value == "last.txt"

    def test_multiple_unbounded_first_gets_none_when_later_required(self):
        """When first is unbounded and later requires values, first gets minimal."""
        args = ["file1.txt", "file2.txt"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("optional", arity=ZERO_OR_MORE_ARITY),
                PositionalSpec("required1", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("required2", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["optional"].value == ()
        assert result.positionals["required1"].value == "file1.txt"
        assert result.positionals["required2"].value == "file2.txt"

    def test_range_arity_respects_max(self):
        """Range arity should respect maximum even with more args available."""
        args = ["a", "b", "c", "d", "e"]
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("first", arity=Arity(1, 2)),
                PositionalSpec("second", arity=Arity(1, 2)),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["first"].value == ("a", "b")
        assert result.positionals["second"].value == ("c", "d")

    def test_optional_followed_by_optional(self):
        """Two optional positionals."""
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("first", arity=ZERO_OR_ONE_ARITY),
                PositionalSpec("second", arity=ZERO_OR_ONE_ARITY),
            ],
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


class TestPositionalsWithOptions:
    """Tests for positionals combined with options."""

    def test_options_before_positionals(self):
        """Options before positionals should be parsed separately."""
        args = ["--verbose", "file.txt"]
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("verbose", is_flag=True)],
            positionals=[PositionalSpec("file", arity=EXACTLY_ONE_ARITY)],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Verify both option and positional are parsed
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"

    def test_positionals_after_double_dash(self):
        """Args after -- should be in extra_args, not positionals."""
        args = ["file.txt", "--", "--not-an-option"]
        spec = CommandSpec(
            name="cmd", positionals=[PositionalSpec("file", arity=EXACTLY_ONE_ARITY)]
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.positionals["file"].value == "file.txt"
        assert result.extra_args == ("--not-an-option",)
