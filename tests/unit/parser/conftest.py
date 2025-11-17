from collections.abc import Callable
from typing import TYPE_CHECKING, Unpack

import pytest

from aclaf.parser import (
    CommandSpec,
    OptionSpec,
    ParsedOptionValue,
    ParsedPositionalValue,
    Parser,
    ParserConfigurationInput,
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

ParserFactory = Callable[..., Parser]


@pytest.fixture
def parser_factory() -> ParserFactory:
    def create_parser(
        spec: CommandSpec | None = None, **kwargs: Unpack[ParserConfigurationInput]
    ) -> Parser:
        if spec is None:
            spec = CommandSpec(name="cmd")
        return Parser(spec, **kwargs)

    return create_parser


@pytest.fixture
def flag_equals_parser(parser_factory: ParserFactory) -> ParserFactory:
    def create_parser(
        spec: CommandSpec, **kwargs: Unpack[ParserConfigurationInput]
    ) -> Parser:
        return parser_factory(spec, flag_equals=True, **kwargs)

    return create_parser


@pytest.fixture
def simple_parser():
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


def assert_flag_true(result: "ParseResult", *flag_names: str) -> None:
    for name in flag_names:
        assert name in result.options
        assert result.options[name].value is True


def assert_flag_false(result: "ParseResult", *flag_names: str) -> None:
    for name in flag_names:
        assert name in result.options
        assert result.options[name].value is False


def assert_option_value(
    result: "ParseResult",
    option_name: str,
    expected_value: ParsedOptionValue,
) -> None:
    assert option_name in result.options, f"Option {option_name!r} not found in result"
    actual_value = result.options[option_name].value
    assert actual_value == expected_value, (
        f"Option {option_name!r}: expected {expected_value!r}, got {actual_value!r}"
    )


def assert_positional_value(
    result: "ParseResult",
    index: int,
    expected_value: ParsedPositionalValue,
) -> None:
    positionals_list = list(result.positionals.values())
    assert len(positionals_list) > index, (
        f"Positional at index {index} not found"
        f" (only {len(positionals_list)} positionals)"
    )
    actual_value = positionals_list[index].value
    assert actual_value == expected_value, (
        f"Positional[{index}]: expected {expected_value!r}, got {actual_value!r}"
    )


def assert_raises_parse_error(
    parser: Parser,
    args: list[str],
    error_type: type[Exception],
    *expected_in_message: str,
):
    """Assert that parsing raises a specific error with expected message content."""
    with pytest.raises(error_type) as exc_info:
        _ = parser.parse(args)

    if expected_in_message:
        assert_error_contains(exc_info, *expected_in_message)

    return exc_info


def assert_error_contains(
    exc_info: pytest.ExceptionInfo[Exception], *expected_strings: str
) -> None:
    message = str(exc_info.value).lower()
    expected: str
    for expected in expected_strings:
        assert expected.lower() in message, (
            f"Expected {expected!r} in error message, but got: {exc_info.value!s}"
        )


def assert_error_message(
    exc_info: pytest.ExceptionInfo[Exception], expected_message: str
) -> None:
    actual = str(exc_info.value)
    assert actual == expected_message, (
        f"Expected error message: {expected_message!r}\nGot: {actual!r}"
    )


def assert_suggestions_in_error(
    exc_info: pytest.ExceptionInfo[Exception], *suggested_names: str
) -> None:
    message = str(exc_info.value).lower()
    suggestion: str
    for suggestion in suggested_names:
        assert suggestion.lower() in message, (
            f"Expected suggestion {suggestion!r} in error message: {exc_info.value!s}"
        )
