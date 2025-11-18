from aclaf.parser import ZERO_ARITY, CommandSpec, OptionSpec, Parser
from aclaf.parser._types import (
    AccumulationMode,
)


class TestNegationWordFlags:
    def test_flag_with_negation_prefix(self):
        args = ["--no-verbose"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", is_flag=True, negation_words=frozenset({"no"})
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is False

    def test_flag_without_negation_prefix(self):
        args = ["--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", is_flag=True, negation_words=frozenset({"no"})
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["verbose"].value is True

    def test_flag_with_multiple_negation_words(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    is_flag=True,
                    negation_words=frozenset({"no", "disable", "without"}),
                )
            },
        )
        parser = Parser(spec)

        # Test --no-verbose
        result = parser.parse(["--no-verbose"])
        assert result.options["verbose"].value is False

        # Test --disable-verbose
        result = parser.parse(["--disable-verbose"])
        assert result.options["verbose"].value is False

        # Test --without-verbose
        result = parser.parse(["--without-verbose"])
        assert result.options["verbose"].value is False

    def test_negation_with_accumulation(self):
        args = ["--verbose", "--no-verbose", "--verbose"]
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    is_flag=True,
                    negation_words=frozenset({"no"}),
                    accumulation_mode=AccumulationMode.LAST_WINS,
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        # Last value wins, which is --verbose (True)
        assert result.options["verbose"].value is True

    def test_negation_with_no_prefix(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", arity=ZERO_ARITY, negation_words=frozenset({"no"})
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--no-verbose"])
        assert result.options["verbose"].value is False

    def test_negation_with_without_prefix(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "color": OptionSpec(
                    "color", arity=ZERO_ARITY, negation_words=frozenset({"without"})
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--without-color"])
        assert result.options["color"].value is False

    def test_negation_multiple_words(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose",
                    arity=ZERO_ARITY,
                    negation_words=frozenset({"no", "without"}),
                )
            },
        )
        parser = Parser(spec)

        result1 = parser.parse(["--no-verbose"])
        assert result1.options["verbose"].value is False

        result2 = parser.parse(["--without-verbose"])
        assert result2.options["verbose"].value is False

    def test_negation_case_insensitive(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", arity=ZERO_ARITY, negation_words=frozenset({"no"})
                )
            },
        )
        parser = Parser(spec, case_insensitive_options=True)

        result = parser.parse(["--NO-VERBOSE"])
        assert result.options["verbose"].value is False
