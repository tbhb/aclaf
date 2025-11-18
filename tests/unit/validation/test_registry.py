from dataclasses import dataclass

import pytest
from annotated_types import BaseMetadata

from aclaf.validation import ValidatorRegistry


@dataclass(frozen=True, slots=True)
class MetadataA(BaseMetadata):
    value: str


@dataclass(frozen=True, slots=True)
class MetadataB(BaseMetadata):
    value: int


@dataclass(frozen=True, slots=True)
class MetadataC(BaseMetadata):
    value: float


def validator_always_passes(value, metadata):
    return None


def validator_always_fails(value, metadata):
    return ("Error message 1",)


def validator_multiple_errors(value, metadata):
    return ("Error 1", "Error 2", "Error 3")


def validator_conditional(value, metadata):
    if isinstance(value, str) and len(value) > 5:
        return ("String too long",)
    return None


class TestValidatorRegistryRegistration:
    def test_register_validator_succeeds(self):
        registry = ValidatorRegistry()

        registry.register(MetadataA, validator_always_passes)

        assert registry.has_validator(MetadataA)
        assert registry.get_validator(MetadataA) is validator_always_passes

    def test_register_multiple_validators_succeeds(self):
        registry = ValidatorRegistry()

        registry.register(MetadataA, validator_always_passes)
        registry.register(MetadataB, validator_always_fails)
        registry.register(MetadataC, validator_multiple_errors)

        assert registry.has_validator(MetadataA)
        assert registry.has_validator(MetadataB)
        assert registry.has_validator(MetadataC)
        assert registry.get_validator(MetadataA) is validator_always_passes
        assert registry.get_validator(MetadataB) is validator_always_fails
        assert registry.get_validator(MetadataC) is validator_multiple_errors

    def test_register_duplicate_key_raises_value_error(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(MetadataA, validator_always_fails)

    def test_register_duplicate_preserves_original_validator(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(MetadataA, validator_always_fails)

        assert registry.get_validator(MetadataA) is validator_always_passes

    def test_unregister_existing_validator_succeeds(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)

        registry.unregister(MetadataA)

        assert not registry.has_validator(MetadataA)
        assert registry.get_validator(MetadataA) is None

    def test_unregister_nonexistent_validator_raises_key_error(self):
        registry = ValidatorRegistry()

        with pytest.raises(KeyError):
            registry.unregister(MetadataA)

    def test_unregister_then_reregister_same_key_succeeds(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)
        registry.unregister(MetadataA)

        registry.register(MetadataA, validator_always_fails)

        assert registry.has_validator(MetadataA)
        assert registry.get_validator(MetadataA) is validator_always_fails

    def test_get_validator_returns_none_for_nonexistent_key(self):
        registry = ValidatorRegistry()

        result = registry.get_validator(MetadataA)

        assert result is None

    def test_get_validator_returns_correct_validator_for_existing_key(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)

        result = registry.get_validator(MetadataA)

        assert result is validator_always_passes

    def test_has_validator_returns_false_for_nonexistent_key(self):
        registry = ValidatorRegistry()

        result = registry.has_validator(MetadataA)

        assert result is False

    def test_has_validator_returns_true_for_existing_key(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)

        result = registry.has_validator(MetadataA)

        assert result is True


class TestValidatorRegistryValidation:
    def test_validate_with_no_validators_registered_returns_none(self):
        registry = ValidatorRegistry()
        metadata = (MetadataA(value="test"),)

        result = registry.validate("test_value", metadata)

        assert result is None

    def test_validate_with_no_metadata_returns_none(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)

        result = registry.validate("test_value", ())

        assert result is None

    def test_validate_with_single_passing_validator_returns_none(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)
        metadata = (MetadataA(value="test"),)

        result = registry.validate("test_value", metadata)

        assert result is None

    def test_validate_with_single_failing_validator_returns_errors(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_fails)
        metadata = (MetadataA(value="test"),)

        result = registry.validate("test_value", metadata)

        assert result is not None
        assert len(result) == 1
        assert result[0] == "Error message 1"

    def test_validate_with_multiple_passing_validators_returns_none(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)
        registry.register(MetadataB, validator_always_passes)
        metadata = (MetadataA(value="test"), MetadataB(value=42))

        result = registry.validate("test_value", metadata)

        assert result is None

    def test_validate_with_multiple_failing_validators_aggregates_errors(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_fails)
        registry.register(MetadataB, validator_multiple_errors)
        metadata = (MetadataA(value="test"), MetadataB(value=42))

        result = registry.validate("test_value", metadata)

        assert result is not None
        assert len(result) == 4
        assert result[0] == "Error message 1"
        assert result[1] == "Error 1"
        assert result[2] == "Error 2"
        assert result[3] == "Error 3"

    def test_validate_with_mixed_validators_returns_only_errors(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)
        registry.register(MetadataB, validator_always_fails)
        registry.register(MetadataC, validator_multiple_errors)
        metadata = (
            MetadataA(value="test"),
            MetadataB(value=42),
            MetadataC(value=3.14),
        )

        result = registry.validate("test_value", metadata)

        assert result is not None
        assert len(result) == 4
        assert "Error message 1" in result
        assert "Error 1" in result
        assert "Error 2" in result
        assert "Error 3" in result

    def test_validate_with_unregistered_metadata_skips_validation(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_fails)
        metadata = (MetadataA(value="test"), MetadataB(value=42))

        result = registry.validate("test_value", metadata)

        assert result is not None
        assert len(result) == 1
        assert result[0] == "Error message 1"

    def test_validate_calls_validator_with_correct_arguments(self):
        registry = ValidatorRegistry()
        called_with = []

        def capture_args(value, metadata):
            called_with.append((value, metadata))

        registry.register(MetadataA, capture_args)
        test_value = "test_value"
        test_metadata = MetadataA(value="test")
        metadata = (test_metadata,)

        registry.validate(test_value, metadata)

        assert len(called_with) == 1
        assert called_with[0][0] == test_value
        assert called_with[0][1] == test_metadata

    def test_validate_with_conditional_validator_passes_short_string(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_conditional)
        metadata = (MetadataA(value="test"),)

        result = registry.validate("short", metadata)

        assert result is None

    def test_validate_with_conditional_validator_fails_long_string(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_conditional)
        metadata = (MetadataA(value="test"),)

        result = registry.validate("very_long_string", metadata)

        assert result is not None
        assert len(result) == 1
        assert result[0] == "String too long"

    def test_validate_preserves_error_order(self):
        registry = ValidatorRegistry()

        def validator_errors_ordered(value, metadata):
            return ("Error A", "Error B", "Error C")

        registry.register(MetadataA, validator_errors_ordered)
        metadata = (MetadataA(value="test"),)

        result = registry.validate("test_value", metadata)

        assert result is not None
        assert result == ("Error A", "Error B", "Error C")

    def test_validate_with_none_value(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_passes)
        metadata = (MetadataA(value="test"),)

        result = registry.validate(None, metadata)

        assert result is None

    def test_validate_returns_tuple_not_list(self):
        registry = ValidatorRegistry()
        registry.register(MetadataA, validator_always_fails)
        metadata = (MetadataA(value="test"),)

        result = registry.validate("test_value", metadata)

        assert isinstance(result, tuple)
        assert not isinstance(result, list)


class TestValidatorRegistryMerge:
    def test_merge_from_adds_validators_from_other_registry(self):
        registry1 = ValidatorRegistry()
        registry2 = ValidatorRegistry()
        registry2.register(MetadataA, validator_always_passes)
        registry2.register(MetadataB, validator_always_fails)

        registry1.merge_from(registry2)

        assert registry1.has_validator(MetadataA)
        assert registry1.has_validator(MetadataB)
        assert registry1.get_validator(MetadataA) is validator_always_passes
        assert registry1.get_validator(MetadataB) is validator_always_fails

    def test_merge_from_preserves_existing_validators_child_wins(self):
        registry1 = ValidatorRegistry()
        registry1.register(MetadataA, validator_always_fails)
        registry2 = ValidatorRegistry()
        registry2.register(MetadataA, validator_always_passes)

        registry1.merge_from(registry2)

        assert registry1.get_validator(MetadataA) is validator_always_fails

    def test_merge_from_empty_registry_has_no_effect(self):
        registry1 = ValidatorRegistry()
        registry1.register(MetadataA, validator_always_passes)
        registry2 = ValidatorRegistry()

        registry1.merge_from(registry2)

        assert registry1.has_validator(MetadataA)
        assert registry1.get_validator(MetadataA) is validator_always_passes
        assert not registry1.has_validator(MetadataB)

    def test_merge_from_into_empty_registry_copies_all_validators(self):
        registry1 = ValidatorRegistry()
        registry2 = ValidatorRegistry()
        registry2.register(MetadataA, validator_always_passes)
        registry2.register(MetadataB, validator_always_fails)

        registry1.merge_from(registry2)

        assert registry1.has_validator(MetadataA)
        assert registry1.has_validator(MetadataB)
        assert registry1.get_validator(MetadataA) is validator_always_passes
        assert registry1.get_validator(MetadataB) is validator_always_fails

    def test_merge_from_partial_overlap_merges_correctly(self):
        registry1 = ValidatorRegistry()
        registry1.register(MetadataA, validator_always_fails)
        registry1.register(MetadataB, validator_conditional)
        registry2 = ValidatorRegistry()
        registry2.register(MetadataA, validator_always_passes)
        registry2.register(MetadataC, validator_multiple_errors)

        registry1.merge_from(registry2)

        assert registry1.get_validator(MetadataA) is validator_always_fails
        assert registry1.get_validator(MetadataB) is validator_conditional
        assert registry1.get_validator(MetadataC) is validator_multiple_errors

    def test_merge_from_does_not_modify_source_registry(self):
        registry1 = ValidatorRegistry()
        registry1.register(MetadataA, validator_always_fails)
        registry2 = ValidatorRegistry()
        registry2.register(MetadataB, validator_always_passes)

        registry1.merge_from(registry2)

        assert not registry2.has_validator(MetadataA)
        assert registry2.has_validator(MetadataB)
        assert registry2.get_validator(MetadataB) is validator_always_passes
