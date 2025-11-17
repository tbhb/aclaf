from typing import TYPE_CHECKING

from aclaf import Context, ParameterSource, ParameterSourceMapping
from aclaf.parser import ParseResult

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from aclaf import ParameterValueType


class TestContextCreation:
    def test_minimal_context_creation(self):
        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        assert ctx.command == "test"
        assert ctx.parse_result is parse_result
        assert ctx.parameters == {}
        assert ctx.parameter_sources == {}
        assert ctx.parent is None
        assert ctx.is_async is False
        assert ctx.console is None

    def test_context_with_all_fields(self, test_console: "MagicMock") -> None:
        parent_result = ParseResult(command="parent", options={}, positionals={})
        parent_ctx = Context(
            command="parent", command_path=("parent",), parse_result=parent_result
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        parameters: dict[str, ParameterValueType] = {"arg": "value"}
        parameter_sources: ParameterSourceMapping = {
            "arg": ParameterSource.COMMAND_LINE
        }

        ctx = Context(
            command="child",
            command_path=("parent", "child"),
            parse_result=child_result,
            parameters=parameters,
            parameter_sources=parameter_sources,
            parent=parent_ctx,
            is_async=True,
            console=test_console,
        )

        assert ctx.command == "child"
        assert ctx.command_path == ("parent", "child")
        assert ctx.parse_result is child_result
        assert ctx.parameters == parameters
        assert ctx.parameter_sources == parameter_sources
        assert ctx.parent is parent_ctx
        assert ctx.is_async is True
        assert ctx.console is test_console

    def test_is_root_true_without_parent(self):
        parse_result = ParseResult(command="test", options={}, positionals={})
        ctx = Context(command="test", command_path=("test",), parse_result=parse_result)

        assert ctx.is_root is True

    def test_is_root_false_with_parent(self):
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
