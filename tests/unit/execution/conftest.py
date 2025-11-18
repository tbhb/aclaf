from typing import TYPE_CHECKING

import pytest

from aclaf.console import BaseConsole, BasicConsole

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from pytest_mock import MockerFixture


@pytest.fixture
def console() -> BasicConsole:
    return BasicConsole()


@pytest.fixture
def mock_console(mocker: "MockerFixture") -> "MagicMock":
    return mocker.Mock(spec=BaseConsole)
