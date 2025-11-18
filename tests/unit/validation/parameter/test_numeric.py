"""Unit tests for numeric parameter validators."""

from annotated_types import Interval, MultipleOf

from aclaf.validation.parameter import (
    IsInteger,
    IsNegative,
    IsNonNegative,
    IsNonPositive,
    IsPositive,
    Precision,
    validate_interval,
    validate_is_integer,
    validate_is_negative,
    validate_is_non_negative,
    validate_is_non_positive,
    validate_is_positive,
    validate_multiple_of,
    validate_precision,
)


class TestMultipleOf:
    def test_validates_exact_multiple(self):
        metadata = MultipleOf(5)
        value = 15

        result = validate_multiple_of(value, metadata)

        assert result is None

    def test_validates_zero_as_multiple(self):
        metadata = MultipleOf(5)
        value = 0

        result = validate_multiple_of(value, metadata)

        assert result is None

    def test_rejects_non_multiple(self):
        metadata = MultipleOf(5)
        value = 17

        result = validate_multiple_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a multiple of 5" in result[0]

    def test_validates_float_multiple(self):
        metadata = MultipleOf(0.5)
        value = 2.5

        result = validate_multiple_of(value, metadata)

        assert result is None

    def test_rejects_float_non_multiple(self):
        metadata = MultipleOf(0.5)
        value = 2.3

        result = validate_multiple_of(value, metadata)

        assert result is not None

    def test_rejects_non_numeric_value(self):
        metadata = MultipleOf(5)
        value = "not a number"

        result = validate_multiple_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "cannot be divided" in result[0]


class TestInterval:
    def test_validates_value_within_inclusive_bounds(self):
        metadata = Interval(ge=0, le=10)
        value = 5

        result = validate_interval(value, metadata)

        assert result is None

    def test_validates_value_at_inclusive_lower_bound(self):
        metadata = Interval(ge=0, le=10)
        value = 0

        result = validate_interval(value, metadata)

        assert result is None

    def test_validates_value_at_inclusive_upper_bound(self):
        metadata = Interval(ge=0, le=10)
        value = 10

        result = validate_interval(value, metadata)

        assert result is None

    def test_rejects_value_below_inclusive_lower_bound(self):
        metadata = Interval(ge=0, le=10)
        value = -1

        result = validate_interval(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "greater than or equal to 0" in result[0]

    def test_rejects_value_above_inclusive_upper_bound(self):
        metadata = Interval(ge=0, le=10)
        value = 11

        result = validate_interval(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "less than or equal to 10" in result[0]

    def test_validates_value_within_exclusive_bounds(self):
        metadata = Interval(gt=0, lt=10)
        value = 5

        result = validate_interval(value, metadata)

        assert result is None

    def test_rejects_value_at_exclusive_lower_bound(self):
        metadata = Interval(gt=0, lt=10)
        value = 0

        result = validate_interval(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "greater than 0" in result[0]

    def test_rejects_value_at_exclusive_upper_bound(self):
        metadata = Interval(gt=0, lt=10)
        value = 10

        result = validate_interval(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "less than 10" in result[0]

    def test_validates_mixed_inclusive_exclusive_bounds(self):
        metadata = Interval(ge=0, lt=10)
        value = 0

        result = validate_interval(value, metadata)

        assert result is None

    def test_rejects_mixed_bounds_violation(self):
        metadata = Interval(ge=0, lt=10)
        value = 10

        result = validate_interval(value, metadata)

        assert result is not None

    def test_validates_none_value(self):
        metadata = Interval(ge=0, le=10)
        value = None

        result = validate_interval(value, metadata)

        assert result is None

    def test_rejects_non_numeric_value(self):
        metadata = Interval(ge=0, le=10)
        value = "not a number"

        result = validate_interval(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a number" in result[0]

    def test_validates_float_in_range(self):
        metadata = Interval(ge=0.0, le=1.0)
        value = 0.5

        result = validate_interval(value, metadata)

        assert result is None

    def test_validates_only_lower_bound(self):
        metadata = Interval(ge=0)
        value = 100

        result = validate_interval(value, metadata)

        assert result is None

    def test_validates_only_upper_bound(self):
        metadata = Interval(le=100)
        value = 50

        result = validate_interval(value, metadata)

        assert result is None

    def test_collects_multiple_bound_violations(self):
        metadata = Interval(ge=10, le=20)
        value = 5

        result = validate_interval(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "greater than or equal to 10" in result[0]


class TestIsInteger:
    def test_validates_integer(self):
        metadata = IsInteger()
        value = 42

        result = validate_is_integer(value, metadata)

        assert result is None

    def test_validates_zero(self):
        metadata = IsInteger()
        value = 0

        result = validate_is_integer(value, metadata)

        assert result is None

    def test_validates_negative_integer(self):
        metadata = IsInteger()
        value = -10

        result = validate_is_integer(value, metadata)

        assert result is None

    def test_validates_float_with_no_decimal(self):
        metadata = IsInteger()
        value = 5.0

        result = validate_is_integer(value, metadata)

        assert result is None

    def test_rejects_float_with_decimal(self):
        metadata = IsInteger()
        value = 5.5

        result = validate_is_integer(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a whole number" in result[0]

    def test_rejects_non_numeric_value(self):
        metadata = IsInteger()
        value = "not a number"

        result = validate_is_integer(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a number" in result[0]

    def test_validates_none_value(self):
        metadata = IsInteger()
        value = None

        result = validate_is_integer(value, metadata)

        assert result is None


class TestIsPositive:
    def test_validates_positive_integer(self):
        metadata = IsPositive()
        value = 10

        result = validate_is_positive(value, metadata)

        assert result is None

    def test_validates_positive_float(self):
        metadata = IsPositive()
        value = 0.1

        result = validate_is_positive(value, metadata)

        assert result is None

    def test_rejects_zero(self):
        metadata = IsPositive()
        value = 0

        result = validate_is_positive(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be greater than 0" in result[0]
        assert "got 0" in result[0]

    def test_rejects_negative_value(self):
        metadata = IsPositive()
        value = -5

        result = validate_is_positive(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be greater than 0" in result[0]

    def test_rejects_non_numeric_value(self):
        metadata = IsPositive()
        value = "not a number"

        result = validate_is_positive(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a number" in result[0]

    def test_validates_none_value(self):
        metadata = IsPositive()
        value = None

        result = validate_is_positive(value, metadata)

        assert result is None


class TestIsNegative:
    def test_validates_negative_integer(self):
        metadata = IsNegative()
        value = -10

        result = validate_is_negative(value, metadata)

        assert result is None

    def test_validates_negative_float(self):
        metadata = IsNegative()
        value = -0.1

        result = validate_is_negative(value, metadata)

        assert result is None

    def test_rejects_zero(self):
        metadata = IsNegative()
        value = 0

        result = validate_is_negative(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be less than 0" in result[0]
        assert "got 0" in result[0]

    def test_rejects_positive_value(self):
        metadata = IsNegative()
        value = 5

        result = validate_is_negative(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be less than 0" in result[0]

    def test_rejects_non_numeric_value(self):
        metadata = IsNegative()
        value = "not a number"

        result = validate_is_negative(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a number" in result[0]

    def test_validates_none_value(self):
        metadata = IsNegative()
        value = None

        result = validate_is_negative(value, metadata)

        assert result is None


class TestIsNonNegative:
    def test_validates_positive_value(self):
        metadata = IsNonNegative()
        value = 10

        result = validate_is_non_negative(value, metadata)

        assert result is None

    def test_validates_zero(self):
        metadata = IsNonNegative()
        value = 0

        result = validate_is_non_negative(value, metadata)

        assert result is None

    def test_validates_positive_float(self):
        metadata = IsNonNegative()
        value = 0.1

        result = validate_is_non_negative(value, metadata)

        assert result is None

    def test_rejects_negative_value(self):
        metadata = IsNonNegative()
        value = -5

        result = validate_is_non_negative(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be greater than or equal to 0" in result[0]
        assert "got -5" in result[0]

    def test_rejects_non_numeric_value(self):
        metadata = IsNonNegative()
        value = "not a number"

        result = validate_is_non_negative(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a number" in result[0]

    def test_validates_none_value(self):
        metadata = IsNonNegative()
        value = None

        result = validate_is_non_negative(value, metadata)

        assert result is None


class TestIsNonPositive:
    def test_validates_negative_value(self):
        metadata = IsNonPositive()
        value = -10

        result = validate_is_non_positive(value, metadata)

        assert result is None

    def test_validates_zero(self):
        metadata = IsNonPositive()
        value = 0

        result = validate_is_non_positive(value, metadata)

        assert result is None

    def test_validates_negative_float(self):
        metadata = IsNonPositive()
        value = -0.1

        result = validate_is_non_positive(value, metadata)

        assert result is None

    def test_rejects_positive_value(self):
        metadata = IsNonPositive()
        value = 5

        result = validate_is_non_positive(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be less than or equal to 0" in result[0]
        assert "got 5" in result[0]

    def test_rejects_non_numeric_value(self):
        metadata = IsNonPositive()
        value = "not a number"

        result = validate_is_non_positive(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a number" in result[0]

    def test_validates_none_value(self):
        metadata = IsNonPositive()
        value = None

        result = validate_is_non_positive(value, metadata)

        assert result is None


class TestPrecision:
    def test_validates_integer(self):
        metadata = Precision(max_decimals=2)
        value = 42

        result = validate_precision(value, metadata)

        assert result is None

    def test_validates_float_within_precision(self):
        metadata = Precision(max_decimals=2)
        value = 3.14

        result = validate_precision(value, metadata)

        assert result is None

    def test_validates_float_at_exact_precision(self):
        metadata = Precision(max_decimals=3)
        value = 1.234

        result = validate_precision(value, metadata)

        assert result is None

    def test_rejects_float_exceeding_precision(self):
        metadata = Precision(max_decimals=2)
        value = 3.141

        result = validate_precision(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must have at most 2 decimal places" in result[0]
        assert "got 3" in result[0]

    def test_validates_zero_decimal_places(self):
        metadata = Precision(max_decimals=0)
        # 5 as integer has no decimal places
        value = 5

        result = validate_precision(value, metadata)

        assert result is None

    def test_rejects_decimal_when_zero_allowed(self):
        metadata = Precision(max_decimals=0)
        value = 5.1

        result = validate_precision(value, metadata)

        assert result is not None

    def test_validates_none_value(self):
        metadata = Precision(max_decimals=2)
        value = None

        result = validate_precision(value, metadata)

        assert result is None

    def test_rejects_non_numeric_value(self):
        metadata = Precision(max_decimals=2)
        value = "not a number"

        result = validate_precision(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a number" in result[0]

    def test_validates_small_decimal(self):
        metadata = Precision(max_decimals=5)
        value = 0.00001

        result = validate_precision(value, metadata)

        assert result is None

    def test_handles_float_precision_edge_case(self):
        metadata = Precision(max_decimals=2)
        value = 1.005

        result = validate_precision(value, metadata)

        assert result is not None
