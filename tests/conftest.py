from typing import TYPE_CHECKING

import pytest

from aclaf.console import MockConsole
from aclaf.logging import MockLogger

if TYPE_CHECKING:
    from aclaf.console import Console
    from aclaf.logging import Logger


@pytest.fixture
def console() -> "Console":
    return MockConsole()


@pytest.fixture
def logger() -> "Logger":
    return MockLogger()
