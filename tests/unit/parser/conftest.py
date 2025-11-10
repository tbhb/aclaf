"""Shared test fixtures and utilities for parser tests.

This module provides reusable pytest fixtures and assertion helper functions for
parser unit tests. The fixtures create pre-configured parsers for common scenarios,
and the assertion helpers provide clear, consistent error messages for test failures.

## Fixtures

### simple_parser
Basic parser with three common options (verbose, output, input).
Useful for testing fundamental option parsing without complexity.

Usage:
    def test_basic_option(simple_parser):
        result = simple_parser.parse(["-v"])
        assert result.options["verbose"].value is True

### parser_with_positionals
Parser with one option and two required positional arguments.
Useful for testing positional argument handling.

Usage:
    def test_positionals(parser_with_positionals):
        result = parser_with_positionals.parse(["-v", "src.txt", "dst.txt"])
        assert result.positionals["source"].value == "src.txt"

### parser_with_subcommands
Parser with two subcommands (add, remove) that have their own options/positionals.
Useful for testing subcommand resolution and parsing.

Usage:
    def test_subcommand(parser_with_subcommands):
        result = parser_with_subcommands.parse(["add", "-f", "file.txt"])
        assert result.subcommand.command == "add"

### complex_command_spec
Full-featured CommandSpec with options, positionals, and nested subcommands.
Returns a spec (not a parser) for flexible test configuration.

Usage:
    def test_complex(complex_command_spec):
        parser = Parser(complex_command_spec)
        result = parser.parse(["process", "-t", "4"])

## Assertion Helpers

### assert_option_value(result, name, value)
Assert that an option was parsed with the expected value.
Provides clear error messages showing expected vs. actual values.

Usage:
    assert_option_value(result, "verbose", True)
    assert_option_value(result, "files", ("a.txt", "b.txt"))

### assert_positional_value(result, index, value)
Assert that a positional argument at a given index has the expected value.
Uses index-based access for simple positional checking.

Usage:
    assert_positional_value(result, 0, "file.txt")
    assert_positional_value(result, 1, ("a", "b"))

### assert_error_contains(exc_info, *strings)
Assert that an exception message contains all expected strings (case-insensitive).
Useful for flexible error message verification.

Usage:
    with pytest.raises(ValueError) as exc:
        parser.parse(["--bad"])
    assert_error_contains(exc, "unknown", "option")

### assert_error_message(exc_info, message)
Assert that an exception message exactly matches the expected message.
Use for precise error message verification.

Usage:
    with pytest.raises(ValueError) as exc:
        parser.parse([])
    assert_error_message(exc, "Missing required argument")

### assert_suggestions_in_error(exc_info, *names)
Assert that an error message contains suggestions for similar names.
Useful for testing fuzzy matching and error suggestions.

Usage:
    with pytest.raises(UnknownOptionError) as exc:
        parser.parse(["--verbse"])
    assert_suggestions_in_error(exc, "verbose")
"""

from typing import TYPE_CHECKING

import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    Parser,
    PositionalSpec,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
)

if TYPE_CHECKING:
    from aclaf.parser import ParseResult


@pytest.fixture
def simple_parser():
    """Create a parser with basic options for testing."""
    spec = CommandSpec(
        name="cmd",
        options={
            "verbose": OptionSpec("verbose", short=frozenset({"v"}), arity=ZERO_ARITY),
            "output": OptionSpec(
                "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
            ),
            "input": OptionSpec(
                "input", short=frozenset({"i"}), arity=EXACTLY_ONE_ARITY
            ),
        },
    )
    return Parser(spec)


@pytest.fixture
def parser_with_positionals():
    """Create a parser with positionals for testing."""
    spec = CommandSpec(
        name="cmd",
        options={
            "verbose": OptionSpec("verbose", short=frozenset({"v"}), arity=ZERO_ARITY)
        },
        positionals={
            "source": PositionalSpec("source", arity=EXACTLY_ONE_ARITY),
            "dest": PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
        },
    )
    return Parser(spec)


@pytest.fixture
def parser_with_subcommands():
    """Create a parser with subcommands for testing."""
    spec = CommandSpec(
        name="cmd",
        subcommands={
            "add": CommandSpec(
                name="add",
                options={
                    "force": OptionSpec(
                        "force", short=frozenset({"f"}), arity=ZERO_ARITY
                    )
                },
                positionals={"files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)},
            ),
            "remove": CommandSpec(
                name="remove",
                aliases=frozenset({"rm"}),
                options={
                    "recursive": OptionSpec(
                        "recursive", short=frozenset({"r"}), arity=ZERO_ARITY
                    )
                },
                positionals={"files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)},
            ),
        },
    )
    return Parser(spec)


@pytest.fixture
def complex_command_spec():
    """Create a complex command spec with options, positionals, and subcommands."""
    return CommandSpec(
        name="tool",
        options={
            "verbose": OptionSpec("verbose", short=frozenset({"v"}), arity=ZERO_ARITY),
            "output": OptionSpec(
                "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
            ),
            "files": OptionSpec(
                "files", short=frozenset({"f"}), arity=ONE_OR_MORE_ARITY
            ),
        },
        positionals={
            "input": PositionalSpec("input", arity=EXACTLY_ONE_ARITY),
            "extras": PositionalSpec("extras", arity=ZERO_OR_MORE_ARITY),
        },
        subcommands={
            "process": CommandSpec(
                name="process",
                aliases=frozenset({"proc"}),
                options={
                    "threads": OptionSpec(
                        "threads", short=frozenset({"t"}), arity=EXACTLY_ONE_ARITY
                    ),
                },
            ),
            "analyze": CommandSpec(
                name="analyze",
                options={
                    "depth": OptionSpec(
                        "depth", short=frozenset({"d"}), arity=EXACTLY_ONE_ARITY
                    ),
                },
            ),
        },
    )


# Assertion helpers


def assert_option_value(
    result: "ParseResult",
    option_name: str,
    expected_value: bool  # noqa: FBT001
    | int
    | str
    | tuple[bool, ...]
    | tuple[str, ...]
    | tuple[tuple[str, ...], ...],
) -> None:
    """Assert that a parsed option has the expected value."""
    assert option_name in result.options, f"Option {option_name!r} not found in result"
    actual_value = result.options[option_name].value
    assert actual_value == expected_value, (
        f"Option {option_name!r}: expected {expected_value!r}, got {actual_value!r}"
    )


def assert_positional_value(
    result: "ParseResult",
    index: int,
    expected_value: str | tuple[str, ...],
) -> None:
    """Assert that a parsed positional has the expected value."""
    positionals_list = list(result.positionals.values())
    assert len(positionals_list) > index, (
        f"Positional at index {index} not found"
        f" (only {len(positionals_list)} positionals)"
    )
    actual_value = positionals_list[index].value
    assert actual_value == expected_value, (
        f"Positional[{index}]: expected {expected_value!r}, got {actual_value!r}"
    )


def assert_error_contains(
    exc_info: pytest.ExceptionInfo[Exception], *expected_strings: str
) -> None:
    """Assert exception message contains all expected strings (case-insensitive)."""
    message = str(exc_info.value).lower()
    expected: str
    for expected in expected_strings:
        assert expected.lower() in message, (
            f"Expected {expected!r} in error message, but got: {exc_info.value!s}"
        )


def assert_error_message(
    exc_info: pytest.ExceptionInfo[Exception], expected_message: str
) -> None:
    """Assert that an exception message exactly matches the expected message."""
    actual = str(exc_info.value)
    assert actual == expected_message, (
        f"Expected error message: {expected_message!r}\nGot: {actual!r}"
    )


def assert_suggestions_in_error(
    exc_info: pytest.ExceptionInfo[Exception], *suggested_names: str
) -> None:
    """Assert that error message contains suggestions for similar names."""
    message = str(exc_info.value).lower()
    suggestion: str
    for suggestion in suggested_names:
        assert suggestion.lower() in message, (
            f"Expected suggestion {suggestion!r} in error message: {exc_info.value!s}"
        )
