from typing import TYPE_CHECKING

import pytest

from aclaf.console import MockConsole
from aclaf.conversion import ConverterRegistry
from aclaf.execution import (
    Context,
    RuntimeCommand,
    RuntimeParameter,
)
from aclaf.logging import MockLogger
from aclaf.parser import EXACTLY_ONE_ARITY, ParsedOption, ParseResult
from aclaf.types import ParameterKind
from aclaf.validation import ValidatorRegistry

if TYPE_CHECKING:
    from aclaf.console import Console
    from aclaf.logging import Logger


class TestContextParameterInjection:
    def test_context_param_injected_to_run_func(self):
        received_context: Context | None = None

        def handler(ctx: "Context"):
            nonlocal received_context
            received_context = ctx

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            context_param="ctx",
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        cmd.dispatch(ctx)

        assert received_context is ctx

    def test_context_param_not_injected_when_param_name_none(self):
        call_args: dict[str, object] | None = None

        def handler(**kwargs: object):
            nonlocal call_args
            call_args = kwargs

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            context_param=None,
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        cmd.dispatch(ctx)

        assert call_args is not None
        assert "ctx" not in call_args


class TestConsoleParameterInjection:
    def test_console_param_injected_to_run_func(self):
        received_console: Console | None = None
        test_console = MockConsole()

        def handler(con: "Console"):
            nonlocal received_console
            received_console = con

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            console_param="con",
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            console=test_console,
        )

        cmd.dispatch(ctx)

        assert received_console is test_console

    def test_console_param_not_injected_when_param_name_none(self):
        call_args: dict[str, object] | None = None

        def handler(**kwargs: object):
            nonlocal call_args
            call_args = kwargs

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            console_param=None,
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        cmd.dispatch(ctx)

        assert call_args is not None
        assert "con" not in call_args


class TestLoggerParameterInjection:
    def test_logger_param_injected_to_run_func(self):
        received_logger: Logger | None = None
        test_logger = MockLogger()

        def handler(log: "Logger"):
            nonlocal received_logger
            received_logger = log

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            logger_param="log",
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            logger=test_logger,
        )

        cmd.dispatch(ctx)

        assert received_logger is test_logger

    def test_logger_param_not_injected_when_param_name_none(self):
        call_args: dict[str, object] | None = None

        def handler(**kwargs: object):
            nonlocal call_args
            call_args = kwargs

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            logger_param=None,
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        cmd.dispatch(ctx)

        assert call_args is not None
        assert "log" not in call_args


class TestMultipleSpecialParametersInjection:
    def test_all_special_params_injected_together(self):
        received_context: Context | None = None
        received_console: Console | None = None
        received_logger: Logger | None = None
        test_console = MockConsole()
        test_logger = MockLogger()

        def handler(ctx: Context, con: "Console", log: "Logger"):
            nonlocal received_context, received_console, received_logger
            received_context = ctx
            received_console = con
            received_logger = log

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            context_param="ctx",
            console_param="con",
            logger_param="log",
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            console=test_console,
            logger=test_logger,
        )

        cmd.dispatch(ctx)

        assert received_context is ctx
        assert received_console is test_console
        assert received_logger is test_logger

    def test_partial_special_params_injected(self):
        received_args: dict[str, object] | None = None
        test_console = MockConsole()

        def handler(**kwargs: object):
            nonlocal received_args
            received_args = kwargs

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            context_param=None,
            console_param="con",
            logger_param=None,
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            console=test_console,
        )

        cmd.dispatch(ctx)

        assert received_args is not None
        assert "con" in received_args
        assert received_args["con"] is test_console
        assert "ctx" not in received_args
        assert "log" not in received_args


class TestSpecialParamsMixedWithConvertedParams:
    def test_special_params_mixed_with_regular_parameters(self):
        received_args: dict[str, object] | None = None
        test_console = MockConsole()

        def handler(**kwargs: object):
            nonlocal received_args
            received_args = kwargs

        param = RuntimeParameter(
            name="value",
            kind=ParameterKind.OPTION,
            value_type=int,
            arity=EXACTLY_ONE_ARITY,
            long=("value",),
        )

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            parameters={"value": param},
            console_param="con",
        )

        parse_result = ParseResult(
            command="test",
            options={"value": ParsedOption(name="value", value="42")},
            positionals={},
        )

        parameters, conversion_errors = cmd._convert_parameters(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            parse_result, cmd.parameters
        )
        errors = cmd._validate_parameters(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            parameters, cmd.parameters, conversion_errors
        )

        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            console=test_console,
            parameters=parameters,
            errors=errors,
        )

        cmd.dispatch(ctx)

        assert received_args is not None
        assert "con" in received_args
        assert received_args["con"] is test_console
        assert "value" in received_args
        assert received_args["value"] == 42

    def test_special_params_do_not_override_converted_params(self):
        received_args: dict[str, object] | None = None

        def handler(**kwargs: object):
            nonlocal received_args
            received_args = kwargs

        param = RuntimeParameter(
            name="ctx",
            kind=ParameterKind.OPTION,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
        )

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            parameters={"ctx": param},
            context_param="ctx",
        )

        parse_result = ParseResult(
            command="test",
            options={"ctx": ParsedOption(name="ctx", value="user_value")},
            positionals={},
        )
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        cmd.dispatch(ctx)

        assert received_args is not None
        assert "ctx" in received_args
        assert isinstance(received_args["ctx"], Context)


class TestSpecialParamsWithSubcommands:
    def test_special_params_propagated_to_subcommands(self):
        received_parent_args: dict[str, object] | None = None
        received_child_args: dict[str, object] | None = None
        test_console = MockConsole()
        test_logger = MockLogger()

        def parent_handler(**kwargs: object):
            nonlocal received_parent_args
            received_parent_args = kwargs

        def child_handler(**kwargs: object):
            nonlocal received_child_args
            received_child_args = kwargs

        child = RuntimeCommand(
            name="child",
            run_func=child_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            subcommands={"child": child},
            console_param="con",
            logger_param="log",
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="child", options={}, positionals={}),
        )
        ctx = Context(
            command="parent",
            command_path=("parent",),
            parse_result=parse_result,
            console=test_console,
            logger=test_logger,
        )

        parent.dispatch(ctx)

        assert received_parent_args is not None
        assert "con" in received_parent_args
        assert "log" in received_parent_args
        assert received_parent_args["con"] is test_console
        assert received_parent_args["log"] is test_logger

        assert received_child_args is not None
        assert received_child_args == {}

    @pytest.mark.asyncio
    async def test_special_params_injected_in_async_dispatch(self):
        received_context: Context | None = None
        received_console: Console | None = None
        test_console = MockConsole()

        async def handler(ctx: Context, con: "Console"):
            nonlocal received_context, received_console
            received_context = ctx
            received_console = con

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
            context_param="ctx",
            console_param="con",
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            is_async=True,
            console=test_console,
        )

        await cmd.dispatch_async(ctx)

        assert received_context is ctx
        assert received_console is test_console
