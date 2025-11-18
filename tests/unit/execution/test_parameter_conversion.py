# pyright: reportPrivateUsage=false
# ruff: noqa: SLF001
from typing import TYPE_CHECKING

from aclaf import (
    ConverterRegistry,
    RuntimeCommand,
    ValidatorRegistry,
)
from aclaf.exceptions import ConversionError
from aclaf.parser import EXACTLY_ONE_ARITY, ParsedOption, ParsedPositional, ParseResult

if TYPE_CHECKING:
    from collections.abc import Callable

    from aclaf import RuntimeParameter


class TestBasicConversion:

    def test_convert_string_to_int(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        parse_result = ParseResult(
            command="test",
            options={"count": ParsedOption(name="count", value="42")},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["count"] == 42
        assert errors == {}

    def test_convert_string_to_float(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="ratio", value_type=float, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"ratio": param},
        )

        parse_result = ParseResult(
            command="test",
            options={"ratio": ParsedOption(name="ratio", value="3.14")},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["ratio"] == 3.14
        assert errors == {}

    def test_convert_string_to_bool(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="verbose", value_type=bool, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"verbose": param},
        )

        parse_result = ParseResult(
            command="test",
            options={"verbose": ParsedOption(name="verbose", value="true")},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["verbose"] is True
        assert errors == {}

    def test_convert_tuple_to_list(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="files", value_type=list[str], arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"files": param},
        )

        parse_result = ParseResult(
            command="test",
            options={"files": ParsedOption(name="files", value=("a.txt", "b.txt"))},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["files"] == ["a.txt", "b.txt"]
        assert errors == {}


class TestCustomConverter:

    def test_convert_with_custom_converter_function(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        called_with: list[tuple[str, object]] = []

        def custom_converter(value: str, metadata: object) -> int:
            called_with.append((value, metadata))
            return int(value) * 2

        param = runtime_option_factory(
            name="count", value_type=int, converter=custom_converter
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        parse_result = ParseResult(
            command="test",
            options={"count": ParsedOption(name="count", value="21")},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["count"] == 42  # 21 * 2
        assert errors == {}
        assert len(called_with) == 1
        assert called_with[0][0] == "21"


class TestDefaultValues:

    def test_static_default_applied_when_parameter_missing(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, default=10, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        parse_result = ParseResult(command="test", options={}, positionals={})

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["count"] == 10
        assert errors == {}

    def test_default_factory_invoked_when_parameter_missing(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        call_count: list[int] = []

        def factory() -> list[int]:
            call_count.append(1)
            return [1, 2, 3]

        # Need to provide a default value for the condition to trigger
        param = runtime_option_factory(
            name="items", value_type=list[int], default=[], default_factory=factory
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"items": param},
        )

        parse_result = ParseResult(command="test", options={}, positionals={})

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["items"] == [1, 2, 3]
        assert errors == {}
        assert len(call_count) == 1  # Factory called exactly once

    def test_default_not_applied_when_parameter_present(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, default=10, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        parse_result = ParseResult(
            command="test",
            options={"count": ParsedOption(name="count", value="42")},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["count"] == 42  # Not 10
        assert errors == {}

    def test_default_factory_takes_precedence_over_static_default(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="items",
            value_type=list[int],
            default=[],
            default_factory=lambda: [99],
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"items": param},
        )

        parse_result = ParseResult(command="test", options={}, positionals={})

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["items"] == [99]  # Factory result, not []
        assert errors == {}


class TestConversionErrors:

    def test_conversion_error_captured_in_errors_dict(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        parse_result = ParseResult(
            command="test",
            options={"count": ParsedOption(name="count", value="not_a_number")},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert "count" not in converted
        assert "count" in errors
        assert "not_a_number" in errors["count"]

    def test_multiple_conversion_errors_collected(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
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
            parameter_validators=ValidatorRegistry(),
            parameters={"count": count_param, "ratio": ratio_param},
        )

        parse_result = ParseResult(
            command="test",
            options={
                "count": ParsedOption(name="count", value="bad"),
                "ratio": ParsedOption(name="ratio", value="also_bad"),
            },
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert "count" not in converted
        assert "ratio" not in converted
        assert "count" in errors
        assert "ratio" in errors

    def test_conversion_error_does_not_prevent_other_conversions(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        count_param = runtime_option_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        name_param = runtime_option_factory(
            name="name", value_type=str, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": count_param, "name": name_param},
        )

        parse_result = ParseResult(
            command="test",
            options={
                "count": ParsedOption(name="count", value="bad"),
                "name": ParsedOption(name="name", value="Alice"),
            },
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        # Name should still be converted despite count error
        assert converted["name"] == "Alice"
        assert "count" in errors

    def test_custom_converter_error_message_preserved(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        def failing_converter(value: str, metadata: object) -> int:  # noqa: ARG001
            raise ConversionError(value, int, "Custom error message")

        param = runtime_option_factory(
            name="count", value_type=int, converter=failing_converter
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        parse_result = ParseResult(
            command="test",
            options={"count": ParsedOption(name="count", value="42")},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert "count" not in converted
        assert "Custom error message" in errors["count"]


class TestPositionalConversion:

    def test_convert_positional_parameter(
        self,
        runtime_positional_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_positional_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        parse_result = ParseResult(
            command="test",
            options={},
            positionals={"count": ParsedPositional(name="count", value="100")},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["count"] == 100
        assert errors == {}

    def test_convert_mixed_options_and_positionals(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        runtime_positional_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        opt_param = runtime_option_factory(
            name="verbose", value_type=bool, arity=EXACTLY_ONE_ARITY
        )
        pos_param = runtime_positional_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"verbose": opt_param, "count": pos_param},
        )

        parse_result = ParseResult(
            command="test",
            options={"verbose": ParsedOption(name="verbose", value="true")},
            positionals={"count": ParsedPositional(name="count", value="42")},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["verbose"] is True
        assert converted["count"] == 42
        assert errors == {}


class TestEdgeCases:

    def test_empty_string_converted(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="optional", value_type=str, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"optional": param},
        )

        # Empty string is a valid value (not None)
        parse_result = ParseResult(
            command="test",
            options={"optional": ParsedOption(name="optional", value="")},
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["optional"] == ""
        assert errors == {}

    def test_empty_parse_result(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        parse_result = ParseResult(command="test", options={}, positionals={})

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted == {}
        assert errors == {}

    def test_parameter_not_in_spec_ignored(
        self,
        runtime_option_factory: "Callable[..., RuntimeParameter]",
        converters: ConverterRegistry,
    ):
        param = runtime_option_factory(
            name="count", value_type=int, arity=EXACTLY_ONE_ARITY
        )
        cmd = RuntimeCommand(
            name="test",
            run_func=lambda: None,
            converters=converters,
            parameter_validators=ValidatorRegistry(),
            parameters={"count": param},
        )

        # Parse result has "other" but parameter spec only has "count"
        parse_result = ParseResult(
            command="test",
            options={
                "count": ParsedOption(name="count", value="42"),
                "other": ParsedOption(name="other", value="ignored"),
            },
            positionals={},
        )

        converted, errors = cmd._convert_parameters(parse_result, cmd.parameters)

        assert converted["count"] == 42
        assert "other" not in converted
        assert errors == {}
