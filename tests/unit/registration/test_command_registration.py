import pytest

from aclaf import EMPTY_COMMAND_FUNCTION, Command, RuntimeCommand


class TestCommandCreation:
    def test_defaults(self):
        cmd = Command(name="test")

        assert cmd.name == "test"
        assert cmd.aliases == ()
        assert cmd.run_func is None
        assert cmd.parser_config is None
        assert cmd.parent_command is None
        assert cmd.root_command is None
        assert cmd.subcommands == {}
        assert cmd.context_param is None
        assert cmd.is_async is False
        assert cmd.is_mounted is False

    def test_command_with_aliases(self):
        cmd = Command(name="test", aliases=("t", "tst"))

        assert cmd.aliases == ("t", "tst")

    def test_command_with_run_func(self):
        def handler():
            pass

        cmd = Command(name="test", run_func=handler)

        assert cmd.run_func is handler
        assert cmd.is_async is False  # Detected from non-async function

    def test_command_with_async_run_func(self):
        async def handler():
            pass

        cmd = Command(name="test", run_func=handler)

        assert cmd.run_func is handler
        assert cmd.is_async is True

    def test_command_name_validation(self):
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
        cmd = Command(name="test", aliases=("t",))
        repr_str = repr(cmd)

        assert "Command" in repr_str
        assert "name='test'" in repr_str


class TestCommandAsyncDetection:
    def test_async_detection_for_sync_function(self):
        def handler():
            pass

        cmd = Command(name="test", run_func=handler)
        assert cmd.is_async is False

    def test_async_detection_for_async_function(self):
        async def handler():
            pass

        cmd = Command(name="test", run_func=handler)
        assert cmd.is_async is True

    def test_async_detection_when_no_run_func(self):
        cmd = Command(name="test")
        assert cmd.is_async is False

    def test_async_detection_updated_when_run_func_set(self):
        async def handler():
            pass

        cmd = Command(name="test")
        assert cmd.is_async is None

        cmd.run_func = handler
        cmd.is_async = cmd._check_run_func_async()  # noqa: SLF001
        assert cmd.is_async is True


class TestCommandConversion:
    def test_to_command_creates_runtime_command(self):
        def handler():
            pass

        cmd = Command(name="test", run_func=handler, aliases=("t",))
        converted = cmd.to_runtime_command()

        assert isinstance(converted, RuntimeCommand)
        assert converted.name == "test"
        assert converted.run_func is handler
        assert converted.aliases == ("t",)
        assert converted.is_async is False

    def test_to_command_without_run_func_uses_noop(self):
        cmd = Command(name="test")

        converted = cmd.to_runtime_command()

        assert converted.run_func is EMPTY_COMMAND_FUNCTION

    def test_to_command_converts_subcommands(self):
        parent = Command(name="parent", run_func=EMPTY_COMMAND_FUNCTION)
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        parent.subcommands["child"] = child

        converted = parent.to_runtime_command()

        assert "child" in converted.subcommands
        assert isinstance(converted.subcommands["child"], RuntimeCommand)
        assert converted.subcommands["child"].name == "child"

    def test_to_command_converts_aliases_to_tuple(self):
        cmd = Command(name="test", aliases=["t", "tst"])
        final = cmd.to_runtime_command()

        assert isinstance(final.aliases, tuple)
        assert final.aliases == ("t", "tst")

    def test_to_command_detects_async_if_not_set(self):
        async def handler():
            pass

        cmd = Command(name="test", run_func=handler)
        cmd.is_async = False

        final = cmd.to_runtime_command()
        assert final.is_async is True


class TestCommandCallable:
    def test_command_is_callable(self):
        def handler():
            pass

        cmd = Command(name="test", run_func=handler)
        assert callable(cmd)

    def test_call_converts_and_invokes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        invoked: list[list[str]] = []

        def mock_invoke(_self: object, args: list[str]) -> None:
            invoked.append(args)

        cmd = Command(name="test", run_func=EMPTY_COMMAND_FUNCTION)

        monkeypatch.setattr(RuntimeCommand, "invoke", mock_invoke)

        cmd(["arg1"])

        assert len(invoked) == 1
        assert invoked[0] == ["arg1"]


class TestCommandMethods:
    def test_mounted_commands(self):
        parent = Command(name="parent")

        mounted = Command(name="mounted", is_mounted=True)
        not_mounted = Command(name="not_mounted", is_mounted=False)

        parent.subcommands["mounted"] = mounted
        parent.subcommands["not_mounted"] = not_mounted

        assert parent.mounted_commands() == ["mounted"]

    def test_non_mounted_commands(self):
        parent = Command(name="parent")

        mounted = Command(name="mounted", is_mounted=True)
        not_mounted = Command(name="not_mounted", is_mounted=False)

        parent.subcommands["mounted"] = mounted
        parent.subcommands["not_mounted"] = not_mounted

        assert parent.non_mounted_commands() == ["not_mounted"]

    def test_mounted_commands_empty_when_no_subcommands(self):
        cmd = Command(name="test")
        assert cmd.mounted_commands() == []

    def test_non_mounted_commands_empty_when_all_mounted(self):
        parent = Command(name="parent")
        mounted = Command(name="mounted", is_mounted=True)
        parent.subcommands["mounted"] = mounted

        assert parent.non_mounted_commands() == []
