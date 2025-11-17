from inspect import Parameter as FunctionParameter
from typing import Annotated

import pytest
from annotated_types import Gt, Le
from typing_inspection.introspection import AnnotationSource

from aclaf._parameters import CommandParameter
from aclaf._runtime import ParameterKind
from aclaf.metadata import Arg, Opt


class TestAnnotationExtraction:
    def test_from_annotation_extracts_name(self):
        annotation = Annotated[int, Opt(), Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.name == "count"

    def test_from_annotation_extracts_type(self):
        annotation = Annotated[int, Opt(), Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.value_type is int

    def test_from_annotation_extracts_metadata(self):
        annotation = Annotated[int, Opt(), Gt(0), Le(100)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert len(param.metadata) >= 2
        gt_found = any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)
        le_found = any(isinstance(m, Le) and m.le == 100 for m in param.metadata)
        assert gt_found
        assert le_found

    def test_from_annotation_with_default_value(self):
        annotation = Annotated[int, Opt(), Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE, default=10
        )
        assert param.default == 10
        assert not param.is_required

    def test_from_annotation_without_default_is_required(self):
        annotation = Annotated[int, Opt(), Gt(0)]
        _ = CommandParameter.from_annotation("count", annotation, AnnotationSource.BARE)

    def test_from_annotation_raises_when_kind_cannot_be_determined(self):
        annotation = int
        with pytest.raises(TypeError, match="Could not determine parameter type"):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )


class TestKindDetermination:
    def test_from_annotation_with_opt_metadata_is_option(self):
        annotation = Annotated[int, Opt(), Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION

    def test_from_annotation_with_arg_metadata_is_positional(self):
        annotation = Annotated[int, Arg(), Gt(0)]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.POSITIONAL


class TestNameExtraction:
    def test_from_annotation_with_long_name_is_option(self):
        annotation = Annotated[int, "--count", Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert "count" in param.long

    def test_from_annotation_with_short_name_is_option(self):
        annotation = Annotated[int, "-c", Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert "c" in param.short

    def test_from_annotation_with_short_name_only(self):
        annotation = Annotated[int, "-c"]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert "c" in param.short

    def test_from_annotation_long_or_short_names_determines_option(self):
        annotation = Annotated[str, "--test"]
        param = CommandParameter.from_annotation(
            "test", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION

    def test_from_annotation_short_name_determines_option(self):
        annotation = Annotated[str, "-t"]
        param = CommandParameter.from_annotation(
            "test", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION


class TestFunctionParameterExtraction:
    def test_from_function_parameter_positional_only(self):
        func_param = FunctionParameter(
            "value", FunctionParameter.POSITIONAL_ONLY, annotation=int
        )
        param = CommandParameter.from_function_parameter(func_param, int)
        assert param.kind == ParameterKind.POSITIONAL

    def test_from_function_parameter_keyword_only(self):
        func_param = FunctionParameter(
            "value", FunctionParameter.KEYWORD_ONLY, annotation=int
        )
        param = CommandParameter.from_function_parameter(func_param, int)
        assert param.kind == ParameterKind.OPTION

    def test_from_function_parameter_positional_or_keyword(self):
        func_param = FunctionParameter(
            "value", FunctionParameter.POSITIONAL_OR_KEYWORD, annotation=int
        )
        param = CommandParameter.from_function_parameter(func_param, int)
        assert param.kind == ParameterKind.POSITIONAL

    def test_from_function_parameter_with_default(self):
        func_param = FunctionParameter(
            "value",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=int,
            default=42,
        )
        param = CommandParameter.from_function_parameter(func_param, int)
        assert param.default == 42

    def test_from_function_parameter_bool_becomes_flag(self):
        func_param = FunctionParameter(
            "verbose", FunctionParameter.KEYWORD_ONLY, annotation=bool
        )
        param = CommandParameter.from_function_parameter(func_param, bool)
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag

    def test_from_function_parameter_extracts_annotated_metadata(self):
        annotation = Annotated[int, Gt(0), "--count"]
        func_param = FunctionParameter(
            "count", FunctionParameter.KEYWORD_ONLY, annotation=annotation
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.kind == ParameterKind.OPTION
        assert "count" in param.long
        gt_found = any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)
        assert gt_found

    def test_from_function_parameter_with_only_long_name(self):
        annotation = Annotated[str, "-o"]
        func_param = FunctionParameter(
            "output",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.kind == ParameterKind.OPTION
        assert "o" in param.short

    def test_from_function_parameter_long_or_short_names(self):
        func_param = FunctionParameter(
            "test",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=Annotated[str, "--test"],
        )
        param = CommandParameter.from_function_parameter(
            func_param, Annotated[str, "--test"]
        )
        assert param.kind == ParameterKind.OPTION
