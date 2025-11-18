from typing import TYPE_CHECKING

from aclaf.execution import Context
from aclaf.parser import ParseResult

if TYPE_CHECKING:
    from aclaf.console import Console


class TestContextHierarchy:
    def test_single_level_hierarchy(self):
        parse_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root", command_path=("root",), parse_result=parse_result
        )

        assert root_ctx.parent is None
        assert root_ctx.is_root is True

    def test_two_level_hierarchy(self):
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root", command_path=("root",), parse_result=root_result
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            command_path=("root", "child"),
            parse_result=child_result,
            parent=root_ctx,
        )

        assert child_ctx.parent is root_ctx
        assert child_ctx.is_root is False
        assert root_ctx.is_root is True

    def test_three_level_hierarchy(self):
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root", command_path=("root",), parse_result=root_result
        )

        mid_result = ParseResult(command="mid", options={}, positionals={})
        mid_ctx = Context(
            command="mid",
            command_path=("root", "mid"),
            parse_result=mid_result,
            parent=root_ctx,
        )

        leaf_result = ParseResult(command="leaf", options={}, positionals={})
        leaf_ctx = Context(
            command="leaf",
            command_path=("root", "mid", "leaf"),
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
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root", command_path=("root",), parse_result=root_result
        )

        mid_result = ParseResult(command="mid", options={}, positionals={})
        mid_ctx = Context(
            command="mid",
            command_path=("root", "mid"),
            parse_result=mid_result,
            parent=root_ctx,
        )

        leaf_result = ParseResult(command="leaf", options={}, positionals={})
        leaf_ctx = Context(
            command="leaf",
            command_path=("root", "mid", "leaf"),
            parse_result=leaf_result,
            parent=mid_ctx,
        )

        current = leaf_ctx
        chain: list[str] = []
        while current is not None:
            chain.append(current.command)
            current = current.parent

        assert chain == ["leaf", "mid", "root"]

    def test_console_inheritance(self, console: "Console") -> None:
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root",
            command_path=("root",),
            parse_result=root_result,
            console=console,
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            command_path=("root", "child"),
            parse_result=child_result,
            parent=root_ctx,
            console=console,  # Should inherit same console
        )

        assert root_ctx.console is console
        assert child_ctx.console is console
        assert root_ctx.console is child_ctx.console

    def test_params_isolated_between_contexts(self):
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root",
            command_path=("root",),
            parse_result=root_result,
            parameters={"root_param": "root_value"},
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            command_path=("root", "child"),
            parse_result=child_result,
            parent=root_ctx,
            parameters={"child_param": "child_value"},
        )

        assert root_ctx.parameters == {"root_param": "root_value"}
        assert child_ctx.parameters == {"child_param": "child_value"}

    def test_async_flag_independent_per_context(self):
        root_result = ParseResult(command="root", options={}, positionals={})
        root_ctx = Context(
            command="root",
            command_path=("root",),
            parse_result=root_result,
            is_async=False,
        )

        child_result = ParseResult(command="child", options={}, positionals={})
        child_ctx = Context(
            command="child",
            command_path=("root", "child"),
            parse_result=child_result,
            parent=root_ctx,
            is_async=True,
        )

        assert root_ctx.is_async is False
        assert child_ctx.is_async is True
