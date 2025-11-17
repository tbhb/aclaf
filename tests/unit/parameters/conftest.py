# pyright: reportAny=false, reportExplicitAny=false
from typing import Annotated, Any

import pytest
from annotated_types import Ge, Gt, Le, MinLen

from aclaf.metadata import AtLeastOne, Flag


@pytest.fixture
def simple_annotated() -> Any:
    """Simple Annotated[int, Gt(0)]."""
    return Annotated[int, Gt(0)]


@pytest.fixture
def nested_annotated() -> Any:
    """Nested Annotated[Annotated[int, Gt(0)], Le(100)]."""
    inner = Annotated[int, Gt(0)]
    return Annotated[inner, Le(100)]


@pytest.fixture
def triple_nested_annotated() -> Any:
    """Triple nested Annotated."""
    level1 = Annotated[int, Gt(0)]
    level2 = Annotated[level1, Le(100)]
    return Annotated[level2, Ge(5)]


@pytest.fixture
def complex_metadata() -> Any:
    """Parameter with multiple metadata types."""
    return Annotated[int, Gt(0), Le(100), "--count", "-c"]


@pytest.fixture
def string_metadata_annotated() -> Any:
    """Annotated type with string metadata for option names."""
    return Annotated[str, "--verbose", "-v"]


@pytest.fixture
def arity_metadata_annotated() -> Any:
    """Annotated type with arity metadata."""
    return Annotated[list[str], AtLeastOne()]


@pytest.fixture
def flag_metadata_annotated() -> Any:
    """Annotated type with Flag metadata."""
    return Annotated[bool, Flag()]


@pytest.fixture
def mixed_validation_metadata() -> Any:
    """Annotated type with multiple validation constraints."""
    return Annotated[str, MinLen(1), Le(100), Gt(0)]
