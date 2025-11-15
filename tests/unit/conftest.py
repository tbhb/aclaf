"""Shared fixtures for unit tests."""

from io import StringIO

import pytest

from aclaf.console._basic import BasicConsole


@pytest.fixture
def string_buffer() -> StringIO:
    """Provide a StringIO buffer for capturing console output."""
    return StringIO()


@pytest.fixture
def test_console(string_buffer: StringIO) -> BasicConsole:
    """Provide a BasicConsole writing to a StringIO buffer."""
    return BasicConsole(file=string_buffer)
