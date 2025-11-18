"""Unit tests for mapping parameter validators."""

from aclaf.validation.parameter import (
    ForbiddenKeys,
    KeyPattern,
    MaxKeys,
    MinKeys,
    RequiredKeys,
    ValuePattern,
    ValueType,
    validate_forbidden_keys,
    validate_key_pattern,
    validate_max_keys,
    validate_min_keys,
    validate_required_keys,
    validate_value_pattern,
    validate_value_type,
)


class TestRequiredKeys:
    def test_validates_all_required_keys_present(self):
        metadata = RequiredKeys(keys=("name", "age"))
        value = {"name": "Alice", "age": 30}

        result = validate_required_keys(value, metadata)

        assert result is None

    def test_validates_extra_keys_present(self):
        metadata = RequiredKeys(keys=("name", "age"))
        value = {"name": "Alice", "age": 30, "city": "NYC"}

        result = validate_required_keys(value, metadata)

        assert result is None

    def test_rejects_one_missing_key(self):
        metadata = RequiredKeys(keys=("name", "age"))
        value = {"name": "Alice"}

        result = validate_required_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "missing required keys" in result[0]
        assert "'age'" in result[0]

    def test_rejects_multiple_missing_keys(self):
        metadata = RequiredKeys(keys=("name", "age", "city"))
        value = {"name": "Alice"}

        result = validate_required_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'age'" in result[0]
        assert "'city'" in result[0]

    def test_validates_empty_required_keys(self):
        metadata = RequiredKeys(keys=())
        value = {"name": "Alice"}

        result = validate_required_keys(value, metadata)

        assert result is None

    def test_validates_empty_dict_with_no_required_keys(self):
        metadata = RequiredKeys(keys=())
        value = {}

        result = validate_required_keys(value, metadata)

        assert result is None

    def test_validates_none_value(self):
        metadata = RequiredKeys(keys=("name",))
        value = None

        result = validate_required_keys(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = RequiredKeys(keys=("name",))
        value = ["name", "Alice"]

        result = validate_required_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a mapping" in result[0]


class TestForbiddenKeys:
    def test_validates_no_forbidden_keys_present(self):
        metadata = ForbiddenKeys(keys=("password", "secret"))
        value = {"name": "Alice", "age": 30}

        result = validate_forbidden_keys(value, metadata)

        assert result is None

    def test_validates_empty_dict(self):
        metadata = ForbiddenKeys(keys=("password", "secret"))
        value = {}

        result = validate_forbidden_keys(value, metadata)

        assert result is None

    def test_rejects_one_forbidden_key_present(self):
        metadata = ForbiddenKeys(keys=("password", "secret"))
        value = {"name": "Alice", "password": "123"}

        result = validate_forbidden_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "forbidden keys present" in result[0]
        assert "'password'" in result[0]

    def test_rejects_multiple_forbidden_keys_present(self):
        metadata = ForbiddenKeys(keys=("password", "secret", "token"))
        value = {"name": "Alice", "password": "123", "secret": "xyz"}

        result = validate_forbidden_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'password'" in result[0]
        assert "'secret'" in result[0]

    def test_validates_empty_forbidden_keys(self):
        metadata = ForbiddenKeys(keys=())
        value = {"password": "123", "secret": "xyz"}

        result = validate_forbidden_keys(value, metadata)

        assert result is None

    def test_validates_none_value(self):
        metadata = ForbiddenKeys(keys=("password",))
        value = None

        result = validate_forbidden_keys(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = ForbiddenKeys(keys=("password",))
        value = "not a dict"

        result = validate_forbidden_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a mapping" in result[0]


class TestKeyPattern:
    def test_validates_all_keys_match_pattern(self):
        metadata = KeyPattern(pattern=r"^[a-z]+$")
        value = {"name": "Alice", "age": "30"}

        result = validate_key_pattern(value, metadata)

        assert result is None

    def test_validates_empty_dict(self):
        metadata = KeyPattern(pattern=r"^[a-z]+$")
        value = {}

        result = validate_key_pattern(value, metadata)

        assert result is None

    def test_rejects_one_key_not_matching(self):
        metadata = KeyPattern(pattern=r"^[a-z]+$")
        value = {"name": "Alice", "AGE": "30"}

        result = validate_key_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must match pattern" in result[0]
        assert "'AGE'" in result[0]

    def test_rejects_multiple_keys_not_matching(self):
        metadata = KeyPattern(pattern=r"^[a-z]+$")
        value = {"name": "Alice", "AGE": "30", "City": "NYC"}

        result = validate_key_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'AGE'" in result[0]
        assert "'City'" in result[0]

    def test_rejects_non_string_keys(self):
        metadata = KeyPattern(pattern=r"^[a-z]+$")
        value = {1: "one", "name": "Alice"}

        result = validate_key_pattern(value, metadata)

        assert result is not None
        assert "1" in result[0]

    def test_limits_error_message_to_five_keys(self):
        metadata = KeyPattern(pattern=r"^[a-z]+$")
        value = {str(i): i for i in range(10)}

        result = validate_key_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "10 keys do not match" in result[0]
        assert "First 5:" in result[0]

    def test_rejects_invalid_regex_pattern(self):
        metadata = KeyPattern(pattern=r"[invalid(")
        value = {"name": "Alice"}

        result = validate_key_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "invalid regex pattern" in result[0]

    def test_validates_none_value(self):
        metadata = KeyPattern(pattern=r"^[a-z]+$")
        value = None

        result = validate_key_pattern(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = KeyPattern(pattern=r"^[a-z]+$")
        value = 42

        result = validate_key_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a mapping" in result[0]


class TestValuePattern:
    def test_validates_all_string_values_match_pattern(self):
        metadata = ValuePattern(pattern=r"^[A-Z][a-z]+$")
        value = {"first": "Alice", "last": "Smith"}

        result = validate_value_pattern(value, metadata)

        assert result is None

    def test_validates_empty_dict(self):
        metadata = ValuePattern(pattern=r"^[A-Z][a-z]+$")
        value = {}

        result = validate_value_pattern(value, metadata)

        assert result is None

    def test_rejects_one_value_not_matching(self):
        metadata = ValuePattern(pattern=r"^[A-Z][a-z]+$")
        value = {"first": "Alice", "last": "smith"}

        result = validate_value_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must match pattern" in result[0]
        assert "'last'='smith'" in result[0]

    def test_rejects_multiple_values_not_matching(self):
        metadata = ValuePattern(pattern=r"^[A-Z][a-z]+$")
        value = {"first": "alice", "last": "smith", "city": "NYC"}

        result = validate_value_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'first'='alice'" in result[0]
        assert "'last'='smith'" in result[0]

    def test_ignores_non_string_values(self):
        metadata = ValuePattern(pattern=r"^[A-Z][a-z]+$")
        value = {"name": "Alice", "age": 30}

        result = validate_value_pattern(value, metadata)

        assert result is None

    def test_limits_error_message_to_five_values(self):
        metadata = ValuePattern(pattern=r"^[A-Z][a-z]+$")
        value = {str(i): "invalid" for i in range(10)}

        result = validate_value_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "10 values do not match" in result[0]
        assert "First 5:" in result[0]

    def test_rejects_invalid_regex_pattern(self):
        metadata = ValuePattern(pattern=r"[invalid(")
        value = {"name": "Alice"}

        result = validate_value_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "invalid regex pattern" in result[0]

    def test_validates_none_value(self):
        metadata = ValuePattern(pattern=r"^[A-Z][a-z]+$")
        value = None

        result = validate_value_pattern(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = ValuePattern(pattern=r"^[A-Z][a-z]+$")
        value = "not a dict"

        result = validate_value_pattern(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a mapping" in result[0]


class TestValueType:
    def test_validates_all_values_correct_type(self):
        metadata = ValueType(types=(str,))
        value = {"first": "Alice", "last": "Smith"}

        result = validate_value_type(value, metadata)

        assert result is None

    def test_validates_multiple_allowed_types(self):
        metadata = ValueType(types=(int, str))
        value = {"name": "Alice", "age": 30}

        result = validate_value_type(value, metadata)

        assert result is None

    def test_validates_empty_dict(self):
        metadata = ValueType(types=(str,))
        value = {}

        result = validate_value_type(value, metadata)

        assert result is None

    def test_rejects_one_value_wrong_type(self):
        metadata = ValueType(types=(str,))
        value = {"name": "Alice", "age": 30}

        result = validate_value_type(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be of type str" in result[0]
        assert "'age'=30 (int)" in result[0]

    def test_rejects_multiple_values_wrong_type(self):
        metadata = ValueType(types=(str,))
        value = {"name": "Alice", "age": 30, "score": 95.5}

        result = validate_value_type(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'age'=30 (int)" in result[0]
        assert "'score'=95.5 (float)" in result[0]

    def test_limits_error_message_to_five_values(self):
        metadata = ValueType(types=(str,))
        value = {str(i): i for i in range(10)}

        result = validate_value_type(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "10 values are not of type" in result[0]
        assert "First 5:" in result[0]

    def test_validates_none_value(self):
        metadata = ValueType(types=(str,))
        value = None

        result = validate_value_type(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = ValueType(types=(str,))
        value = ["Alice", "Smith"]

        result = validate_value_type(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a mapping" in result[0]


class TestMinKeys:
    def test_validates_dict_with_minimum_keys(self):
        metadata = MinKeys(min_keys=2)
        value = {"name": "Alice", "age": 30}

        result = validate_min_keys(value, metadata)

        assert result is None

    def test_validates_dict_exceeding_minimum(self):
        metadata = MinKeys(min_keys=2)
        value = {"name": "Alice", "age": 30, "city": "NYC"}

        result = validate_min_keys(value, metadata)

        assert result is None

    def test_rejects_dict_below_minimum(self):
        metadata = MinKeys(min_keys=3)
        value = {"name": "Alice", "age": 30}

        result = validate_min_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must have at least 3 keys" in result[0]
        assert "got 2" in result[0]

    def test_validates_empty_dict_with_zero_minimum(self):
        metadata = MinKeys(min_keys=0)
        value = {}

        result = validate_min_keys(value, metadata)

        assert result is None

    def test_rejects_empty_dict_with_positive_minimum(self):
        metadata = MinKeys(min_keys=1)
        value = {}

        result = validate_min_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must have at least 1 keys" in result[0]
        assert "got 0" in result[0]

    def test_validates_none_value(self):
        metadata = MinKeys(min_keys=2)
        value = None

        result = validate_min_keys(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = MinKeys(min_keys=2)
        value = 42

        result = validate_min_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a mapping" in result[0]


class TestMaxKeys:
    def test_validates_dict_below_maximum(self):
        metadata = MaxKeys(max_keys=3)
        value = {"name": "Alice", "age": 30}

        result = validate_max_keys(value, metadata)

        assert result is None

    def test_validates_dict_at_maximum(self):
        metadata = MaxKeys(max_keys=3)
        value = {"name": "Alice", "age": 30, "city": "NYC"}

        result = validate_max_keys(value, metadata)

        assert result is None

    def test_rejects_dict_exceeding_maximum(self):
        metadata = MaxKeys(max_keys=2)
        value = {"name": "Alice", "age": 30, "city": "NYC"}

        result = validate_max_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must have at most 2 keys" in result[0]
        assert "got 3" in result[0]

    def test_validates_empty_dict(self):
        metadata = MaxKeys(max_keys=5)
        value = {}

        result = validate_max_keys(value, metadata)

        assert result is None

    def test_rejects_empty_dict_with_zero_maximum(self):
        metadata = MaxKeys(max_keys=0)
        value = {"name": "Alice"}

        result = validate_max_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must have at most 0 keys" in result[0]

    def test_validates_none_value(self):
        metadata = MaxKeys(max_keys=2)
        value = None

        result = validate_max_keys(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = MaxKeys(max_keys=2)
        value = "not a dict"

        result = validate_max_keys(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a mapping" in result[0]
