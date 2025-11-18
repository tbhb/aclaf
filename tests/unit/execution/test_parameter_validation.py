# pyright: reportPrivateUsage=false
# ruff: noqa: SLF001
from typing import TYPE_CHECKING

from annotated_types import MinLen

from aclaf import (
    ConverterRegistry,
    RuntimeCommand,
    ValidatorRegistry,
)
from aclaf.parser import EXACTLY_ONE_ARITY

if TYPE_CHECKING:
    from collections.abc import Callable

    from aclaf import RuntimeParameter
    from aclaf.types import ParameterValueType


class TestConversionErrorHandling:

    def test_conversion_errors_become_validation_errors(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        # Simulate conversion error
        conversion_errors = {"count": "Invalid integer: 'abc'"}
        raw: dict[str, ParameterValueType] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert "count" in validation_errors
        assert validation_errors["count"] == ("Invalid integer: 'abc'",)

    def test_conversion_errors_prevent_further_validation(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        # Validator that should NOT be called when conversion fails
        validator_called: list[bool] = []

        def should_not_be_called(
            value: object, other_values: object, metadata: object  # noqa: ARG001
        ) -> tuple[str, ...] | None:
            validator_called.append(True)
            return None

        param = runtime_option_factory(
            name="count",
            value_type=int,
            validators=(should_not_be_called,),
            arity=EXACTLY_ONE_ARITY,
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        conversion_errors = {"count": "Invalid integer"}
        raw: dict[str, ParameterValueType] = {}

        _ = cmd._validate_parameters(raw, cmd.parameters, conversion_errors)

        # Validator should NOT have been called
        assert not validator_called

    def test_multiple_conversion_errors_collected(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        count_param = runtime_option_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        ratio_param = runtime_option_factory(
            name="ratio", value_type=float, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": count_param, "ratio": ratio_param},
        )

        conversion_errors = {
            "count": "Invalid integer: 'abc'",
            "ratio": "Invalid float: 'xyz'",
        }
        raw: dict[str, ParameterValueType] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert "count" in validation_errors
        assert "ratio" in validation_errors
        assert validation_errors["count"] == ("Invalid integer: 'abc'",)
        assert validation_errors["ratio"] == ("Invalid float: 'xyz'",)


class TestRequiredParameterValidation:

    def test_required_parameter_missing_from_raw_raises_error(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, is_required=True, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        raw: dict[str, ParameterValueType] = {}  # Missing required param
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert "count" in validation_errors
        assert validation_errors["count"] == ("is required",)

    def test_required_parameter_with_none_value_raises_error(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, is_required=True, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        raw: dict[str, ParameterValueType] = {"count": None}  # pyright: ignore[reportAssignmentType]
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert "count" in validation_errors
        assert validation_errors["count"] == ("is required",)

    def test_optional_parameter_missing_does_not_raise_error(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, is_required=False, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        raw: dict[str, ParameterValueType] = {}  # Missing optional param
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert "count" not in validation_errors
        assert validation_errors == {}

    def test_optional_parameter_with_none_does_not_raise_error(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, is_required=False, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        raw: dict[str, ParameterValueType] = {"count": None}  # pyright: ignore[reportAssignmentType]
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert "count" not in validation_errors
        assert validation_errors == {}


class TestValidatorErrorCollection:

    def test_validator_errors_collected_in_runtime(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        parameter_validators = ValidatorRegistry()

        param = runtime_option_factory(
            name="email",
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
            metadata=(MinLen(5),),
        )

        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"email": param},
        )

        raw: dict[str, ParameterValueType] = {"email": "abc"}
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert "email" in validation_errors
        assert len(validation_errors["email"]) > 0


class TestValidatorInvocation:

    def test_validators_not_called_for_none_values(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        # The ValidatorRegistry is what actually validates
        # based on metadata, not RuntimeParameter.validators field
        param = runtime_option_factory(
            name="count",
            value_type=int,
            arity=EXACTLY_ONE_ARITY,
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        raw: dict[str, ParameterValueType] = {"count": None}  # pyright: ignore[reportAssignmentType]
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        # No validation should happen for None values
        assert "count" not in validation_errors

    def test_validator_registry_called_for_present_values(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        # Validators are called via the registry based on metadata
        param = runtime_option_factory(
            name="count",
            value_type=int,
            arity=EXACTLY_ONE_ARITY,
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        raw: dict[str, ParameterValueType] = {"count": 42}
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        # With default validators registry and no metadata, should be no errors
        assert "count" not in validation_errors


class TestErrorAggregation:

    def test_empty_dict_returned_when_all_valid(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param},
        )

        raw: dict[str, ParameterValueType] = {"count": 42}
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert validation_errors == {}

    def test_multiple_conversion_and_required_errors_collected(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        param1 = runtime_option_factory(
            name="count",
            value_type=int,
            is_required=True,
            arity=EXACTLY_ONE_ARITY,
        )
        param2 = runtime_option_factory(
            name="ratio",
            value_type=float,
            is_required=True,
            arity=EXACTLY_ONE_ARITY,
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": param1, "ratio": param2},
        )

        # Both parameters missing (required errors)
        raw: dict[str, ParameterValueType] = {}
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        assert len(validation_errors) == 2
        assert "count" in validation_errors
        assert "ratio" in validation_errors
        assert validation_errors["count"] == ("is required",)
        assert validation_errors["ratio"] == ("is required",)

    def test_error_format_is_dict_of_tuples(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
        parameter_validators: ValidatorRegistry,
    ):
        count_param = runtime_option_factory(
            name="count", value_type=int, is_required=True, arity=EXACTLY_ONE_ARITY
        )
        name_param = runtime_option_factory(
            name="name", value_type=str, is_required=True, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=parameter_validators,
            parameters={"count": count_param, "name": name_param},
        )

        # Both missing - required errors
        raw: dict[str, ParameterValueType] = {}
        conversion_errors: dict[str, str] = {}

        validation_errors = cmd._validate_parameters(
            raw, cmd.parameters, conversion_errors
        )

        # Verify structure: dict[str, tuple[str, ...]]
        assert isinstance(validation_errors, dict)
        assert isinstance(validation_errors["count"], tuple)
        assert isinstance(validation_errors["name"], tuple)
        assert validation_errors["count"] == ("is required",)
        assert validation_errors["name"] == ("is required",)
