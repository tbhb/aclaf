from typing import TYPE_CHECKING

import pytest

from aclaf.conversion import ConverterRegistry
from aclaf.execution import Context, RuntimeCommand
from aclaf.parser import ParseResult
from aclaf.validation import ValidatorRegistry

if TYPE_CHECKING:
    from aclaf.console._basic import BasicConsole


class TestSyncDispatch:
    def test_dispatch_calls_run_func(self):
        called: list[bool] = []

        def handler():
            called.append(True)

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        cmd.dispatch(ctx)

        assert len(called) == 1

    def test_dispatch_with_no_subcommand(self):
        called: list[str] = []

        def handler():
            called.append("parent")

        cmd = RuntimeCommand(
            name="parent",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
        )

        parse_result = ParseResult(command="parent", options={}, positionals={})
        ctx = Context(
            command="parent", command_path=("parent",), parse_result=parse_result
        )

        cmd.dispatch(ctx)

        assert called == ["parent"]

    def test_dispatch_with_subcommand(self):
        called: list[str] = []

        def parent_handler():
            called.append("parent")

        def child_handler():
            called.append("child")

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
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="child", options={}, positionals={}),
        )
        ctx = Context(
            command="parent", command_path=("parent",), parse_result=parse_result
        )

        parent.dispatch(ctx)

        assert called == ["parent", "child"]

    def test_dispatch_calls_child_and_parent_in_order(self):
        called: list[tuple[str, int]] = []

        def parent_handler():
            called.append(("parent", len(called)))

        def child_handler():
            called.append(("child", len(called)))

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
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="child", options={}, positionals={}),
        )
        parent_ctx = Context(
            command="parent", command_path=("parent",), parse_result=parse_result
        )

        parent.dispatch(parent_ctx)

        assert len(called) == 2
        assert called[0] == ("parent", 0)
        assert called[1] == ("child", 1)


class TestAsyncDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_async_calls_async_run_func(self):
        called: list[bool] = []

        async def handler():
            called.append(True)

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            is_async=True,
        )

        await cmd.dispatch_async(ctx)

        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_dispatch_async_calls_sync_run_func_if_not_async(self):
        called: list[bool] = []

        def handler():
            called.append(True)

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        await cmd.dispatch_async(ctx)

        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_dispatch_async_with_subcommand(self):
        called: list[str] = []

        async def parent_handler():
            called.append("parent")

        async def child_handler():
            called.append("child")

        child = RuntimeCommand(
            name="child",
            run_func=child_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
            subcommands={"child": child},
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
            is_async=True,
        )

        await parent.dispatch_async(ctx)

        assert called == ["parent", "child"]

    @pytest.mark.asyncio
    async def test_dispatch_async_mixed_sync_async(self):
        called: list[str] = []

        def parent_handler():
            called.append("parent")

        async def child_handler():
            called.append("child")

        child = RuntimeCommand(
            name="child",
            run_func=child_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
            subcommands={"child": child},
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
            is_async=True,
        )

        await parent.dispatch_async(ctx)

        assert called == ["parent", "child"]

    @pytest.mark.asyncio
    async def test_async_command_returning_sync_value_raises_type_error(self):
        def sync_handler():
            return 42

        cmd = RuntimeCommand(
            name="test",
            run_func=sync_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            is_async=True,
        )

        with pytest.raises(
            TypeError, match="Async command returned non-awaitable result"
        ):
            await cmd.dispatch_async(ctx)


class TestSubcommandContextCreation:
    def test_prepare_subcommand_dispatch_returns_none_without_subcommand(
        self,
        converters: "ConverterRegistry",
        parameter_validators: "ValidatorRegistry",
    ):
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
        )

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        result = cmd._prepare_subcommand_dispatch(ctx)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

        assert result is None

    def test_prepare_subcommand_dispatch_returns_subcommand_and_context(
        self,
        converters: "ConverterRegistry",
        parameter_validators: "ValidatorRegistry",
    ):
        child = RuntimeCommand(
            name="child",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            subcommands={"child": child},
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="child", options={}, positionals={}),
        )
        parent_ctx = Context(
            command="parent", command_path=("parent",), parse_result=parse_result
        )

        result = parent._prepare_subcommand_dispatch(parent_ctx)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

        assert result is not None
        subcommand, subcommand_ctx = result
        assert subcommand is child
        assert subcommand_ctx.command == "child"
        assert subcommand_ctx.parent is parent_ctx

    def test_subcommand_context_inherits_console(
        self,
        console: "BasicConsole",
        converters: "ConverterRegistry",
        parameter_validators: "ValidatorRegistry",
    ) -> None:
        child = RuntimeCommand(
            name="child",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            subcommands={"child": child},
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="child", options={}, positionals={}),
        )
        parent_ctx = Context(
            command="parent",
            command_path=("parent",),
            parse_result=parse_result,
            console=console,
        )

        result = parent._prepare_subcommand_dispatch(parent_ctx)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

        assert result is not None
        _, subcommand_ctx = result
        assert subcommand_ctx.console is console
