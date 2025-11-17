# pyright: reportPrivateUsage=false, reportDeprecated=false, reportAny=false
from __future__ import annotations

from typing import Annotated, TypedDict, Unpack

import pytest
from annotated_types import Gt
from typing_inspection.introspection import (
    UNKNOWN,
    AnnotationSource,
    InspectedAnnotation,
)

from aclaf import (
    Context,
    ParameterKind,
)
from aclaf._parameters import (
    CommandParameter,
    extract_function_parameters,
    extract_typeddict_parameters,
)
from aclaf.console import Console  # noqa: TC001
from aclaf.logging import Logger  # noqa: TC001
from aclaf.metadata import Flag, Opt


class TestUnknownTypeHandling:
    def test_get_type_unknown_annotation_raises_type_error(self):
        ann = InspectedAnnotation(
            UNKNOWN,
            set(),
            [],
        )
        with pytest.raises(TypeError, match="must be type-annotated"):
            _ = CommandParameter._get_type("test_param", ann)  # noqa: SLF001


class TestTypedDictExtraction:
    def test_extract_typeddict_parameters_basic(self):
        class MyTypedDict(TypedDict):
            name: Annotated[str, Opt(), "--name"]
            count: Annotated[int, Opt(), "--count"]
            enabled: Annotated[bool, Flag(), "--enabled"]

        params = extract_typeddict_parameters(MyTypedDict)
        assert len(params) == 3
        assert "name" in params
        assert "count" in params
        assert "enabled" in params
        assert params["name"].kind == ParameterKind.OPTION
        assert params["name"].value_type is str
        assert params["count"].kind == ParameterKind.OPTION
        assert params["count"].value_type is int
        assert params["enabled"].kind == ParameterKind.OPTION
        assert params["enabled"].is_flag is True

    def test_extract_typeddict_with_annotated_fields(self):
        class AnnotatedTypedDict(TypedDict):
            value: Annotated[int, Gt(0), Opt(), "--value"]
            label: Annotated[str, Opt(), "--label"]

        params = extract_typeddict_parameters(AnnotatedTypedDict)
        assert len(params) == 2
        assert "value" in params
        assert "label" in params
        value_param = params["value"]
        assert any(isinstance(m, Gt) for m in value_param.metadata)
        assert value_param.kind == ParameterKind.OPTION

    def test_typeddict_required_fields(self):
        class RequiredTypedDict(TypedDict):
            name: Annotated[str, Opt(), "--name"]

        params = extract_typeddict_parameters(RequiredTypedDict)
        assert "name" in params
        assert params["name"].is_required is True

    def test_nested_typeddict_not_flattened(self):
        class MyTypedDict(TypedDict):
            name: Annotated[str, Opt(), "--name"]
            count: Annotated[int, Opt(), "--count"]
            enabled: Annotated[bool, Flag(), "--enabled"]

        params = extract_typeddict_parameters(MyTypedDict)
        assert len(params) == 3


class TestSpecialParameterExtraction:
    def test_extract_function_parameters_with_context(self):
        def my_command(_ctx: Context, _value: Annotated[int, Opt(), "--value"]) -> None:
            pass

        params, special = extract_function_parameters(my_command)
        assert "context" in special
        assert special["context"] == "_ctx"
        assert "_ctx" not in params
        assert "_value" in params

    def test_extract_function_parameters_with_console(self):
        def my_command(
            _console: Console, _value: Annotated[int, Opt(), "--value"]
        ) -> None:
            pass

        params, special = extract_function_parameters(my_command)
        assert "console" in special
        assert special["console"] == "_console"
        assert "_console" not in params
        assert "_value" in params

    def test_extract_function_parameters_with_logger(self):
        def my_command(
            _logger: Logger, _value: Annotated[int, Opt(), "--value"]
        ) -> None:
            pass

        params, special = extract_function_parameters(my_command)
        assert "logger" in special
        assert special["logger"] == "_logger"
        assert "_logger" not in params
        assert "_value" in params

    def test_extract_function_parameters_multiple_special_params(self):
        def my_command(
            _ctx: Context,
            _console: Console,
            _logger: Logger,
            _value: Annotated[int, Opt(), "--value"],
        ) -> None:
            pass

        params, special = extract_function_parameters(my_command)
        assert len(special) == 3
        assert special.get("context") == "_ctx"
        assert special.get("console") == "_console"
        assert special.get("logger") == "_logger"
        assert "_value" in params
        assert "_ctx" not in params
        assert "_console" not in params
        assert "_logger" not in params

    def test_extract_function_parameters_no_special_params(self):
        def my_command(_value: Annotated[int, Opt(), "--value"]) -> None:
            pass

        params, special = extract_function_parameters(my_command)
        assert len(special) == 0
        assert "_value" in params

    def test_extract_function_parameters_filters_special_params(self):
        def simple_func(_value: Annotated[int, Opt()]) -> None:
            pass

        params, special = extract_function_parameters(simple_func)
        assert len(special) == 0
        assert "_value" in params

    def test_extract_function_with_all_parameter_kinds(self):
        def complex_func(
            _positional_only: Annotated[int, Opt()],
            /,
            _positional_or_keyword: Annotated[str, Opt()],
            *_args: Annotated[int, Opt()],
            _keyword_only: Annotated[bool, Flag()],
        ) -> None:
            pass

        params, _special = extract_function_parameters(complex_func)
        assert len(params) == 4


class OptionsTypedDict(TypedDict):
    verbose: Annotated[bool, Flag(), "--verbose"]
    output: Annotated[str, Opt(), "--output"]


class TestTypedDictUnpack:
    def test_extract_function_with_var_keyword_unpack(self):
        def my_command(
            _name: Annotated[str, Opt(), "--name"], **_options: Unpack[OptionsTypedDict]
        ) -> None:
            pass

        params, _special = extract_function_parameters(my_command)
        assert "_name" in params
        assert "verbose" in params
        assert "output" in params
        verbose_param = params["verbose"]
        assert isinstance(verbose_param, CommandParameter)
        assert verbose_param.is_flag is True
        output_param = params["output"]
        assert isinstance(output_param, CommandParameter)
        assert output_param.value_type is str
        assert "_options" not in params


class TestComplexUnions:
    def test_complex_union_with_multiple_annotated_types(self):
        type1 = Annotated[int, Gt(0)]
        type2 = Annotated[str, Gt(5)]
        type3 = Annotated[float, Gt(0.0)]
        annotation = Annotated[type1 | type2 | type3, Opt()]  # type: ignore[misc]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        assert len([m for m in param.metadata if isinstance(m, Gt)]) == 3

    def test_annotation_with_none_type(self):
        annotation = Annotated[int | None, Opt()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION

    def test_annotation_with_pipe_union(self):
        annotation = Annotated[int | str, Opt()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION


class TestPathologicalCases:
    def test_pathological_nesting_depth(self):
        annotation = int
        for i in range(10):
            annotation = Annotated[annotation, Gt(i)]
        annotation = Annotated[annotation, Opt()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        assert param.value_type is int
        gt_constraints = [m for m in param.metadata if isinstance(m, Gt)]
        assert len(gt_constraints) == 10


class TestParameterOrdering:
    def test_extract_function_parameters_preserves_parameter_order(self):
        def my_command(
            _first: Annotated[int, Opt()],
            _second: Annotated[str, Opt()],
            _third: Annotated[bool, Opt()],
        ) -> None:
            pass

        params, _ = extract_function_parameters(my_command)
        param_names = list(params.keys())
        assert param_names == ["_first", "_second", "_third"]
