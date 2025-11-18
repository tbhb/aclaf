"""Unit tests for comparison parameter validators."""

from annotated_types import Ge, Gt, Le, Lt, MaxLen, MinLen

from aclaf.validation.parameter._comparison import (
    validate_ge,
    validate_gt,
    validate_le,
    validate_lt,
    validate_max_len,
    validate_min_len,
)


class TestValidateGt:
    def test_validates_value_greater_than_threshold(self):
        metadata = Gt(10)
        value = 11

        result = validate_gt(value, metadata)

        assert result is None

    def test_rejects_value_equal_to_threshold(self):
        metadata = Gt(10)
        value = 10

        result = validate_gt(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be greater than 10" in result[0]

    def test_rejects_value_less_than_threshold(self):
        metadata = Gt(10)
        value = 9

        result = validate_gt(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be greater than 10" in result[0]

    def test_validates_float_greater_than_threshold(self):
        metadata = Gt(5.5)
        value = 5.6

        result = validate_gt(value, metadata)

        assert result is None

    def test_rejects_float_equal_to_threshold(self):
        metadata = Gt(5.5)
        value = 5.5

        result = validate_gt(value, metadata)

        assert result is not None

    def test_validates_negative_values(self):
        metadata = Gt(-10)
        value = -5

        result = validate_gt(value, metadata)

        assert result is None

    def test_rejects_incomparable_types(self):
        metadata = Gt(10)
        value = "not a number"

        result = validate_gt(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "cannot be compared with 10" in result[0]

    def test_validates_string_comparison(self):
        metadata = Gt("apple")
        value = "banana"

        result = validate_gt(value, metadata)

        assert result is None

    def test_rejects_string_less_than_threshold(self):
        metadata = Gt("banana")
        value = "apple"

        result = validate_gt(value, metadata)

        assert result is not None


class TestValidateGe:
    def test_validates_value_greater_than_threshold(self):
        metadata = Ge(10)
        value = 11

        result = validate_ge(value, metadata)

        assert result is None

    def test_validates_value_equal_to_threshold(self):
        metadata = Ge(10)
        value = 10

        result = validate_ge(value, metadata)

        assert result is None

    def test_rejects_value_less_than_threshold(self):
        metadata = Ge(10)
        value = 9

        result = validate_ge(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be greater than or equal to 10" in result[0]

    def test_validates_float_equal_to_threshold(self):
        metadata = Ge(5.5)
        value = 5.5

        result = validate_ge(value, metadata)

        assert result is None

    def test_validates_float_greater_than_threshold(self):
        metadata = Ge(5.5)
        value = 5.6

        result = validate_ge(value, metadata)

        assert result is None

    def test_rejects_float_less_than_threshold(self):
        metadata = Ge(5.5)
        value = 5.4

        result = validate_ge(value, metadata)

        assert result is not None

    def test_validates_zero_as_threshold(self):
        metadata = Ge(0)
        value = 0

        result = validate_ge(value, metadata)

        assert result is None

    def test_rejects_incomparable_types(self):
        metadata = Ge(10)
        value = "not a number"

        result = validate_ge(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "cannot be compared with 10" in result[0]


class TestValidateLt:
    def test_validates_value_less_than_threshold(self):
        metadata = Lt(10)
        value = 9

        result = validate_lt(value, metadata)

        assert result is None

    def test_rejects_value_equal_to_threshold(self):
        metadata = Lt(10)
        value = 10

        result = validate_lt(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be less than 10" in result[0]

    def test_rejects_value_greater_than_threshold(self):
        metadata = Lt(10)
        value = 11

        result = validate_lt(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be less than 10" in result[0]

    def test_validates_float_less_than_threshold(self):
        metadata = Lt(5.5)
        value = 5.4

        result = validate_lt(value, metadata)

        assert result is None

    def test_rejects_float_equal_to_threshold(self):
        metadata = Lt(5.5)
        value = 5.5

        result = validate_lt(value, metadata)

        assert result is not None

    def test_validates_negative_values(self):
        metadata = Lt(-5)
        value = -10

        result = validate_lt(value, metadata)

        assert result is None

    def test_rejects_incomparable_types(self):
        metadata = Lt(10)
        value = "not a number"

        result = validate_lt(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "cannot be compared with 10" in result[0]


class TestValidateLe:
    def test_validates_value_less_than_threshold(self):
        metadata = Le(10)
        value = 9

        result = validate_le(value, metadata)

        assert result is None

    def test_validates_value_equal_to_threshold(self):
        metadata = Le(10)
        value = 10

        result = validate_le(value, metadata)

        assert result is None

    def test_rejects_value_greater_than_threshold(self):
        metadata = Le(10)
        value = 11

        result = validate_le(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be less than or equal to 10" in result[0]

    def test_validates_float_equal_to_threshold(self):
        metadata = Le(5.5)
        value = 5.5

        result = validate_le(value, metadata)

        assert result is None

    def test_validates_float_less_than_threshold(self):
        metadata = Le(5.5)
        value = 5.4

        result = validate_le(value, metadata)

        assert result is None

    def test_rejects_float_greater_than_threshold(self):
        metadata = Le(5.5)
        value = 5.6

        result = validate_le(value, metadata)

        assert result is not None

    def test_validates_zero_as_threshold(self):
        metadata = Le(0)
        value = 0

        result = validate_le(value, metadata)

        assert result is None

    def test_rejects_incomparable_types(self):
        metadata = Le(10)
        value = "not a number"

        result = validate_le(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "cannot be compared with 10" in result[0]


class TestValidateMinLen:
    def test_validates_string_meeting_minimum_length(self):
        metadata = MinLen(5)
        value = "hello"

        result = validate_min_len(value, metadata)

        assert result is None

    def test_validates_string_exceeding_minimum_length(self):
        metadata = MinLen(5)
        value = "hello world"

        result = validate_min_len(value, metadata)

        assert result is None

    def test_rejects_string_below_minimum_length(self):
        metadata = MinLen(5)
        value = "hi"

        result = validate_min_len(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "length must be at least 5" in result[0]

    def test_validates_empty_string_with_zero_minimum(self):
        metadata = MinLen(0)
        value = ""

        result = validate_min_len(value, metadata)

        assert result is None

    def test_rejects_empty_string_with_nonzero_minimum(self):
        metadata = MinLen(1)
        value = ""

        result = validate_min_len(value, metadata)

        assert result is not None

    def test_validates_list_meeting_minimum_length(self):
        metadata = MinLen(3)
        value = [1, 2, 3]

        result = validate_min_len(value, metadata)

        assert result is None

    def test_rejects_list_below_minimum_length(self):
        metadata = MinLen(3)
        value = [1, 2]

        result = validate_min_len(value, metadata)

        assert result is not None

    def test_validates_dict_meeting_minimum_length(self):
        metadata = MinLen(2)
        value = {"a": 1, "b": 2}

        result = validate_min_len(value, metadata)

        assert result is None

    def test_rejects_dict_below_minimum_length(self):
        metadata = MinLen(2)
        value = {"a": 1}

        result = validate_min_len(value, metadata)

        assert result is not None

    def test_rejects_value_without_length(self):
        metadata = MinLen(5)
        value = 123

        result = validate_min_len(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "length cannot be determined" in result[0]

    def test_validates_tuple_meeting_minimum_length(self):
        metadata = MinLen(2)
        value = (1, 2, 3)

        result = validate_min_len(value, metadata)

        assert result is None


class TestValidateMaxLen:
    def test_validates_string_meeting_maximum_length(self):
        metadata = MaxLen(5)
        value = "hello"

        result = validate_max_len(value, metadata)

        assert result is None

    def test_validates_string_below_maximum_length(self):
        metadata = MaxLen(5)
        value = "hi"

        result = validate_max_len(value, metadata)

        assert result is None

    def test_rejects_string_exceeding_maximum_length(self):
        metadata = MaxLen(5)
        value = "hello world"

        result = validate_max_len(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "length must be at most 5" in result[0]

    def test_validates_empty_string(self):
        metadata = MaxLen(5)
        value = ""

        result = validate_max_len(value, metadata)

        assert result is None

    def test_validates_list_meeting_maximum_length(self):
        metadata = MaxLen(3)
        value = [1, 2, 3]

        result = validate_max_len(value, metadata)

        assert result is None

    def test_rejects_list_exceeding_maximum_length(self):
        metadata = MaxLen(3)
        value = [1, 2, 3, 4]

        result = validate_max_len(value, metadata)

        assert result is not None

    def test_validates_dict_meeting_maximum_length(self):
        metadata = MaxLen(2)
        value = {"a": 1, "b": 2}

        result = validate_max_len(value, metadata)

        assert result is None

    def test_rejects_dict_exceeding_maximum_length(self):
        metadata = MaxLen(2)
        value = {"a": 1, "b": 2, "c": 3}

        result = validate_max_len(value, metadata)

        assert result is not None

    def test_rejects_value_without_length(self):
        metadata = MaxLen(5)
        value = 123

        result = validate_max_len(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "length cannot be determined" in result[0]

    def test_validates_zero_maximum_length_with_empty_string(self):
        metadata = MaxLen(0)
        value = ""

        result = validate_max_len(value, metadata)

        assert result is None

    def test_rejects_non_empty_string_with_zero_maximum(self):
        metadata = MaxLen(0)
        value = "a"

        result = validate_max_len(value, metadata)

        assert result is not None
