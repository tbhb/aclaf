"""Tests for Command builder pattern.

This module tests the Command class which provides a mutable builder pattern
for constructing commands before conversion to immutable FinalCommand.
"""

import pytest

from aclaf import Command, RuntimeCommand


class TestCommandCreation:
    """Test Command builder initialization."""

    def test_minimal_command_creation(self):
        """Command can be created with just a name."""
        cmd = Command(name="test")

        assert cmd.name == "test"
        assert cmd.aliases == ()
        assert cmd.run_func is None
        assert cmd.parser_config is None
        assert cmd.parent_command is None
        assert cmd.root_command is None
        assert cmd.subcommands == {}
        assert cmd.context_param is None
        assert cmd.is_async is None
        assert cmd.is_mounted is False

    def test_command_with_aliases(self):
        """Command accepts aliases."""
        cmd = Command(name="test", aliases=("t", "tst"))

        assert cmd.aliases == ("t", "tst")

    def test_command_with_run_func(self):
        """Command accepts run function."""

        def handler():
            pass

        cmd = Command(name="test", run_func=handler)

        assert cmd.run_func is handler
        assert cmd.is_async is False  # Detected from non-async function

    def test_command_with_async_run_func(self):
        """Command detects async run function."""

        async def handler():
            pass

        cmd = Command(name="test", run_func=handler)

        assert cmd.run_func is handler
        assert cmd.is_async is True

    def test_command_name_validation(self):
        """Command validates name on creation."""
        # Valid names should work
        _ = Command(name="valid")
        _ = Command(name="valid-name")
        _ = Command(name="valid_name")

        # Invalid names should raise ValueError
        with pytest.raises(ValueError, match="Invalid command name"):
            _ = Command(name="")

        with pytest.raises(ValueError, match="Invalid command name"):
            _ = Command(name="invalid name")  # Space not allowed

    def test_repr_is_informative(self):
        """Command __repr__ is informative."""
        cmd = Command(name="test", aliases=("t",))
        repr_str = repr(cmd)

        assert "Command" in repr_str
        assert "name='test'" in repr_str


class TestCommandAsyncDetection:
    """Test async detection in Command builder."""

    def test_async_detection_for_sync_function(self):
        """is_async is False for sync function."""

        def handler():
            pass

        cmd = Command(name="test", run_func=handler)
        assert cmd.is_async is False

    def test_async_detection_for_async_function(self):
        """is_async is True for async function."""

        async def handler():
            pass

        cmd = Command(name="test", run_func=handler)
        assert cmd.is_async is True

    def test_async_detection_when_no_run_func(self):
        """is_async is None when no run function."""
        cmd = Command(name="test")
        assert cmd.is_async is None

    def test_async_detection_updated_when_run_func_set(self):
        """is_async is updated when run_func is set later."""

        async def handler():
            pass

        cmd = Command(name="test")
        assert cmd.is_async is None

        cmd.run_func = handler
        cmd.is_async = cmd._check_run_func_async()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        assert cmd.is_async is True


class TestCommandConversion:
    """Test Command to FinalCommand conversion."""

    def test_to_command_creates_final_command(self):
        """to_command() creates FinalCommand."""

        def handler():
            pass

        cmd = Command(name="test", run_func=handler, aliases=("t",))
        final = cmd.to_runtime_command()

        assert isinstance(final, RuntimeCommand)
        assert final.name == "test"
        assert final.run_func is handler
        assert final.aliases == ("t",)
        assert final.is_async is False

    def test_to_command_without_run_func_uses_noop(self):
        """to_command() uses no-op lambda when no run_func."""
        cmd = Command(name="test")
        final = cmd.to_runtime_command()

        assert final.run_func is not None
        assert callable(final.run_func)
        # Should be a no-op
        assert final.run_func() is None

    def test_to_command_converts_subcommands(self):
        """to_command() recursively converts subcommands."""

        def parent_handler():
            pass

        def child_handler():
            pass

        parent = Command(name="parent", run_func=parent_handler)
        child = Command(name="child", run_func=child_handler)
        parent.subcommands["child"] = child

        final = parent.to_runtime_command()

        assert "child" in final.subcommands
        assert isinstance(final.subcommands["child"], RuntimeCommand)
        assert final.subcommands["child"].name == "child"

    def test_to_command_converts_aliases_to_tuple(self):
        """to_command() converts aliases to tuple."""
        cmd = Command(name="test", aliases=["t", "tst"])
        final = cmd.to_runtime_command()

        assert isinstance(final.aliases, tuple)
        assert final.aliases == ("t", "tst")

    def test_to_command_detects_async_if_not_set(self):
        """to_command() detects async if is_async is None."""

        async def handler():
            pass

        cmd = Command(name="test", run_func=handler)
        cmd.is_async = None  # Reset to None

        final = cmd.to_runtime_command()
        assert final.is_async is True


class TestCommandCallable:
    """Test Command __call__ method."""

    def test_command_is_callable(self):
        """Command can be called."""

        def handler():
            pass

        cmd = Command(name="test", run_func=handler)
        assert callable(cmd)

    def test_call_converts_and_invokes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Command.__call__ converts to FinalCommand and invokes."""
        invoked: list[list[str]] = []

        def mock_invoke(_self: object, args: list[str]) -> None:
            invoked.append(args)

        def handler():
            pass

        cmd = Command(name="test", run_func=handler)

        # Monkey patch FinalCommand.invoke to track calls
        monkeypatch.setattr(RuntimeCommand, "invoke", mock_invoke)

        cmd(["arg1"])

        assert len(invoked) == 1
        assert invoked[0] == ["arg1"]


class TestCommandMutability:
    """Test Command builder is mutable."""

    def test_command_fields_are_mutable(self):
        """Command fields can be modified after creation."""
        cmd = Command(name="test")

        cmd.name = "changed"
        assert cmd.name == "changed"

        cmd.aliases = ("new",)
        assert cmd.aliases == ("new",)

        def handler():
            pass

        cmd.run_func = handler
        assert cmd.run_func is handler

    def test_subcommands_dict_is_mutable(self):
        """subcommands dict can be modified."""
        cmd = Command(name="test")

        child = Command(name="child", run_func=lambda: None)
        cmd.subcommands["child"] = child

        assert "child" in cmd.subcommands
        assert cmd.subcommands["child"] is child


class TestCommandMethods:
    """Test Command builder methods."""

    def test_mounted_commands(self):
        """mounted_commands() returns only mounted subcommands."""
        parent = Command(name="parent")

        mounted = Command(name="mounted", is_mounted=True)
        not_mounted = Command(name="not_mounted", is_mounted=False)

        parent.subcommands["mounted"] = mounted
        parent.subcommands["not_mounted"] = not_mounted

        assert parent.mounted_commands() == ["mounted"]

    def test_non_mounted_commands(self):
        """non_mounted_commands() returns only non-mounted subcommands."""
        parent = Command(name="parent")

        mounted = Command(name="mounted", is_mounted=True)
        not_mounted = Command(name="not_mounted", is_mounted=False)

        parent.subcommands["mounted"] = mounted
        parent.subcommands["not_mounted"] = not_mounted

        assert parent.non_mounted_commands() == ["not_mounted"]

    def test_mounted_commands_empty_when_no_subcommands(self):
        """mounted_commands() returns empty list when no subcommands."""
        cmd = Command(name="test")
        assert cmd.mounted_commands() == []

    def test_non_mounted_commands_empty_when_all_mounted(self):
        """non_mounted_commands() returns empty when all mounted."""
        parent = Command(name="parent")
        mounted = Command(name="mounted", is_mounted=True)
        parent.subcommands["mounted"] = mounted

        assert parent.non_mounted_commands() == []
