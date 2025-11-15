"""Tests for Context hierarchy and parent/child relationships.

This module tests Context parent-child relationships and traversal
through the context chain.
"""

from typing import TYPE_CHECKING

from aclaf._context import Context
from aclaf.parser import ParseResult

if TYPE_CHECKING:
    from aclaf.console._basic import BasicConsole


class TestContextHierarchy:
    """Test Context parent-child relationships."""

    def test_single_level_hierarchy(self):
        """Single context has no parent."""
        parse_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(command="root", parse_result=parse_result)

        assert root_ctx.parent is None
        assert root_ctx.is_root is True

    def test_two_level_hierarchy(self):
        """Child context correctly references parent."""
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(command="root", parse_result=root_result)

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            parse_result=child_result,
            parent=root_ctx,
        )

        assert child_ctx.parent is root_ctx
        assert child_ctx.is_root is False
        assert root_ctx.is_root is True

    def test_three_level_hierarchy(self):
        """Three-level context chain maintains correct relationships."""
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(command="root", parse_result=root_result)

        mid_result = ParseResult(command="mid", options={}, positionals={})
        mid_ctx = Context(
            command="mid",
            parse_result=mid_result,
            parent=root_ctx,
        )

        leaf_result = ParseResult(command="leaf", options={}, positionals={})
        leaf_ctx = Context(
            command="leaf",
            parse_result=leaf_result,
            parent=mid_ctx,
        )

        # Verify chain
        assert leaf_ctx.parent is mid_ctx
        assert mid_ctx.parent is root_ctx
        assert root_ctx.parent is None

        # Verify is_root
        assert leaf_ctx.is_root is False
        assert mid_ctx.is_root is False
        assert root_ctx.is_root is True

    def test_traversing_to_root(self):
        """Can traverse from child to root through parent chain."""
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(command="root", parse_result=root_result)

        mid_result = ParseResult(command="mid", options={}, positionals={})
        mid_ctx = Context(
            command="mid",
            parse_result=mid_result,
            parent=root_ctx,
        )

        leaf_result = ParseResult(command="leaf", options={}, positionals={})
        leaf_ctx = Context(
            command="leaf",
            parse_result=leaf_result,
            parent=mid_ctx,
        )

        # Traverse to root
        current = leaf_ctx
        chain = []
        while current is not None:
            chain.append(current.command)
            current = current.parent

        assert chain == ["leaf", "mid", "root"]

    def test_console_inheritance(self, test_console: "BasicConsole") -> None:
        """Console can be passed through context hierarchy."""
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root",
            parse_result=root_result,
            console=test_console,
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            parse_result=child_result,
            parent=root_ctx,
            console=test_console,  # Should inherit same console
        )

        assert root_ctx.console is test_console
        assert child_ctx.console is test_console
        assert root_ctx.console is child_ctx.console

    def test_params_isolated_between_contexts(self):
        """Params dicts are independent between parent and child."""
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root",
            parse_result=root_result,
            params={"root_param": "root_value"},
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            parse_result=child_result,
            parent=root_ctx,
            params={"child_param": "child_value"},
        )

        assert root_ctx.params == {"root_param": "root_value"}
        assert child_ctx.params == {"child_param": "child_value"}

        # Modifying child doesn't affect parent
        child_ctx.params["new"] = "value"
        assert "new" not in root_ctx.params

    def test_async_flag_independent_per_context(self):
        """is_async flag is independent for each context."""
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root",
            parse_result=root_result,
            is_async=False,
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            parse_result=child_result,
            parent=root_ctx,
            is_async=True,
        )

        assert root_ctx.is_async is False
        assert child_ctx.is_async is True
