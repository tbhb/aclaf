from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_OR_MORE_ARITY,
)


class TestStrictOptionsBeforePositionals:
    def test_long_option_after_positional_strict_mode(self):
        args = ["file.txt", "--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", is_flag=True)},
            positionals={"files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=True)
        result = parser.parse(args)
        # --verbose should be treated as a positional, not an option
        assert "verbose" not in result.options
        assert result.positionals["files"].value == ("file.txt", "--verbose")

    def test_short_option_after_positional_strict_mode(self):
        args = ["file.txt", "-v"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
            positionals={"files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=True)
        result = parser.parse(args)
        # -v should be treated as a positional, not an option
        assert "verbose" not in result.options
        assert result.positionals["files"].value == ("file.txt", "-v")

    def test_long_option_after_positional_non_strict(self):
        args = ["file.txt", "--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", is_flag=True)},
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=False)
        result = parser.parse(args)
        # --verbose should be parsed as an option
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"

    def test_short_option_after_positional_non_strict(self):
        args = ["file.txt", "-v"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True)
            },
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=False)
        result = parser.parse(args)
        # -v should be parsed as an option
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"
