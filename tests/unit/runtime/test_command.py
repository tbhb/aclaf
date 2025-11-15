"""Tests for FinalCommand structure and properties.

This module tests FinalCommand initialization, immutability, properties,
and conversion to CommandSpec.
"""

from typing import TYPE_CHECKING

import pytest

from aclaf import (
    EMPTY_COMMAND_FUNCTION,
    RuntimeCommand,
    RuntimeOption,
    RuntimePositional,
)
from aclaf.parser import Parser

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from pytest_mock import MockerFixture


@pytest.fixture
def mock_option(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=["to_option_spec"])


@pytest.fixture
def mock_positional(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=["to_positional_spec"])


@pytest.fixture
def mock_command() -> RuntimeCommand:
    return RuntimeCommand(name="mock", run_func=EMPTY_COMMAND_FUNCTION)


class TestFinalCommandCreation:
    """Test FinalCommand initialization."""

    def test_minimal_command_creation(self):
        """FinalCommand can be created with minimal required fields."""
        handler = EMPTY_COMMAND_FUNCTION

        cmd = RuntimeCommand(name="test", run_func=handler)

        assert cmd.name == "test"
        assert cmd.run_func is handler
        assert cmd.aliases == ()
        assert cmd.options == {}
        assert cmd.positionals == {}
        assert cmd.is_async is False
        assert cmd.parser_cls is Parser
        assert cmd.parser_config is None
        assert cmd.subcommands == {}
        assert cmd.context_param is None

    def test_command_with_all_fields(
        self,
        mock_option: "MagicMock",
        mock_positional: "MagicMock",
        mock_command: RuntimeCommand,
    ):
        """FinalCommand can be created with all fields."""
        handler = EMPTY_COMMAND_FUNCTION

        options: dict[str, RuntimeOption] = {"opt": mock_option}
        positionals: dict[str, RuntimePositional] = {"pos": mock_positional}
        subcommands: dict[str, RuntimeCommand] = {"sub": mock_command}

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            aliases=("t", "tst"),
            options=options,
            positionals=positionals,
            is_async=True,
            parser_cls=Parser,
            parser_config=None,
            subcommands=subcommands,
            context_param="ctx",
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

    def test_repr_is_informative(self):
        """FinalCommand __repr__ is informative."""

        def handler():
            pass

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            aliases=("t",),
            is_async=True,
        )

        repr_str = repr(cmd)
        assert "FinalCommand" in repr_str
        assert "name='test'" in repr_str
        assert "is_async=True" in repr_str


class TestFinalCommandProperties:
    """Test FinalCommand properties."""

    def test_parameters_combines_options_and_positionals(
        self, mock_option: "MagicMock", mock_positional: "MagicMock"
    ):
        """parameters property combines options and positionals."""
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            options={"verbose": mock_option},
            positionals={"path": mock_positional},
        )

        params = cmd.parameters
        assert len(params) == 2
        assert params["verbose"] is mock_option
        assert params["path"] is mock_positional

    def test_parameters_empty_when_no_params(self):
        """parameters property is empty when no options/positionals."""
        cmd = RuntimeCommand(name="test", run_func=EMPTY_COMMAND_FUNCTION)
        assert cmd.parameters == {}

    def test_parameters_with_only_options(self, mock_option: "MagicMock"):
        """parameters property works with only options."""
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            options={"verbose": mock_option},
        )
        assert cmd.parameters == {"verbose": mock_option}

    def test_parameters_with_only_positionals(self, mock_positional: "MagicMock"):
        """parameters property works with only positionals."""
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            positionals={"path": mock_positional},
        )
        assert cmd.parameters == {"path": mock_positional}


class TestFinalCommandCallable:
    """Test FinalCommand __call__ method."""

    def test_command_is_callable(self):
        """FinalCommand can be called like a function."""
        called: list[bool] = []

        def handler():
            called.append(True)

        cmd = RuntimeCommand(name="test", run_func=handler)

        assert callable(cmd)

    def test_call_delegates_to_invoke(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FinalCommand.__call__ delegates to invoke method."""
        invoked: list[list[str]] = []

        def mock_invoke(_self: object, args: list[str]) -> None:
            invoked.append(args)

        cmd = RuntimeCommand(name="test", run_func=EMPTY_COMMAND_FUNCTION)
        monkeypatch.setattr(RuntimeCommand, "invoke", mock_invoke)

        cmd(["arg1", "arg2"])

        assert len(invoked) == 1
        assert invoked[0] == ["arg1", "arg2"]
