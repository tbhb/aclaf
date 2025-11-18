import pytest

from aclaf.conversion import ConverterRegistry


@pytest.fixture
def registry() -> ConverterRegistry:
    return ConverterRegistry()


@pytest.fixture
def empty_registry() -> ConverterRegistry:
    reg = ConverterRegistry()
    # Clear builtin converters for isolated testing
    reg.converters.clear()
    return reg
