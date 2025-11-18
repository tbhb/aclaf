import pytest

from aclaf import EMPTY_COMMAND_FUNCTION, Command
from aclaf.registration import (
    CommandFunctionAlreadyDefinedError,
    DuplicateCommandError,
)


class TestCommandMount:
    def test_mount_adds_subcommand(self):
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        _ = parent.mount(child)

        assert "child" in parent.subcommands
        assert parent.subcommands["child"] is child

    def test_mount_sets_parent_command(self):
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        _ = parent.mount(child)

        assert child.parent_command is parent

    def test_mount_sets_root_command(self):
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        _ = parent.mount(child)

        assert child.root_command is parent

    def test_mount_sets_is_mounted_flag(self):
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        assert child.is_mounted is False
        _ = parent.mount(child)
        assert child.is_mounted is True

    def test_mount_with_custom_name(self):
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        _ = parent.mount(child, name="custom")

        assert "custom" in parent.subcommands
        assert child.name == "custom"

    def test_mount_preserves_root_in_chain(self):
        root = Command(name="root")
        mid = Command(name="mid", run_func=EMPTY_COMMAND_FUNCTION)
        leaf = Command(name="leaf", run_func=EMPTY_COMMAND_FUNCTION)

        _ = root.mount(mid)
        _ = mid.mount(leaf)

        assert mid.root_command is root
        assert leaf.root_command is root

    def test_mount_duplicate_raises_error(self):
        parent = Command(name="parent")
        child1 = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        child2 = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        _ = parent.mount(child1)

        with pytest.raises(DuplicateCommandError, match="child"):
            _ = parent.mount(child2)

    def test_mount_ignore_existing_overwrites_existing(self):
        parent = Command(name="parent")
        child1 = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        child2 = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        _ = parent.mount(child1)
        _ = parent.mount(child2, ignore_existing=True)

        assert parent.subcommands["child"] is child2

    def test_mount_returns_command(self):
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        result = parent.mount(child)

        assert result is child


class TestCommandDecorator:
    def test_command_decorator_creates_subcommand(self):
        parent = Command(name="parent")

        def child():
            pass

        result = parent.command()(child)

        assert "child" in parent.subcommands
        assert parent.subcommands["child"].name == "child"
        assert parent.subcommands["child"].run_func is child
        assert result is parent.subcommands["child"]

    def test_command_decorator_with_name(self):
        parent = Command(name="parent")

        @parent.command(name="custom")
        def child():  # pyright: ignore[reportUnusedFunction]
            pass

        assert "custom" in parent.subcommands
        assert parent.subcommands["custom"].name == "custom"

    def test_command_decorator_with_aliases(self):
        parent = Command(name="parent")

        child = parent.command("child", aliases=("c", "ch"))(EMPTY_COMMAND_FUNCTION)

        assert child.aliases == ("c", "ch")

    def test_command_decorator_sets_parent_command(self):
        parent = Command(name="parent")

        child = parent.command("child")(EMPTY_COMMAND_FUNCTION)

        assert child.parent_command is parent

    def test_command_decorator_sets_root_command(self):
        parent = Command(name="parent")

        child = parent.command("child")(EMPTY_COMMAND_FUNCTION)

        assert child.root_command is parent

    def test_command_decorator_inherits_parser_config(self):
        config = object()
        parent = Command(
            name="parent",
            parser_config=config,  # pyright: ignore[reportArgumentType]
        )

        child = parent.command("child")(EMPTY_COMMAND_FUNCTION)

        assert child.parser_config is config

    def test_command_decorator_returns_command(self):
        parent = Command(name="parent")

        result = parent.command("child")(EMPTY_COMMAND_FUNCTION)

        assert isinstance(result, Command)
        assert result.name == "child"

    def test_nested_command_decorators(self):
        root = Command(name="root")

        _ = root.command("mid")(EMPTY_COMMAND_FUNCTION)
        _ = root.subcommands["mid"].command("leaf")(EMPTY_COMMAND_FUNCTION)

        assert "mid" in root.subcommands
        assert "leaf" in root.subcommands["mid"].subcommands
        assert root.subcommands["mid"].subcommands["leaf"].root_command is root


class TestHandlerDecorator:
    def test_handler_decorator_sets_run_func(self):
        cmd = Command(name="test")
        handler = EMPTY_COMMAND_FUNCTION

        _ = cmd.handler()(handler)

        assert cmd.run_func is handler

    def test_handler_decorator_with_name(self):
        cmd = Command(name="placeholder")

        _ = cmd.handler(name="custom")(EMPTY_COMMAND_FUNCTION)

        assert cmd.name == "custom"

    def test_handler_decorator_with_aliases(self):
        cmd = Command(name="test")

        _ = cmd.handler(aliases=("t", "tst"))(EMPTY_COMMAND_FUNCTION)

        assert cmd.aliases == ("t", "tst")

    def test_handler_decorator_returns_command(self):
        cmd = Command(name="test", run_func=EMPTY_COMMAND_FUNCTION)

        result = cmd
        assert isinstance(result, Command)

    def test_handler_decorator_detects_async(self):
        cmd = Command(name="test")

        @cmd.handler()
        async def handler():  # pyright: ignore[reportUnusedFunction]
            pass

        assert cmd.is_async is True

    def test_handler_decorator_already_defined_raises_error(self):
        cmd = Command(name="test", run_func=EMPTY_COMMAND_FUNCTION)

        with pytest.raises(CommandFunctionAlreadyDefinedError):
            _ = cmd.handler()(EMPTY_COMMAND_FUNCTION)

    def test_handler_preserves_existing_name(self):
        cmd = Command(name="original")

        def my_handler():
            pass

        _ = cmd.handler()(my_handler)

        assert cmd.name == "original"


class TestSubcommandHierarchy:
    def test_single_level_hierarchy(self):
        cmd = Command(name="root")

        assert cmd.parent_command is None
        assert cmd.root_command is None

    def test_two_level_hierarchy(self):
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        _ = parent.mount(child)

        assert child.parent_command is parent
        assert child.root_command is parent
        assert parent.parent_command is None
        assert parent.root_command is None

    def test_three_level_hierarchy(self):
        root = Command(name="root")
        mid = Command(name="mid", run_func=EMPTY_COMMAND_FUNCTION)
        leaf = Command(name="leaf", run_func=EMPTY_COMMAND_FUNCTION)

        _ = root.mount(mid)
        _ = mid.mount(leaf)

        assert leaf.parent_command is mid
        assert leaf.root_command is root
        assert mid.parent_command is root
        assert mid.root_command is root
        assert root.parent_command is None
        assert root.root_command is None

    def test_conversion_preserves_hierarchy(self):
        root = Command(name="root", run_func=EMPTY_COMMAND_FUNCTION)
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        _ = root.mount(child)
        final = root.to_runtime_command()

        assert "child" in final.subcommands
        assert final.subcommands["child"].name == "child"
