from io import StringIO
from typing import TYPE_CHECKING, Unpack

import pytest

from aclaf.conversion import ConverterRegistry
from aclaf.execution import (
    Context,
    RuntimeCommand,
    RuntimeParameter,
)
from aclaf.parser import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    CommandSpec,
    CommandSpecInput,
    OptionSpec,
    OptionSpecInput,
    Parser,
    ParserConfigurationInput,
    ParseResult,
    PositionalSpec,
    PositionalSpecInput,
)
from aclaf.types import ParameterKind
from aclaf.validation import ValidatorRegistry
from aclaf.validation.parameter import default_parameter_validators

if TYPE_CHECKING:
    from collections.abc import Callable
    from unittest.mock import MagicMock

    from pytest_mock import MockerFixture

    from aclaf.console import Console
    from aclaf.execution import ContextInput, RuntimeCommandInput, RuntimeParameterInput
    from aclaf.logging import Logger
    from aclaf.parser._base import ParsedOption, ParsedPositional


@pytest.fixture
def string_buffer() -> StringIO:
    return StringIO()


@pytest.fixture
def option_spec_factory() -> "Callable[..., OptionSpec]":
    def factory(*names: str, **kwargs: Unpack[OptionSpecInput]) -> "OptionSpec":
        long = [n for n in names if len(n) > 1]
        long += ["option"] if not long else []
        short = [n for n in names if len(n) == 1]
        short += ["o"] if not short else []
        return OptionSpec(
            name=kwargs.get("name", "option"),
            arity=kwargs.get("arity", EXACTLY_ONE_ARITY),
            is_flag=kwargs.get("is_flag", False),
            long=frozenset(long),
            short=frozenset(short),
            truthy_flag_values=kwargs.get("truthy_flag_values"),
            falsey_flag_values=kwargs.get("falsey_flag_values"),
            const_value=kwargs.get("const_value"),
            flatten_values=kwargs.get("flatten_values", False),
        )

    return factory


@pytest.fixture
def option_spec(option_spec_factory: "Callable[..., OptionSpec]") -> "OptionSpec":
    return option_spec_factory()


@pytest.fixture
def positional_spec_factory() -> "Callable[..., PositionalSpec]":
    def factory(**kwargs: Unpack[PositionalSpecInput]) -> "PositionalSpec":
        return PositionalSpec(
            name=kwargs.get("name", "positional"),
            arity=kwargs.get("arity", EXACTLY_ONE_ARITY),
        )

    return factory


@pytest.fixture
def positional_spec(
    positional_spec_factory: "Callable[..., PositionalSpec]",
) -> "PositionalSpec":
    return positional_spec_factory()


@pytest.fixture
def exactly_one_positional_spec(
    positional_spec_factory: "Callable[..., PositionalSpec]",
) -> "PositionalSpec":
    return positional_spec_factory(name="exactly_one", arity=EXACTLY_ONE_ARITY)


@pytest.fixture
def one_or_more_positional_spec(
    positional_spec_factory: "Callable[..., PositionalSpec]",
) -> "PositionalSpec":
    return positional_spec_factory(name="one_or_more", arity=ONE_OR_MORE_ARITY)


@pytest.fixture
def zero_or_more_positional_spec(
    positional_spec_factory: "Callable[..., PositionalSpec]",
) -> "PositionalSpec":
    return positional_spec_factory(name="zero_or_more", arity=ZERO_OR_MORE_ARITY)


@pytest.fixture
def zero_or_one_positional_spec(
    positional_spec_factory: "Callable[..., PositionalSpec]",
) -> "PositionalSpec":
    return positional_spec_factory(name="zero_or_one", arity=ZERO_OR_ONE_ARITY)


@pytest.fixture
def command_spec_factory() -> "Callable[..., CommandSpec]":
    def factory(**kwargs: Unpack[CommandSpecInput]) -> CommandSpec:
        return CommandSpec(
            name=kwargs.get("name", "test"),
            aliases=kwargs.get("aliases", frozenset()),
            options=kwargs.get("options", {}),
            positionals=kwargs.get("positionals", {}),
            subcommands=kwargs.get("subcommands", {}),
            case_insensitive_aliases=kwargs.get("case_insensitive_aliases", False),
            case_insensitive_options=kwargs.get("case_insensitive_options", False),
            flatten_option_values=kwargs.get("flatten_option_values", False),
        )

    return factory


@pytest.fixture
def command_spec(command_spec_factory: "Callable[..., CommandSpec]") -> CommandSpec:
    return command_spec_factory()


@pytest.fixture
def parser_factory() -> "Callable[..., Parser]":
    def factory(
        spec: "CommandSpec", **kwargs: Unpack[ParserConfigurationInput]
    ) -> Parser:
        return Parser(spec, **kwargs)

    return factory


@pytest.fixture
def parse_result_factory() -> "Callable[..., ParseResult]":
    def factory(  # noqa: PLR0913
        command: str | None,
        alias: str | None = None,
        options: dict[str, "ParsedOption"] | None = None,
        positionals: dict[str, "ParsedPositional"] | None = None,
        extra_args: tuple[str, ...] | None = None,
        subcommand: "ParseResult | None" = None,
    ) -> ParseResult:
        return ParseResult(
            command=command or "test",
            alias=alias,
            options=options or {},
            positionals=positionals or {},
            extra_args=extra_args or (),
            subcommand=subcommand,
        )

    return factory


@pytest.fixture
def converters() -> ConverterRegistry:
    return ConverterRegistry()


@pytest.fixture
def validators() -> ValidatorRegistry:
    """Parameter validator registry for backward compatibility."""
    return default_parameter_validators()


@pytest.fixture
def parameter_validators() -> ValidatorRegistry:
    """Provide a ValidatorRegistry for parameter validation testing."""
    return default_parameter_validators()


@pytest.fixture
def empty_command_function() -> "Callable[[], None]":
    def command_function() -> None:
        pass

    return command_function


@pytest.fixture
def runtime_parameter_factory() -> "Callable[..., RuntimeParameter]":
    def factory(**kwargs: Unpack["RuntimeParameterInput"]) -> RuntimeParameter:
        return RuntimeParameter(
            name=kwargs.get("name", "option"),
            kind=kwargs.get("kind", ParameterKind.OPTION),
            value_type=kwargs.get("value_type", str),
            arity=kwargs.get("arity", EXACTLY_ONE_ARITY),
            accumulation_mode=kwargs.get("accumulation_mode"),
            const_value=kwargs.get("const_value"),
            converter=kwargs.get("converter"),
            default=kwargs.get("default"),
            default_factory=kwargs.get("default_factory"),
            falsey_flag_values=kwargs.get("falsey_flag_values", ()),
            flatten_values=kwargs.get("flatten_values", False),
            help=kwargs.get("help", ""),
            is_flag=kwargs.get("is_flag", False),
            is_required=kwargs.get("is_required", False),
            long=kwargs.get("long", ()),
            metadata=kwargs.get("metadata", ()),
            negation_words=kwargs.get("negation_words"),
            short=kwargs.get("short", ()),
            truthy_flag_values=kwargs.get("truthy_flag_values"),
            validators=kwargs.get("validators", ()),
        )

    return factory


@pytest.fixture
def runtime_option_factory(
    runtime_parameter_factory: "Callable[..., RuntimeParameter]",
) -> "Callable[..., RuntimeParameter]":
    def factory(**kwargs: Unpack["RuntimeParameterInput"]) -> RuntimeParameter:
        return runtime_parameter_factory(
            **{
                **kwargs,
                "kind": ParameterKind.OPTION,
                "name": kwargs.get("name", "opt"),
            },
        )

    return factory


@pytest.fixture
def runtime_option(
    runtime_option_factory: "Callable[..., RuntimeParameter]",
) -> RuntimeParameter:
    return runtime_option_factory()


@pytest.fixture
def runtime_flag_factory(
    runtime_option_factory: "Callable[..., RuntimeParameter]",
) -> "Callable[..., RuntimeParameter]":
    def factory(**kwargs: Unpack["RuntimeParameterInput"]) -> RuntimeParameter:
        return runtime_option_factory(
            **{**kwargs, "is_flag": True},
        )

    return factory


@pytest.fixture
def runtime_flag(
    runtime_flag_factory: "Callable[..., RuntimeParameter]",
) -> RuntimeParameter:
    return runtime_flag_factory()


@pytest.fixture
def runtime_positional_factory(
    runtime_parameter_factory: "Callable[..., RuntimeParameter]",
) -> "Callable[..., RuntimeParameter]":
    def factory(**kwargs: Unpack["RuntimeParameterInput"]) -> RuntimeParameter:
        return runtime_parameter_factory(
            **{
                **kwargs,
                "kind": ParameterKind.POSITIONAL,
                "name": kwargs.get("name", "pos"),
            },
        )

    return factory


@pytest.fixture
def runtime_positional(
    runtime_positional_factory: "Callable[..., RuntimeParameter]",
) -> RuntimeParameter:
    return runtime_positional_factory()


@pytest.fixture
def runtime_command_factory(
    converters: ConverterRegistry,
    logger: "Logger",
    validators: ValidatorRegistry,
    empty_command_function: "Callable[[], None]",
) -> "Callable[..., RuntimeCommand]":
    def factory(**kwargs: Unpack["RuntimeCommandInput"]) -> RuntimeCommand:
        return RuntimeCommand(
            aliases=kwargs.get("aliases", ()),
            converters=converters,
            is_async=kwargs.get("is_async", False),
            logger=logger,
            name=kwargs.get("name", "test"),
            parameters=kwargs.get("parameters", {}),
            parser_config=kwargs.get("parser_config"),
            run_func=kwargs.get("run_func", empty_command_function),
            parameter_validators=validators,
        )

    return factory


@pytest.fixture
def runtime_command(
    runtime_command_factory: "Callable[..., RuntimeCommand]",
) -> RuntimeCommand:
    return runtime_command_factory()


@pytest.fixture
def context_factory(
    console: "Console",
    logger: "Logger",
    parser_result_factory: "Callable[..., ParseResult]",
) -> "Callable[..., Context]":
    def factory(**kwargs: Unpack["ContextInput"]) -> Context:
        return Context(
            command=kwargs.get("command", "test"),
            command_path=kwargs.get("command_path", ("test",)),
            console=kwargs.get("console", console),
            console_param=kwargs.get("console_param"),
            context_param=kwargs.get("context_param"),
            errors=kwargs.get("errors", {}),
            is_async=kwargs.get("is_async", False),
            logger=kwargs.get("logger", logger),
            logger_param=kwargs.get("logger_param"),
            parameter_sources=kwargs.get("parameter_sources", {}),
            parameters=kwargs.get("parameters", {}),
            parent=kwargs.get("parent"),
            parse_result=kwargs.get("parse_result", parser_result_factory("test")),
        )

    return factory


@pytest.fixture
def context(
    context_factory: "Callable[..., Context]",
) -> Context:
    return context_factory()


@pytest.fixture
def mock_converters(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=ConverterRegistry)


@pytest.fixture
def mock_validators(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=ValidatorRegistry)


@pytest.fixture
def mock_runtime_parameter(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=RuntimeParameter)


@pytest.fixture
def mock_runtime_command(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=RuntimeCommand)
