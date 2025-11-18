"""Property-based tests for parameter validators using Hypothesis."""

from datetime import date

from hypothesis import given, strategies as st

from aclaf.validation.parameter._datetime import (
    AfterDate,
    BeforeDate,
    DateRange,
    validate_after_date,
    validate_before_date,
    validate_date_range,
)
from aclaf.validation.parameter._mapping import (
    ForbiddenKeys,
    MaxKeys,
    MinKeys,
    RequiredKeys,
    validate_forbidden_keys,
    validate_max_keys,
    validate_min_keys,
    validate_required_keys,
)
from aclaf.validation.parameter._numeric import (
    IsNegative,
    IsNonNegative,
    IsNonPositive,
    IsPositive,
    Precision,
    validate_is_negative,
    validate_is_non_negative,
    validate_is_non_positive,
    validate_is_positive,
    validate_precision,
)
from aclaf.validation.parameter._sequence import (
    ItemType,
    SequenceContains,
    UniqueItems,
    validate_item_type,
    validate_sequence_contains,
    validate_unique_items,
)

# Numeric validators


@given(value=st.integers(min_value=1))
def test_is_positive_passes_for_positive_integers(value):
    metadata = IsPositive()

    result = validate_is_positive(value, metadata)

    assert result is None


@given(value=st.integers(max_value=0))
def test_is_positive_fails_for_non_positive_integers(value):
    metadata = IsPositive()

    result = validate_is_positive(value, metadata)

    assert result is not None
    assert len(result) > 0


@given(value=st.integers(max_value=-1))
def test_is_negative_passes_for_negative_integers(value):
    metadata = IsNegative()

    result = validate_is_negative(value, metadata)

    assert result is None


@given(value=st.integers(min_value=0))
def test_is_negative_fails_for_non_negative_integers(value):
    metadata = IsNegative()

    result = validate_is_negative(value, metadata)

    assert result is not None
    assert len(result) > 0


@given(value=st.integers(min_value=0))
def test_is_non_negative_passes_for_non_negative_integers(value):
    metadata = IsNonNegative()

    result = validate_is_non_negative(value, metadata)

    assert result is None


@given(value=st.integers(max_value=-1))
def test_is_non_negative_fails_for_negative_integers(value):
    metadata = IsNonNegative()

    result = validate_is_non_negative(value, metadata)

    assert result is not None
    assert len(result) > 0


@given(value=st.integers(max_value=0))
def test_is_non_positive_passes_for_non_positive_integers(value):
    metadata = IsNonPositive()

    result = validate_is_non_positive(value, metadata)

    assert result is None


@given(value=st.integers(min_value=1))
def test_is_non_positive_fails_for_positive_integers(value):
    metadata = IsNonPositive()

    result = validate_is_non_positive(value, metadata)

    assert result is not None
    assert len(result) > 0


@given(
    value=st.floats(
        min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False
    ),
    max_decimals=st.integers(min_value=0, max_value=5),
)
def test_precision_validates_integers_regardless_of_limit(value, max_decimals):
    metadata = Precision(max_decimals=max_decimals)
    int_value = int(value)

    result = validate_precision(int_value, metadata)

    # Integers always pass precision checks
    assert result is None


# Datetime validators


@given(
    threshold=st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)),
    days_after=st.integers(min_value=1, max_value=365),
)
def test_after_date_passes_for_dates_after_threshold(threshold, days_after):
    metadata = AfterDate(after=threshold)
    value = date.fromordinal(threshold.toordinal() + days_after)

    result = validate_after_date(value, metadata)

    assert result is None


@given(
    threshold=st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)),
    days_before=st.integers(min_value=0, max_value=365),
)
def test_after_date_fails_for_dates_not_after_threshold(threshold, days_before):
    metadata = AfterDate(after=threshold)
    value = date.fromordinal(threshold.toordinal() - days_before)

    result = validate_after_date(value, metadata)

    assert result is not None
    assert len(result) > 0


@given(
    threshold=st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)),
    days_before=st.integers(min_value=1, max_value=365),
)
def test_before_date_passes_for_dates_before_threshold(threshold, days_before):
    metadata = BeforeDate(before=threshold)
    value = date.fromordinal(threshold.toordinal() - days_before)

    result = validate_before_date(value, metadata)

    assert result is None


@given(
    threshold=st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)),
    days_after=st.integers(min_value=0, max_value=365),
)
def test_before_date_fails_for_dates_not_before_threshold(threshold, days_after):
    metadata = BeforeDate(before=threshold)
    value = date.fromordinal(threshold.toordinal() + days_after)

    result = validate_before_date(value, metadata)

    assert result is not None
    assert len(result) > 0


@given(
    after=st.dates(min_value=date(2000, 1, 1), max_value=date(2020, 12, 31)),
    before=st.dates(min_value=date(2021, 1, 1), max_value=date(2030, 12, 31)),
)
def test_date_range_validates_dates_within_exclusive_range(after, before):
    metadata = DateRange(
        after=after, before=before, inclusive_after=False, inclusive_before=False
    )
    # Generate date strictly between bounds
    value = date.fromordinal(
        (after.toordinal() + before.toordinal()) // 2
    )

    # Only test if value is strictly between bounds
    if after < value < before:
        result = validate_date_range(value, metadata)
        assert result is None


# Sequence validators


@given(items=st.lists(st.integers(), unique=True, min_size=0, max_size=20))
def test_unique_items_passes_for_unique_lists(items):
    metadata = UniqueItems()

    result = validate_unique_items(items, metadata)

    assert result is None


@given(
    items=st.lists(st.integers(), min_size=2, max_size=10),
    duplicate=st.integers(),
)
def test_unique_items_fails_for_lists_with_duplicates(items, duplicate):
    metadata = UniqueItems()
    # Add duplicate to ensure failure
    items_with_dup = [*items, duplicate, duplicate]

    result = validate_unique_items(items_with_dup, metadata)

    assert result is not None
    assert len(result) > 0


@given(
    items=st.lists(st.integers(), min_size=1, max_size=10),
    required_item=st.integers(),
)
def test_sequence_contains_passes_when_item_present(items, required_item):
    metadata = SequenceContains(items=(required_item,))
    # Ensure item is in list
    value = [*items, required_item]

    result = validate_sequence_contains(value, metadata)

    assert result is None


@given(
    items=st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=10)
)
def test_item_type_passes_for_correct_types(items):
    metadata = ItemType(types=(int,))

    result = validate_item_type(items, metadata)

    # All items are integers
    assert result is None



# Mapping validators


@given(
    keys=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=10,
        ),
        min_size=1,
        max_size=5,
        unique=True,
    ),
    data=st.data(),
)
def test_required_keys_passes_when_all_present(keys, data):
    metadata = RequiredKeys(keys=tuple(keys))
    # Build dict with all required keys
    value = {key: data.draw(st.integers()) for key in keys}
    # Add some extra keys
    for i in range(3):
        value[f"extra_{i}"] = data.draw(st.integers())

    result = validate_required_keys(value, metadata)

    assert result is None


@given(
    required=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=10,
        ),
        min_size=2,
        max_size=5,
        unique=True,
    ),
    data=st.data(),
)
def test_required_keys_fails_when_missing(required, data):
    metadata = RequiredKeys(keys=tuple(required))
    # Build dict with only some required keys
    num_to_include = len(required) - 1
    value = {key: data.draw(st.integers()) for key in required[:num_to_include]}

    result = validate_required_keys(value, metadata)

    assert result is not None
    assert len(result) > 0


@given(
    forbidden=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=10,
        ),
        min_size=1,
        max_size=5,
        unique=True,
    ),
    data=st.data(),
)
def test_forbidden_keys_passes_when_none_present(forbidden, data):
    metadata = ForbiddenKeys(keys=tuple(forbidden))
    # Build dict with keys not in forbidden list
    value = {f"allowed_{i}": data.draw(st.integers()) for i in range(5)}

    result = validate_forbidden_keys(value, metadata)

    assert result is None


@given(
    forbidden=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=10,
        ),
        min_size=1,
        max_size=5,
        unique=True,
    ),
    data=st.data(),
)
def test_forbidden_keys_fails_when_present(forbidden, data):
    metadata = ForbiddenKeys(keys=tuple(forbidden))
    # Build dict with at least one forbidden key
    value = {forbidden[0]: data.draw(st.integers())}

    result = validate_forbidden_keys(value, metadata)

    assert result is not None
    assert len(result) > 0


@given(
    min_keys=st.integers(min_value=0, max_value=10),
    actual_keys=st.integers(min_value=0, max_value=20),
)
def test_min_keys_validates_correctly(min_keys, actual_keys):
    metadata = MinKeys(min_keys=min_keys)
    value = {str(i): i for i in range(actual_keys)}

    result = validate_min_keys(value, metadata)

    if actual_keys >= min_keys:
        assert result is None
    else:
        assert result is not None
        assert len(result) > 0


@given(
    max_keys=st.integers(min_value=0, max_value=10),
    actual_keys=st.integers(min_value=0, max_value=20),
)
def test_max_keys_validates_correctly(max_keys, actual_keys):
    metadata = MaxKeys(max_keys=max_keys)
    value = {str(i): i for i in range(actual_keys)}

    result = validate_max_keys(value, metadata)

    if actual_keys <= max_keys:
        assert result is None
    else:
        assert result is not None
        assert len(result) > 0


# Property: None values always pass validation


@given(
    validator_choice=st.sampled_from(
        ["positive", "negative", "non_negative", "non_positive"]
    )
)
def test_numeric_validators_pass_none_values(validator_choice):
    validators = {
        "positive": (IsPositive(), validate_is_positive),
        "negative": (IsNegative(), validate_is_negative),
        "non_negative": (IsNonNegative(), validate_is_non_negative),
        "non_positive": (IsNonPositive(), validate_is_non_positive),
    }

    metadata, validator_fn = validators[validator_choice]

    result = validator_fn(None, metadata)

    assert result is None


@given(
    threshold=st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)),
)
def test_date_validators_pass_none_values(threshold):
    after_meta = AfterDate(after=threshold)
    before_meta = BeforeDate(before=threshold)

    assert validate_after_date(None, after_meta) is None
    assert validate_before_date(None, before_meta) is None


@given(items=st.lists(st.integers(), min_size=0, max_size=10))
def test_sequence_validators_pass_none_values(items):
    unique_meta = UniqueItems()
    contains_meta = SequenceContains(items=tuple(items))

    assert validate_unique_items(None, unique_meta) is None
    assert validate_sequence_contains(None, contains_meta) is None


@given(
    keys=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=10,
        ),
        min_size=1,
        max_size=5,
        unique=True,
    )
)
def test_mapping_validators_pass_none_values(keys):
    required_meta = RequiredKeys(keys=tuple(keys))
    forbidden_meta = ForbiddenKeys(keys=tuple(keys))
    min_meta = MinKeys(min_keys=1)
    max_meta = MaxKeys(max_keys=10)

    assert validate_required_keys(None, required_meta) is None
    assert validate_forbidden_keys(None, forbidden_meta) is None
    assert validate_min_keys(None, min_meta) is None
    assert validate_max_keys(None, max_meta) is None


# Property: Error results are always non-empty tuples of strings


@given(value=st.integers(max_value=0))
def test_errors_are_non_empty_string_tuples_numeric(value):
    metadata = IsPositive()

    result = validate_is_positive(value, metadata)

    if result is not None:
        assert isinstance(result, tuple)
        assert len(result) > 0
        assert all(isinstance(err, str) for err in result)
        assert all(len(err) > 0 for err in result)


@given(
    threshold=st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)),
    days_after=st.integers(min_value=0, max_value=365),
)
def test_errors_are_non_empty_string_tuples_datetime(threshold, days_after):
    metadata = BeforeDate(before=threshold)
    value = date.fromordinal(threshold.toordinal() + days_after)

    result = validate_before_date(value, metadata)

    if result is not None:
        assert isinstance(result, tuple)
        assert len(result) > 0
        assert all(isinstance(err, str) for err in result)
        assert all(len(err) > 0 for err in result)


@given(
    items=st.lists(st.integers(), min_size=2, max_size=10),
    duplicate=st.integers(),
)
def test_errors_are_non_empty_string_tuples_sequence(items, duplicate):
    metadata = UniqueItems()
    value = [*items, duplicate, duplicate]

    result = validate_unique_items(value, metadata)

    if result is not None:
        assert isinstance(result, tuple)
        assert len(result) > 0
        assert all(isinstance(err, str) for err in result)
        assert all(len(err) > 0 for err in result)


@given(
    required=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=10,
        ),
        min_size=2,
        max_size=5,
        unique=True,
    )
)
def test_errors_are_non_empty_string_tuples_mapping(required):
    metadata = RequiredKeys(keys=tuple(required))
    # Build dict missing some keys
    value = {required[0]: 1}

    result = validate_required_keys(value, metadata)

    if result is not None:
        assert isinstance(result, tuple)
        assert len(result) > 0
        assert all(isinstance(err, str) for err in result)
        assert all(len(err) > 0 for err in result)
