"""Unit tests for command conflict validators."""


from aclaf.validation.command._conflict import (
    ConflictsWith,
    validate_conflicts_with,
)


class TestConflictsWith:
    def test_validates_no_parameters_provided(self):
        metadata = ConflictsWith(parameter_names=("production", "staging"))
        value = {"production": None, "staging": None}

        result = validate_conflicts_with(value, metadata)

        assert result is None

    def test_validates_one_parameter_provided(self):
        metadata = ConflictsWith(parameter_names=("production", "staging"))
        value = {"production": True, "staging": None}

        result = validate_conflicts_with(value, metadata)

        assert result is None

    def test_rejects_two_parameters_provided(self):
        metadata = ConflictsWith(parameter_names=("production", "staging"))
        value = {"production": True, "staging": True}

        result = validate_conflicts_with(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "conflict" in result[0]
        assert "'production'" in result[0]
        assert "'staging'" in result[0]

    def test_rejects_all_three_parameters_provided(self):
        metadata = ConflictsWith(parameter_names=("a", "b", "c"))
        value = {"a": 1, "b": 2, "c": 3}

        result = validate_conflicts_with(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "conflict" in result[0]

    def test_ignores_none_values(self):
        metadata = ConflictsWith(parameter_names=("prod", "stage", "dev"))
        value = {"prod": True, "stage": None, "dev": None}

        result = validate_conflicts_with(value, metadata)

        assert result is None

    def test_ignores_missing_keys(self):
        metadata = ConflictsWith(parameter_names=("prod", "stage"))
        value = {"prod": True}

        result = validate_conflicts_with(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = ConflictsWith(parameter_names=("prod", "stage"))
        value = "invalid"

        result = validate_conflicts_with(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "require parameter mapping" in result[0]

    def test_validates_empty_parameter_names(self):
        metadata = ConflictsWith(parameter_names=())
        value = {"a": 1, "b": 2}

        result = validate_conflicts_with(value, metadata)

        assert result is None

    def test_validates_single_parameter_name(self):
        metadata = ConflictsWith(parameter_names=("only",))
        value = {"only": True}

        result = validate_conflicts_with(value, metadata)

        assert result is None

    def test_validates_with_boolean_false(self):
        metadata = ConflictsWith(parameter_names=("a", "b"))
        value = {"a": False, "b": None}

        result = validate_conflicts_with(value, metadata)

        assert result is None
