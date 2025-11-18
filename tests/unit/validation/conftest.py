import pytest

from aclaf.validation import ValidatorRegistry


@pytest.fixture
def registry() -> ValidatorRegistry:
    return ValidatorRegistry()


@pytest.fixture
def empty_registry() -> ValidatorRegistry:
    reg = ValidatorRegistry()
    # Clear built-in validators for isolated testing
    reg.validators.clear()
    return reg
