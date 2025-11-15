"""Tests for Context creation and basic properties.

This module tests the Context dataclass initialization, immutability,
and basic property access.
"""

from unittest.mock import MagicMock

from aclaf import ParameterValueType
from aclaf._context import Context
from aclaf.parser import ParseResult


class TestContextCreation:
    """Test Context initialization and basic properties."""

    def test_minimal_context_creation(self):
        """Context can be created with minimal required fields."""
        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", parse_result=parse_result)

        assert ctx.command == "test"
        assert ctx.parse_result is parse_result
        assert ctx.params == {}
        assert ctx.param_sources == {}
        assert ctx.parent is None
        assert ctx.is_async is False
        assert ctx.console is None

    def test_context_with_all_fields(self, mock_console: "MagicMock") -> None:
        """Context can be created with all fields specified."""
        parent_result = ParseResult(command="parent", options={}, positionals={})
        parent_ctx = Context(
            command="parent", command_path=("parent",), parse_result=parent_result
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        params: dict[str, ParameterValueType] = {"arg": "value"}
        param_sources = {"arg": "cli"}

        ctx = Context(
            command="child",
            command_path=("parent", "child"),
            parse_result=child_result,
            parameters=params,
            parameter_sources=param_sources,
            parent=parent_ctx,
            is_async=True,
            console=mock_console,
        )

        assert ctx.command == "child"
        assert ctx.command_path == ("parent", "child")
        assert ctx.parse_result is child_result
        assert ctx.parameters == params
        assert ctx.parameter_sources == param_sources
        assert ctx.parent is parent_ctx
        assert ctx.is_async is True
        assert ctx.console is test_console

    def test_is_root_true_without_parent(self):
        """is_root returns True when parent is None."""
        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        assert ctx.is_root is True

    def test_is_root_false_with_parent(self):
        """is_root returns False when parent exists."""
        parent_result = ParseResult(command="parent", options={}, positionals={})
        parent_ctx = Context(
            command="parent", command_path=("parent",), parse_result=parent_result
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            command_path=("parent", "child"),
            parse_result=child_result,
            parent=parent_ctx,
        )

        assert child_ctx.is_root is False
        assert parent_ctx.is_root is True
