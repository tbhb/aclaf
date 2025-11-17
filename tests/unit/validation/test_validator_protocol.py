# pyright: reportAny=false, reportExplicitAny=false

from typing import TYPE_CHECKING

from annotated_types import BaseMetadata, Ge, GroupedMetadata, Gt

from aclaf._validation import (
    ParameterValidatorFunctionType,
    ParameterValidatorRegistry,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from aclaf.types import ParameterValueType


def simple_validator(
    value: "ParameterValueType | None",
    _other_parameters: "Mapping[str, ParameterValueType | None]",
    _metadata: "BaseMetadata | GroupedMetadata",
) -> tuple[str, ...] | None:
    if value is None:
        return ("value cannot be None",)
    return None


def always_valid_validator(
    _value: "ParameterValueType | None",
    _other_parameters: "Mapping[str, ParameterValueType | None]",
    _metadata: "BaseMetadata | GroupedMetadata",
) -> tuple[str, ...] | None:
    return None


def always_invalid_validator(
    _value: "ParameterValueType | None",
    _other_parameters: "Mapping[str, ParameterValueType | None]",
    _metadata: "BaseMetadata | GroupedMetadata",
) -> tuple[str, ...] | None:
    return ("always fails",)


class CustomMetadata(BaseMetadata):
    """Custom metadata for protocol testing."""


class TestValidatorProtocol:
    def test_validator_function_signature_is_correct(self):
        validator: ParameterValidatorFunctionType = simple_validator
        result = validator(42, {}, Gt(0))
        assert result is None

    def test_validator_receives_value_parameter(self):
        received_value: list[ParameterValueType | None] = []

        def capturing_validator(
            value: "ParameterValueType | None",
            _other_parameters: "Mapping[str, ParameterValueType | None]",
            _metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            received_value.append(value)
            return None

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, capturing_validator)

        _ = registry.validate(42, {}, (CustomMetadata(),))
        assert len(received_value) == 1
        assert received_value[0] == 42

    def test_validator_receives_other_parameters(self):
        received_params: list[Mapping[str, ParameterValueType | None]] = []

        def capturing_validator(
            _value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            _metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            received_params.append(other_parameters)
            return None

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, capturing_validator)

        other_params = {"param1": 10, "param2": "test"}
        _ = registry.validate(42, other_params, (CustomMetadata(),))

        assert len(received_params) == 1
        assert received_params[0] == other_params

    def test_validator_receives_metadata_parameter(self):
        received_metadata: list[BaseMetadata | GroupedMetadata] = []

        def capturing_validator(
            _value: "ParameterValueType | None",
            _other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            received_metadata.append(metadata)
            return None

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, capturing_validator)

        meta = CustomMetadata()
        _ = registry.validate(42, {}, (meta,))

        assert len(received_metadata) == 1
        assert received_metadata[0] is meta

    def test_validator_returning_none_indicates_success(self):
        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, always_valid_validator)

        result = registry.validate(42, {}, (CustomMetadata(),))
        assert result is None

    def test_validator_returning_error_tuple_indicates_failure(self):
        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, always_invalid_validator)

        result = registry.validate(42, {}, (CustomMetadata(),))
        assert result is not None
        assert len(result) == 1
        assert "always fails" in result[0]

    def test_validator_can_return_single_error(self):
        def single_error_validator(
            _value: "ParameterValueType | None",
            _other_parameters: "Mapping[str, ParameterValueType | None]",
            _metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            return ("single error",)

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, single_error_validator)

        result = registry.validate(42, {}, (CustomMetadata(),))
        assert result is not None
        assert len(result) == 1
        assert result[0] == "single error"

    def test_validator_can_return_multiple_errors(self):
        def multi_error_validator(
            _value: "ParameterValueType | None",
            _other_parameters: "Mapping[str, ParameterValueType | None]",
            _metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            return ("error 1", "error 2", "error 3")

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, multi_error_validator)

        result = registry.validate(42, {}, (CustomMetadata(),))
        assert result is not None
        assert len(result) == 3
        assert "error 1" in result
        assert "error 2" in result
        assert "error 3" in result

    def test_validator_can_access_metadata_attributes(self):
        class ValueBoundMetadata(BaseMetadata):
            bound: int

            def __init__(self, bound: int) -> None:
                self.bound = bound

        def bound_validator(
            value: "ParameterValueType | None",
            _other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            if not isinstance(metadata, ValueBoundMetadata):
                return ("wrong metadata type",)
            if not isinstance(value, int):
                return ("value must be int",)
            if value > metadata.bound:
                return (f"value exceeds bound {metadata.bound}",)
            return None

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(ValueBoundMetadata, bound_validator)

        result = registry.validate(50, {}, (ValueBoundMetadata(100),))
        assert result is None

        result = registry.validate(150, {}, (ValueBoundMetadata(100),))
        assert result is not None
        assert len(result) == 1
        assert "value exceeds bound 100" in result[0]

    def test_validator_can_perform_cross_parameter_validation(self):
        class DependentMetadata(BaseMetadata):
            depends_on: str

            def __init__(self, depends_on: str) -> None:
                self.depends_on = depends_on

        def dependent_validator(
            value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            if not isinstance(metadata, DependentMetadata):
                return ("wrong metadata type",)
            dependency = other_parameters.get(metadata.depends_on)
            if dependency is None:
                return (f"dependency '{metadata.depends_on}' is required",)
            if not isinstance(value, int) or not isinstance(dependency, int):
                return ("both values must be int",)
            if value <= dependency:
                return (f"value must be greater than {metadata.depends_on}",)
            return None

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(DependentMetadata, dependent_validator)

        other_params = {"min_value": 10}
        result = registry.validate(20, other_params, (DependentMetadata("min_value"),))
        assert result is None

        result = registry.validate(5, other_params, (DependentMetadata("min_value"),))
        assert result is not None
        assert len(result) == 1
        assert "must be greater than min_value" in result[0]

    def test_multiple_validators_called_in_metadata_order(self):
        call_order: list[str] = []

        class FirstMetadata(BaseMetadata):
            pass

        class SecondMetadata(BaseMetadata):
            pass

        def first_validator(
            _value: "ParameterValueType | None",
            _other_parameters: "Mapping[str, ParameterValueType | None]",
            _metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            call_order.append("first")
            return None

        def second_validator(
            _value: "ParameterValueType | None",
            _other_parameters: "Mapping[str, ParameterValueType | None]",
            _metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            call_order.append("second")
            return None

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(FirstMetadata, first_validator)
        registry.register(SecondMetadata, second_validator)

        _ = registry.validate(42, {}, (FirstMetadata(), SecondMetadata()))
        assert call_order == ["first", "second"]

    def test_validator_with_none_value_can_succeed(self):
        def none_accepting_validator(
            value: "ParameterValueType | None",
            _other_parameters: "Mapping[str, ParameterValueType | None]",
            _metadata: "BaseMetadata | GroupedMetadata",
        ) -> tuple[str, ...] | None:
            if value is None:
                return None
            return ("value must be None",)

        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, none_accepting_validator)

        result = registry.validate(None, {}, (CustomMetadata(),))
        assert result is None

    def test_validator_with_none_value_can_fail(self):
        registry = ParameterValidatorRegistry()
        registry._validators.clear()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        registry.register(CustomMetadata, simple_validator)

        result = registry.validate(None, {}, (CustomMetadata(),))
        assert result is not None
        assert len(result) == 1
        assert "value cannot be None" in result[0]

    def test_built_in_validators_satisfy_protocol(self):
        from annotated_types import Le, Lt, MaxLen, MinLen, MultipleOf  # noqa: PLC0415

        from aclaf._validation import (  # noqa: PLC0415
            validate_ge,
            validate_gt,
            validate_le,
            validate_lt,
            validate_max_len,
            validate_min_len,
            validate_multiple_of,
        )

        # Test each validator with appropriate metadata
        test_cases: list[tuple[ParameterValidatorFunctionType, BaseMetadata]] = [
            (validate_gt, Gt(0)),
            (validate_ge, Ge(0)),
            (validate_lt, Lt(100)),
            (validate_le, Le(100)),
            (validate_multiple_of, MultipleOf(2)),
            (validate_min_len, MinLen(1)),
            (validate_max_len, MaxLen(100)),
        ]

        for validator, metadata in test_cases:
            # Each should be callable with the protocol signature
            result = validator(42, {}, metadata)
            # Result should be either None or tuple of strings
            assert result is None or isinstance(result, tuple)
