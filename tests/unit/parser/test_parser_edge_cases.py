import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser
from aclaf.parser.exceptions import (
    UnknownOptionError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
)


class TestLongOptionEdgeCases:
    def test_flag_with_value_from_next_args(self):
        args = ["--verbose", "true"]
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", is_flag=True)},
        )
        parser = Parser(spec, allow_equals_for_flags=True)
        result = parser.parse(args)
        # Should parse "true" as the flag value
        assert result.options["verbose"].value is True


class TestShortOptionEdgeCases:
    def test_inner_flag_in_combined_options(self):
        args = ["-abc"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", is_flag=True),
                "b": OptionSpec("b", is_flag=True),
                "c": OptionSpec("c", is_flag=True),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["c"].value is True

    def test_last_option_with_const_value_in_combined(self):
        args = ["-abv"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", is_flag=True),
                "b": OptionSpec("b", is_flag=True),
                "v": OptionSpec("v", is_flag=True, const_value="verbose_mode"),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["v"].value == "verbose_mode"

    def test_unknown_option_at_start_raises(self):
        args = ["-x"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", is_flag=True),
                "f": OptionSpec("f", is_flag=True),
            },
        )
        parser = Parser(spec)
        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse(args)
        assert exc_info.value.name == "x"

    def test_combined_flags_ending_with_equals(self):
        args = ["-ab=", "value"]
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", is_flag=True),
                "b": OptionSpec("b", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["a"].value is True
        # b should get "" as inline value from the '='
        assert result.options["b"].value == ""
