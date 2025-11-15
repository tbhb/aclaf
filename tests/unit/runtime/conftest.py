from typing import TYPE_CHECKING

import pytest

from aclaf import ConsoleResponder
from aclaf.console import BaseConsole, BasicConsole

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from pytest_mock import MockerFixture


@pytest.fixture
def console() -> BasicConsole:
    """Provide a BaseConsole for testing."""
    return BasicConsole()


@pytest.fixture
def responder(console: BaseConsole) -> ConsoleResponder:
    """Provide a Responder for testing."""
    return ConsoleResponder(console=console)


@pytest.fixture
def mock_console(mocker: "MockerFixture") -> "MagicMock":
    """Provide a mocked BaseConsole for testing."""
    return mocker.Mock(spec=BaseConsole)


@pytest.fixture
def mock_responder(mocker: "MockerFixture") -> "MagicMock":
    """Provide a mocked Responder for testing."""
    return mocker.Mock(spec=ConsoleResponder)
