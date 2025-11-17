from typing import TYPE_CHECKING

import pytest

from aclaf import ConsoleResponder
from aclaf.console import BaseConsole, BasicConsole

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from pytest_mock import MockerFixture


@pytest.fixture
def console() -> BasicConsole:
    return BasicConsole()


@pytest.fixture
def responder(console: BaseConsole) -> ConsoleResponder:
    return ConsoleResponder(console=console)


@pytest.fixture
def mock_console(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=BaseConsole)


@pytest.fixture
def mock_responder(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=ConsoleResponder)
