"""Property-based tests for command validators using Hypothesis."""

from hypothesis import given, strategies as st

from aclaf.validation.command import (
    AtLeastOneOf,
    AtMostOneOf,
    ConflictsWith,
    ExactlyOneOf,
    Forbids,
    MutuallyExclusive,
    Requires,
    validate_at_least_one_of,
    validate_at_most_one_of,
    validate_conflicts_with,
    validate_exactly_one_of,
    validate_forbids,
    validate_mutually_exclusive,
    validate_requires,
)

# Strategies for generating test data


@st.composite
def parameter_names_strategy(draw: st.DrawFn, min_size: int = 0, max_size: int = 5):
    """Generate a tuple of valid parameter names."""
    return tuple(
        draw(
            st.lists(
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Ll", "Lu"),
                        min_codepoint=97,
                        max_codepoint=122,
                    ),
                    min_size=1,
                    max_size=10,
                ),
                min_size=min_size,
                max_size=max_size,
                unique=True,
            )
        )
    )


@st.composite
def parameter_mapping_strategy(
    draw: st.DrawFn,
    param_names: tuple[str, ...] | None = None,
    *,
    include_extra: bool = True,
):
    """Generate a parameter mapping with optional extra parameters."""
    if param_names is None:
        param_names = draw(parameter_names_strategy(min_size=1, max_size=5))

    # Generate values for specified parameters (mix of provided and None)
    mapping = {}
    for name in param_names:
        mapping[name] = draw(
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(min_size=0, max_size=20),
            )
        )

    # Optionally add extra parameters not in param_names
    if include_extra:
        extra_count = draw(st.integers(min_value=0, max_value=3))
        for i in range(extra_count):
            extra_name = f"extra_{i}"
            if extra_name not in mapping:
                mapping[extra_name] = draw(st.booleans())

    return mapping


# Property 1: None-value invariant - parameters with None values are always
# treated as "not provided"


@given(
    param_names=parameter_names_strategy(min_size=1, max_size=4),
)
def test_none_values_treated_as_not_provided_mutually_exclusive(param_names: list[str]):
    """Parameters with None values are treated as not provided for MutuallyExclusive."""
    metadata = MutuallyExclusive(parameter_names=param_names)

    # Create mapping where all values are None
    value = dict.fromkeys(param_names)

    result = validate_mutually_exclusive(value, metadata)

    # Should never fail when all values are None
    assert result is None


@given(
    param_names=parameter_names_strategy(min_size=1, max_size=4),
)
def test_none_values_treated_as_not_provided_exactly_one_of(param_names: list[str]):
    """Parameters with None values are treated as not provided for ExactlyOneOf."""
    metadata = ExactlyOneOf(parameter_names=param_names)

    # Create mapping where all values are None
    value = dict.fromkeys(param_names)

    result = validate_exactly_one_of(value, metadata)

    # Should fail because no parameters are provided
    assert result is not None
    assert len(result) > 0
    assert "must be provided" in result[0]


@given(
    param_names=parameter_names_strategy(min_size=1, max_size=4),
)
def test_none_values_treated_as_not_provided_at_least_one_of(param_names: list[str]):
    """Parameters with None values are treated as not provided for AtLeastOneOf."""
    metadata = AtLeastOneOf(parameter_names=param_names)

    # Create mapping where all values are None
    value = dict.fromkeys(param_names)

    result = validate_at_least_one_of(value, metadata)

    # Should fail because no parameters are provided
    assert result is not None
    assert len(result) > 0
    assert "must be provided" in result[0]


# Property 2: Mathematical invariant - count of provided parameters determines success


@given(
    param_names=parameter_names_strategy(min_size=2, max_size=5),
    data=st.data(),
)
def test_mutually_exclusive_fails_iff_multiple_provided(
    param_names: list[str], data: st.DataObject
):
    """MutuallyExclusive fails if and only if 2+ parameters are provided."""
    metadata = MutuallyExclusive(parameter_names=param_names)

    # Generate mapping
    value = data.draw(parameter_mapping_strategy(param_names=tuple(param_names)))

    # Count provided parameters (non-None)
    provided_count = sum(1 for name in param_names if value.get(name) is not None)

    result = validate_mutually_exclusive(value, metadata)

    if provided_count <= 1:
        assert result is None
    else:
        assert result is not None
        assert len(result) > 0


@given(
    param_names=parameter_names_strategy(min_size=1, max_size=5),
    data=st.data(),
)
def test_exactly_one_of_passes_iff_exactly_one_provided(
    param_names: list[str], data: st.DataObject
):
    """ExactlyOneOf passes if and only if exactly 1 parameter is provided."""
    metadata = ExactlyOneOf(parameter_names=param_names)

    # Generate mapping
    value = data.draw(parameter_mapping_strategy(param_names=tuple(param_names)))

    # Count provided parameters (non-None)
    provided_count = sum(1 for name in param_names if value.get(name) is not None)

    result = validate_exactly_one_of(value, metadata)

    if provided_count == 1:
        assert result is None
    else:
        assert result is not None
        assert len(result) > 0


@given(
    param_names=parameter_names_strategy(min_size=1, max_size=5),
    data=st.data(),
)
def test_at_least_one_of_passes_iff_one_or_more_provided(
    param_names: list[str], data: st.DataObject
):
    """AtLeastOneOf passes if and only if 1+ parameters are provided."""
    metadata = AtLeastOneOf(parameter_names=param_names)

    # Generate mapping
    value = data.draw(parameter_mapping_strategy(param_names=tuple(param_names)))

    # Count provided parameters (non-None)
    provided_count = sum(1 for name in param_names if value.get(name) is not None)

    result = validate_at_least_one_of(value, metadata)

    if provided_count >= 1:
        assert result is None
    else:
        assert result is not None
        assert len(result) > 0


@given(
    param_names=parameter_names_strategy(min_size=2, max_size=5),
    data=st.data(),
)
def test_at_most_one_of_passes_iff_zero_or_one_provided(
    param_names: list[str], data: st.DataObject
):
    """AtMostOneOf passes if and only if 0 or 1 parameter is provided."""
    metadata = AtMostOneOf(parameter_names=param_names)

    # Generate mapping
    value = data.draw(parameter_mapping_strategy(param_names=tuple(param_names)))

    # Count provided parameters (non-None)
    provided_count = sum(1 for name in param_names if value.get(name) is not None)

    result = validate_at_most_one_of(value, metadata)

    if provided_count <= 1:
        assert result is None
    else:
        assert result is not None
        assert len(result) > 0


# Property 3: Extra parameters should be ignored


@given(
    param_names=parameter_names_strategy(min_size=1, max_size=3),
    data=st.data(),
)
def test_mutually_exclusive_ignores_extra_parameters(
    param_names: list[str], data: st.DataObject
):
    """MutuallyExclusive only considers specified parameters, ignores extras."""
    metadata = MutuallyExclusive(parameter_names=param_names)

    # Generate base mapping
    value = data.draw(
        parameter_mapping_strategy(param_names=tuple(param_names), include_extra=False)
    )

    # Add many extra parameters with non-None values
    for i in range(10):
        value[f"unrelated_{i}"] = True

    # Result should only depend on param_names, not extras
    provided_count = sum(1 for name in param_names if value.get(name) is not None)

    result = validate_mutually_exclusive(value, metadata)

    if provided_count <= 1:
        assert result is None
    else:
        assert result is not None


# Property 4: Dependency validators - source not provided means no validation


@given(
    source=st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Lu"), min_codepoint=97, max_codepoint=122
        ),
        min_size=1,
        max_size=10,
    ),
    required=parameter_names_strategy(min_size=1, max_size=3),
    data=st.data(),
)
def test_requires_no_validation_when_source_not_provided(
    source: str, required: list[str], data: st.DataObject
):
    """Requires validator passes when source parameter is None or missing."""
    # Skip if source is in required names (conflict)
    if source in required:
        return

    metadata = Requires(source=source, required=required)

    # Create mapping where source is None
    value: dict[str, bool | None] = {source: None}
    # Add some required params (may or may not be None)
    for req in required:
        value[req] = data.draw(st.one_of(st.none(), st.booleans()))

    result = validate_requires(value, metadata)

    # Should always pass when source is None
    assert result is None


@given(
    source=st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Lu"), min_codepoint=97, max_codepoint=122
        ),
        min_size=1,
        max_size=10,
    ),
    forbidden=parameter_names_strategy(min_size=1, max_size=3),
    data=st.data(),
)
def test_forbids_no_validation_when_source_not_provided(
    source: str, forbidden: list[str], data: st.DataObject
):
    """Forbids validator passes when source parameter is None or missing."""
    # Skip if source is in forbidden names (conflict)
    if source in forbidden:
        return

    metadata = Forbids(source=source, forbidden=forbidden)

    # Create mapping where source is None
    value: dict[str, bool | None] = {source: None}
    # Add forbidden params (can be anything)
    for forb in forbidden:
        value[forb] = data.draw(st.one_of(st.none(), st.booleans()))

    result = validate_forbids(value, metadata)

    # Should always pass when source is None
    assert result is None


# Property 5: Error consistency - failures always return non-empty tuple of strings


@given(
    param_names=parameter_names_strategy(min_size=2, max_size=4),
)
def test_mutually_exclusive_error_format_consistent(param_names: list[str]):
    """When MutuallyExclusive fails, it returns non-empty tuple of strings."""
    metadata = MutuallyExclusive(parameter_names=param_names)

    # Force failure by providing all parameters
    value = dict.fromkeys(param_names, True)

    result = validate_mutually_exclusive(value, metadata)

    # Check error format
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) > 0
    assert all(isinstance(err, str) for err in result)
    assert all(len(err) > 0 for err in result)


@given(
    source=st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Lu"), min_codepoint=97, max_codepoint=122
        ),
        min_size=1,
        max_size=10,
    ),
    required=parameter_names_strategy(min_size=1, max_size=3),
)
def test_requires_error_format_consistent(source: str, required: list[str]):
    """When Requires fails, it returns non-empty tuple of strings."""
    # Skip if source is in required names (conflict)
    if source in required:
        return

    metadata = Requires(source=source, required=required)

    # Force failure: source provided, required parameters missing
    value: dict[str, bool | None] = {source: True}
    for req in required:
        value[req] = None

    result = validate_requires(value, metadata)

    # Check error format
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) > 0
    assert all(isinstance(err, str) for err in result)
    assert all(len(err) > 0 for err in result)


# Property 6: ConflictsWith behaves identically to MutuallyExclusive


@given(
    param_names=parameter_names_strategy(min_size=2, max_size=5),
    data=st.data(),
)
def test_conflicts_with_equivalent_to_mutually_exclusive(
    param_names: list[str], data: st.DataObject
):
    """ConflictsWith has identical behavior to MutuallyExclusive."""
    conflicts_meta = ConflictsWith(parameter_names=param_names)
    mutually_exclusive_meta = MutuallyExclusive(parameter_names=param_names)

    # Generate mapping
    value = data.draw(parameter_mapping_strategy(param_names=tuple(param_names)))

    conflicts_result = validate_conflicts_with(value, conflicts_meta)
    mutually_exclusive_result = validate_mutually_exclusive(
        value, mutually_exclusive_meta
    )

    # Both should pass or both should fail
    if conflicts_result is None:
        assert mutually_exclusive_result is None
    else:
        assert mutually_exclusive_result is not None


# Property 7: Empty parameter lists behave predictably


def test_mutually_exclusive_with_empty_params_always_passes():
    """MutuallyExclusive with no parameters always passes."""
    metadata = MutuallyExclusive(parameter_names=())

    @given(mapping=st.dictionaries(st.text(min_size=1), st.booleans()))
    def check(mapping):
        result = validate_mutually_exclusive(mapping, metadata)
        assert result is None

    check()


def test_exactly_one_of_with_empty_params_always_fails():
    """ExactlyOneOf with no parameters always fails."""
    metadata = ExactlyOneOf(parameter_names=())

    @given(mapping=st.dictionaries(st.text(min_size=1), st.booleans()))
    def check(mapping):
        result = validate_exactly_one_of(mapping, metadata)
        assert result is not None

    check()
