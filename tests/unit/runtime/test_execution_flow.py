"""Tests for basic command execution flow (without parameter injection).

This module tests the execution flow through FinalCommand.invoke(), dispatch(),
and dispatch_async() methods. Note that full parameter injection is not yet
implemented, so these tests focus on command routing and async detection.
"""

from typing import TYPE_CHECKING

import pytest

from aclaf import Context, RuntimeCommand
from aclaf.parser import ParseResult

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from aclaf.console._basic import BasicConsole


class TestSyncDispatch:
    """Test synchronous command dispatch."""

    def test_dispatch_calls_run_func(self, mock_responder: "MagicMock"):
        """dispatch() calls the run function."""
        called: list[bool] = []

        def handler():
            called.append(True)

        cmd = RuntimeCommand(name="test", run_func=handler)

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        cmd.dispatch(ctx, mock_responder)

        assert len(called) == 1

    def test_dispatch_with_no_subcommand(self, mock_responder: "MagicMock"):
        """dispatch() works when no subcommand is invoked."""
        called: list[str] = []

        def handler():
            called.append("parent")

        cmd = RuntimeCommand(name="parent", run_func=handler)

        parse_result = ParseResult(command="parent", options={}, positionals={})
        ctx = Context(
            command="parent", command_path=("parent",), parse_result=parse_result
        )

        cmd.dispatch(ctx, mock_responder)

        assert called == ["parent"]

    def test_dispatch_with_subcommand(self, mock_responder: "MagicMock"):
        """dispatch() dispatches to subcommand."""
        called: list[str] = []

        def parent_handler():
            called.append("parent")

        def child_handler():
            called.append("child")

        child = RuntimeCommand(name="child", run_func=child_handler)
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
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

        parent.dispatch(ctx, mock_responder)

        assert called == ["parent", "child"]

    def test_dispatch_calls_child_and_parent_in_order(
        self, mock_responder: "MagicMock"
    ):
        """dispatch() calls parent then child in correct order."""
        called: list[tuple[str, int]] = []

        def parent_handler():
            called.append(("parent", len(called)))

        def child_handler():
            called.append(("child", len(called)))

        child = RuntimeCommand(name="child", run_func=child_handler)
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
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

        parent.dispatch(parent_ctx, mock_responder)

        assert len(called) == 2
        assert called[0] == ("parent", 0)
        assert called[1] == ("child", 1)


class TestAsyncDispatch:
    """Test asynchronous command dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_async_calls_async_run_func(
        self, mock_responder: "MagicMock"
    ):
        """dispatch_async() calls async run function."""
        called: list[bool] = []

        async def handler():
            called.append(True)

        cmd = RuntimeCommand(name="test", run_func=handler, is_async=True)

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(
            command="test",
            command_path=("test",),
            parse_result=parse_result,
            is_async=True,
        )

        await cmd.dispatch_async(ctx, mock_responder)

        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_dispatch_async_calls_sync_run_func_if_not_async(
        self, mock_responder: "MagicMock"
    ):
        """dispatch_async() can call sync run function."""
        called: list[bool] = []

        def handler():
            called.append(True)

        cmd = RuntimeCommand(name="test", run_func=handler, is_async=False)

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        await cmd.dispatch_async(ctx, mock_responder)

        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_dispatch_async_with_subcommand(self, mock_responder: "MagicMock"):
        """dispatch_async() dispatches to subcommand."""
        called: list[str] = []

        async def parent_handler():
            called.append("parent")

        async def child_handler():
            called.append("child")

        child = RuntimeCommand(name="child", run_func=child_handler, is_async=True)
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
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

        await parent.dispatch_async(ctx, mock_responder)

        assert called == ["parent", "child"]

    @pytest.mark.asyncio
    async def test_dispatch_async_mixed_sync_async(self, mock_responder: "MagicMock"):
        """dispatch_async() handles mixed sync/async commands."""
        called: list[str] = []

        def parent_handler():
            called.append("parent")

        async def child_handler():
            called.append("child")

        child = RuntimeCommand(name="child", run_func=child_handler, is_async=True)
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
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

        await parent.dispatch_async(ctx, mock_responder)

        assert called == ["parent", "child"]


class TestSubcommandContextCreation:
    """Test context creation for subcommands."""

    def test_prepare_subcommand_dispatch_returns_none_without_subcommand(self):
        """_prepare_subcommand_dispatch returns None when no subcommand."""
        cmd = RuntimeCommand(name="test", run_func=lambda: None)

        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        result = cmd._prepare_subcommand_dispatch(ctx)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

        assert result is None

    def test_prepare_subcommand_dispatch_returns_subcommand_and_context(self):
        """_prepare_subcommand_dispatch returns subcommand and its context."""
        child = RuntimeCommand(name="child", run_func=lambda: None)
        parent = RuntimeCommand(
            name="parent",
            run_func=lambda: None,
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
        self, test_console: "BasicConsole"
    ) -> None:
        """Subcommand context inherits console from parent."""
        child = RuntimeCommand(name="child", run_func=lambda: None)
        parent = RuntimeCommand(
            name="parent",
            run_func=lambda: None,
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
            console=test_console,
        )

        result = parent._prepare_subcommand_dispatch(parent_ctx)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

        assert result is not None
        _, subcommand_ctx = result
        assert subcommand_ctx.console is test_console
