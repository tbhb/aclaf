"""Tests for async detection logic.

This module tests FinalCommand.check_async() which determines whether
a command or its subcommands are async and require async execution.
"""

import pytest

from aclaf import RuntimeCommand
from aclaf.parser import ParseResult


class TestAsyncDetection:
    """Test async detection for commands."""

    def test_sync_command_returns_false(self):
        """Sync command returns False from check_async."""

        def handler():
            pass

        cmd = RuntimeCommand(name="test", run_func=handler, is_async=False)
        parse_result = ParseResult(command="test", options={}, positionals={})

        assert cmd.check_async(parse_result) is False

    def test_async_command_returns_true(self):
        """Async command returns True from check_async."""

        async def handler():
            pass

        cmd = RuntimeCommand(name="test", run_func=handler, is_async=True)
        parse_result = ParseResult(command="test", options={}, positionals={})

        assert cmd.check_async(parse_result) is True

    def test_sync_command_no_subcommand_returns_false(self):
        """Sync command without subcommand invocation returns False."""

        def handler():
            pass

        cmd = RuntimeCommand(name="test", run_func=handler, is_async=False)
        parse_result = ParseResult(
            command="test",
            options={},
            positionals={},
            subcommand=None,
        )

        assert cmd.check_async(parse_result) is False


class TestAsyncPropagationFromSubcommands:
    """Test async detection propagates from subcommands."""

    def test_sync_parent_with_async_subcommand(self):
        """Sync parent with async subcommand returns True."""

        def parent_handler():
            pass

        async def child_handler():
            pass

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

        assert parent.check_async(parse_result) is True

    def test_sync_parent_with_sync_subcommand(self):
        """Sync parent with sync subcommand returns False."""

        def parent_handler():
            pass

        def child_handler():
            pass

        child = RuntimeCommand(name="child", run_func=child_handler, is_async=False)
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

        assert parent.check_async(parse_result) is False

    def test_async_parent_returns_true_regardless_of_subcommand(self):
        """Async parent returns True even if subcommand is sync."""

        async def parent_handler():
            pass

        def child_handler():
            pass

        child = RuntimeCommand(name="child", run_func=child_handler, is_async=False)
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

        # Parent is async, so True regardless of child
        assert parent.check_async(parse_result) is True


class TestNestedAsyncPropagation:
    """Test async detection through multi-level command chains."""

    def test_three_level_async_in_leaf(self):
        """Async detection propagates through three-level chain."""

        def root_handler():
            pass

        def mid_handler():
            pass

        async def leaf_handler():
            pass

        leaf = RuntimeCommand(name="leaf", run_func=leaf_handler, is_async=True)
        mid = RuntimeCommand(
            name="mid",
            run_func=mid_handler,
            is_async=False,
            subcommands={"leaf": leaf},
        )
        root = RuntimeCommand(
            name="root",
            run_func=root_handler,
            is_async=False,
            subcommands={"mid": mid},
        )

        parse_result = ParseResult(
            command="root",
            options={},
            positionals={},
            subcommand=ParseResult(
                command="mid",
                options={},
                positionals={},
                subcommand=ParseResult(command="leaf", options={}, positionals={}),
            ),
        )

        assert root.check_async(parse_result) is True

    def test_three_level_all_sync(self):
        """All-sync three-level chain returns False."""

        def root_handler():
            pass

        def mid_handler():
            pass

        def leaf_handler():
            pass

        leaf = RuntimeCommand(name="leaf", run_func=leaf_handler, is_async=False)
        mid = RuntimeCommand(
            name="mid",
            run_func=mid_handler,
            is_async=False,
            subcommands={"leaf": leaf},
        )
        root = RuntimeCommand(
            name="root",
            run_func=root_handler,
            is_async=False,
            subcommands={"mid": mid},
        )

        parse_result = ParseResult(
            command="root",
            options={},
            positionals={},
            subcommand=ParseResult(
                command="mid",
                options={},
                positionals={},
                subcommand=ParseResult(command="leaf", options={}, positionals={}),
            ),
        )

        assert root.check_async(parse_result) is False


class TestAsyncDetectionErrorHandling:
    """Test error handling in async detection."""

    def test_unknown_subcommand_raises_error(self):
        """Unknown subcommand raises ValueError."""

        def handler():
            pass

        cmd = RuntimeCommand(name="parent", run_func=handler, subcommands={})

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="unknown", options={}, positionals={}),
        )

        with pytest.raises(ValueError, match="Unknown subcommand: unknown"):
            _ = cmd.check_async(parse_result)

    def test_missing_subcommand_in_registry(self):
        """Missing subcommand in registry raises ValueError."""

        def parent_handler():
            pass

        def child_handler():
            pass

        # Register "child" but parse result asks for "other"
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
            subcommand=ParseResult(command="other", options={}, positionals={}),
        )

        with pytest.raises(ValueError, match="Unknown subcommand: other"):
            _ = parent.check_async(parse_result)
