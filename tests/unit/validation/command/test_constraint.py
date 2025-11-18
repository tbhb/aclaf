"""Unit tests for command constraint validators."""


from aclaf.validation.command._constraint import (
    AtLeastOneOf,
    AtMostOneOf,
    ExactlyOneOf,
    MutuallyExclusive,
    validate_at_least_one_of,
    validate_at_most_one_of,
    validate_exactly_one_of,
    validate_mutually_exclusive,
)


class TestMutuallyExclusive:
    def test_validates_no_parameters_provided(self):
        metadata = MutuallyExclusive(parameter_names=("verbose", "quiet"))
        value = {"verbose": None, "quiet": None}

        result = validate_mutually_exclusive(value, metadata)

        assert result is None

    def test_validates_one_parameter_provided(self):
        metadata = MutuallyExclusive(parameter_names=("verbose", "quiet"))
        value = {"verbose": True, "quiet": None}

        result = validate_mutually_exclusive(value, metadata)

        assert result is None

    def test_rejects_two_parameters_provided(self):
        metadata = MutuallyExclusive(parameter_names=("verbose", "quiet"))
        value = {"verbose": True, "quiet": True}

        result = validate_mutually_exclusive(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "mutually exclusive" in result[0]
        assert "'verbose'" in result[0]
        assert "'quiet'" in result[0]

    def test_rejects_all_parameters_provided(self):
        metadata = MutuallyExclusive(parameter_names=("a", "b", "c"))
        value = {"a": 1, "b": 2, "c": 3}

        result = validate_mutually_exclusive(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "mutually exclusive" in result[0]

    def test_ignores_none_values(self):
        metadata = MutuallyExclusive(parameter_names=("verbose", "quiet", "debug"))
        value = {"verbose": True, "quiet": None, "debug": None}

        result = validate_mutually_exclusive(value, metadata)

        assert result is None

    def test_ignores_missing_keys(self):
        metadata = MutuallyExclusive(parameter_names=("verbose", "quiet"))
        value = {"verbose": True}

        result = validate_mutually_exclusive(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = MutuallyExclusive(parameter_names=("verbose", "quiet"))
        value = "not a mapping"

        result = validate_mutually_exclusive(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "require parameter mapping" in result[0]

    def test_validates_empty_parameter_names(self):
        metadata = MutuallyExclusive(parameter_names=())
        value = {"a": 1, "b": 2}

        result = validate_mutually_exclusive(value, metadata)

        assert result is None

    def test_validates_single_parameter_name(self):
        metadata = MutuallyExclusive(parameter_names=("verbose",))
        value = {"verbose": True}

        result = validate_mutually_exclusive(value, metadata)

        assert result is None


class TestExactlyOneOf:
    def test_validates_one_parameter_provided(self):
        metadata = ExactlyOneOf(parameter_names=("file", "stdin"))
        value = {"file": "input.txt", "stdin": None}

        result = validate_exactly_one_of(value, metadata)

        assert result is None

    def test_rejects_zero_parameters_provided(self):
        metadata = ExactlyOneOf(parameter_names=("file", "stdin"))
        value = {"file": None, "stdin": None}

        result = validate_exactly_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "Exactly one" in result[0]
        assert "must be provided" in result[0]

    def test_rejects_two_parameters_provided(self):
        metadata = ExactlyOneOf(parameter_names=("file", "stdin"))
        value = {"file": "input.txt", "stdin": True}

        result = validate_exactly_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "Exactly one" in result[0]
        assert "'file'" in result[0]
        assert "'stdin'" in result[0]

    def test_rejects_all_three_parameters_provided(self):
        metadata = ExactlyOneOf(parameter_names=("a", "b", "c"))
        value = {"a": 1, "b": 2, "c": 3}

        result = validate_exactly_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1

    def test_ignores_none_values(self):
        metadata = ExactlyOneOf(parameter_names=("file", "stdin", "url"))
        value = {"file": "input.txt", "stdin": None, "url": None}

        result = validate_exactly_one_of(value, metadata)

        assert result is None

    def test_ignores_missing_keys(self):
        metadata = ExactlyOneOf(parameter_names=("file", "stdin"))
        value = {"file": "input.txt"}

        result = validate_exactly_one_of(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = ExactlyOneOf(parameter_names=("file", "stdin"))
        value = 42

        result = validate_exactly_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "require parameter mapping" in result[0]

    def test_validates_with_boolean_false(self):
        metadata = ExactlyOneOf(parameter_names=("enable", "disable"))
        value = {"enable": False, "disable": None}

        result = validate_exactly_one_of(value, metadata)

        assert result is None


class TestAtLeastOneOf:
    def test_validates_one_parameter_provided(self):
        metadata = AtLeastOneOf(parameter_names=("name", "id", "email"))
        value = {"name": "Alice", "id": None, "email": None}

        result = validate_at_least_one_of(value, metadata)

        assert result is None

    def test_validates_two_parameters_provided(self):
        metadata = AtLeastOneOf(parameter_names=("name", "id", "email"))
        value = {"name": "Alice", "id": 123, "email": None}

        result = validate_at_least_one_of(value, metadata)

        assert result is None

    def test_validates_all_parameters_provided(self):
        metadata = AtLeastOneOf(parameter_names=("name", "id", "email"))
        value = {"name": "Alice", "id": 123, "email": "alice@example.com"}

        result = validate_at_least_one_of(value, metadata)

        assert result is None

    def test_rejects_zero_parameters_provided(self):
        metadata = AtLeastOneOf(parameter_names=("name", "id", "email"))
        value = {"name": None, "id": None, "email": None}

        result = validate_at_least_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "At least one" in result[0]
        assert "must be provided" in result[0]

    def test_ignores_none_values(self):
        metadata = AtLeastOneOf(parameter_names=("a", "b", "c"))
        value = {"a": None, "b": 2, "c": None}

        result = validate_at_least_one_of(value, metadata)

        assert result is None

    def test_ignores_missing_keys(self):
        metadata = AtLeastOneOf(parameter_names=("a", "b"))
        value = {"a": 1}

        result = validate_at_least_one_of(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = AtLeastOneOf(parameter_names=("a", "b"))
        value = []

        result = validate_at_least_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "require parameter mapping" in result[0]


class TestAtMostOneOf:
    def test_validates_zero_parameters_provided(self):
        metadata = AtMostOneOf(parameter_names=("cache", "no_cache"))
        value = {"cache": None, "no_cache": None}

        result = validate_at_most_one_of(value, metadata)

        assert result is None

    def test_validates_one_parameter_provided(self):
        metadata = AtMostOneOf(parameter_names=("cache", "no_cache"))
        value = {"cache": True, "no_cache": None}

        result = validate_at_most_one_of(value, metadata)

        assert result is None

    def test_rejects_two_parameters_provided(self):
        metadata = AtMostOneOf(parameter_names=("cache", "no_cache"))
        value = {"cache": True, "no_cache": True}

        result = validate_at_most_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "At most one" in result[0]
        assert "can be provided" in result[0]

    def test_rejects_all_parameters_provided(self):
        metadata = AtMostOneOf(parameter_names=("a", "b", "c"))
        value = {"a": 1, "b": 2, "c": 3}

        result = validate_at_most_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1

    def test_ignores_none_values(self):
        metadata = AtMostOneOf(parameter_names=("a", "b", "c"))
        value = {"a": 1, "b": None, "c": None}

        result = validate_at_most_one_of(value, metadata)

        assert result is None

    def test_ignores_missing_keys(self):
        metadata = AtMostOneOf(parameter_names=("a", "b"))
        value = {"a": 1}

        result = validate_at_most_one_of(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = AtMostOneOf(parameter_names=("a", "b"))
        value = None

        result = validate_at_most_one_of(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "require parameter mapping" in result[0]
