from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

from aclaf.execution import EMPTY_COMMAND_FUNCTION, RuntimeCommand, RuntimeParameter
from aclaf.logging import NullLogger
from aclaf.parser import Parser
from aclaf.types import ParameterKind

if TYPE_CHECKING:
    from collections.abc import Callable
    from unittest.mock import MagicMock

    from pytest_mock import MockerFixture


@pytest.fixture
def mock_option(mocker: "MockerFixture") -> "MagicMock":
    mock = mocker.Mock(spec=["to_option_spec", "kind"])
    mock.kind = ParameterKind.OPTION
    return mock


@pytest.fixture
def mock_positional(mocker: "MockerFixture") -> "MagicMock":
    mock = mocker.Mock(spec=["to_positional_spec", "kind"])
    mock.kind = ParameterKind.POSITIONAL
    return mock


class TestRuntimeCommand:
    def test_defaults(self, mock_converters: "MagicMock", mock_validators: "MagicMock"):
        handler = EMPTY_COMMAND_FUNCTION

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=mock_converters,
            parameter_validators=mock_validators,
        )

        assert cmd.aliases == ()
        assert cmd.console_param is None
        assert cmd.context_param is None
        assert isinstance(cmd.parameters, MappingProxyType)
        assert cmd.parameters == {}
        assert cmd.is_async is False
        assert isinstance(cmd.logger, NullLogger)
        assert cmd.logger_param is None
        assert cmd.parser_cls is Parser
        assert cmd.parser_config is None
        assert isinstance(cmd.subcommands, MappingProxyType)
        assert cmd.subcommands == {}

    def test_command_with_all_fields(
        self,
        mock_option: "MagicMock",
        mock_positional: "MagicMock",
        mock_converters: "MagicMock",
        mock_validators: "MagicMock",
        runtime_command: RuntimeCommand,
    ):
        handler = EMPTY_COMMAND_FUNCTION

        options: dict[str, RuntimeParameter] = {"opt": mock_option}
        positionals: dict[str, RuntimeParameter] = {"pos": mock_positional}
        subcommands: dict[str, RuntimeCommand] = {"sub": runtime_command}

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            aliases=("t", "tst"),
            parameters={**options, **positionals},
            is_async=True,
            parser_cls=Parser,
            parser_config=None,
            subcommands=subcommands,
            context_param="ctx",
            converters=mock_converters,
            parameter_validators=mock_validators,
        )

        assert cmd.name == "test"
        assert cmd.run_func is handler
        assert cmd.aliases == ("t", "tst")
        assert cmd.options == options
        assert cmd.positionals == positionals
        assert cmd.is_async is True
        assert cmd.parser_cls is Parser
        assert cmd.subcommands == subcommands
        assert cmd.context_param == "ctx"

    def test_repr_is_informative(
        self,
        runtime_command_factory: "Callable[..., RuntimeCommand]",
    ):
        cmd = runtime_command_factory(
            name="test",
            aliases=("t",),
        )

        repr_str = repr(cmd)
        assert "RuntimeCommand" in repr_str
        assert "name='test'" in repr_str
        assert "aliases=('t',)" in repr_str


class TestRuntimeCommandCallable:
    def test_command_is_callable(
        self, runtime_command_factory: "Callable[..., RuntimeCommand]"
    ) -> None:
        cmd = runtime_command_factory()

        assert callable(cmd)

    def test_call_delegates_to_invoke(
        self,
        monkeypatch: pytest.MonkeyPatch,
        runtime_command_factory: "Callable[..., RuntimeCommand]",
    ) -> None:
        invoked: list[list[str]] = []

        def mock_invoke(_self: object, args: list[str]) -> None:
            invoked.append(args)

        cmd = runtime_command_factory()
        monkeypatch.setattr(RuntimeCommand, "invoke", mock_invoke)

        cmd(["arg1", "arg2"])

        assert len(invoked) == 1
        assert invoked[0] == ["arg1", "arg2"]
