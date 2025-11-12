"""Branch coverage tests for parser conditional logic.

This module provides tests specifically targeting branch coverage for
conditional logic in the parser. These tests ensure both true and false
paths are exercised in conditionals, multi-way branches, guard clauses,
and error handling.

Each test documents the specific line(s) and branch condition in _parser.py
that it targets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.exceptions import (
    InsufficientOptionValuesError,
    InsufficientPositionalArgumentsError,
    OptionDoesNotAcceptValueError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    AccumulationMode,
    Arity,
)

if TYPE_CHECKING:
    from aclaf.parser import ParseResult


class TestFlagConstValueBranches:
    """Test branches for flag options with const_value.

    These tests cover the conditional branches in short option processing
    where flags may or may not have const_value set, affecting the parsed
    value.
    """

    def test_flag_with_const_value_in_short_cluster(self):
        """Flag with const_value in short option cluster returns const_value.

        Tests line 526-534 in _parser.py where a flag in a short option
        cluster has const_value set, taking the first branch of the
        conditional (is_flag and const_value is not None).
        """
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
        """Flag without const_value in short option cluster returns True.

        Tests line 536-541 in _parser.py where a flag in a short option
        cluster does NOT have const_value, taking the second branch of the
        conditional (is_flag but const_value is None).
        """
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
        """Zero-arity option with const_value returns const_value.

        Tests line 546-554 in _parser.py where a non-flag zero-arity option
        has const_value set in a short option cluster.
        """
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
        """Zero-arity option without const_value returns True.

        Tests line 556-561 in _parser.py where a non-flag zero-arity option
        does NOT have const_value in a short option cluster.
        """
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


class TestArityMinBranches:
    """Test branches for arity.min conditionals.

    These tests cover conditional branches where arity.min is checked to
    determine if values are required and how many.
    """

    def test_short_option_arity_min_greater_than_one_with_inline_value(
        self,
    ):
        """Short option with arity.min > 1 and inline value raises error.

        Tests line 718-721 in _parser.py where a short option with arity.min > 1
        is given only an inline value, taking the error branch.
        """
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
        """Short option with arity.min = 1 and inline value succeeds.

        Tests line 718-728 in _parser.py where a short option with arity.min = 1
        is given an inline value, taking the success branch (not line 719).
        """
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


class TestInlineValueBranches:
    """Test branches for inline value handling.

    These tests cover conditionals where inline values (via = syntax) are
    present or absent, affecting parsing behavior.
    """

    def test_zero_arity_with_inline_value_raises_error(self):
        """Zero-arity option with inline value raises error.

        Tests line 656-659 in _parser.py where a zero-arity non-flag option
        in last position receives an inline value, taking the error branch.
        """
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
        """Zero-arity option with const_value and no inline value succeeds.

        Tests line 661-669 in _parser.py where a zero-arity option has
        const_value but no inline value, taking the const_value branch.
        """
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
        """Zero-arity option without const_value and no inline value succeeds.

        Tests line 671-678 in _parser.py where a zero-arity option has no
        const_value and no inline value, returning True.
        """
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


class TestPositionalValidationBranches:
    """Test branches for positional argument validation.

    These tests cover conditional branches in positional argument validation,
    including the guard clause that checks if there are insufficient positionals.
    """

    def test_positional_validation_sufficient_args_passes(self):
        """Positional validation with sufficient args passes guard clause.

        Tests line 892-896 in _parser.py where positional validation checks
        if there are sufficient arguments. This test ensures the FALSE branch
        is taken (sufficient args, no error raised).
        """
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

    def test_positional_validation_insufficient_args_in_loop_iteration(self):
        """Positional validation detects insufficient args in second iteration.

        Tests line 892-896 in _parser.py where the validation loop checks
        each positional spec and determines that the SECOND spec doesn't have
        enough remaining arguments, taking the TRUE branch (error raised).
        """
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


class TestFlattenNestedTuplesBranches:
    """Test branches in _flatten_nested_tuples utility.

    These tests cover guard clause branches that determine if tuple flattening
    is needed based on the structure of parsed option values.
    """

    def test_non_tuple_value_early_return(self):
        """Non-tuple value returns early without processing.

        Tests line 1402-1403 in _parser.py where the value is not a tuple,
        taking the TRUE branch (early return).
        """
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
        """Flat tuple value returns early without flattening.

        Tests line 1407-1408 in _parser.py where the value is a tuple but
        not nested (first element is not a tuple), taking the TRUE branch
        (early return).
        """
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
        """Nested tuple value gets flattened.

        Tests line 1407-1419 in _parser.py where the value is a nested tuple
        structure from COLLECT mode, taking the FALSE branch (flattening occurs).
        """
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
