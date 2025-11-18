from inspect import Parameter as FunctionParameter
from typing import Annotated, Literal

import pytest
from annotated_types import Gt, Le

from aclaf.metadata import Arg, Default, Flag, Opt
from aclaf.registration import CommandParameter
from aclaf.types import ParameterKind


class TestBasicParameterKinds:
    def test_from_function_parameter_var_positional_becomes_positional(self):
        func_param = FunctionParameter(
            "args", FunctionParameter.VAR_POSITIONAL, annotation=int
        )
        param = CommandParameter.from_function_parameter(func_param, int)
        assert param.kind == ParameterKind.POSITIONAL

    def test_from_function_parameter_positional_only_becomes_positional(self):
        func_param = FunctionParameter(
            "value", FunctionParameter.POSITIONAL_ONLY, annotation=int
        )
        param = CommandParameter.from_function_parameter(func_param, int)
        assert param.kind == ParameterKind.POSITIONAL

    def test_from_function_parameter_empty_parameter_defaults_to_positional(self):
        func_param = FunctionParameter(
            "value",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=str,
        )
        param = CommandParameter.from_function_parameter(func_param, str)
        assert param.kind == ParameterKind.POSITIONAL


class TestDefaultHandling:
    def test_from_function_parameter_with_default_none(self):
        func_param = FunctionParameter(
            "value",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=int,
            default=None,
        )
        param = CommandParameter.from_function_parameter(func_param, int)
        assert param.default is None

    def test_from_function_parameter_with_default_empty_list(self):
        default_value: list[str] = []
        func_param = FunctionParameter(
            "items",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=list[str],
            default=default_value,
        )
        param = CommandParameter.from_function_parameter(func_param, list[str])
        assert param.default == []

    def test_from_function_parameter_with_default_false(self):
        func_param = FunctionParameter(
            "flag",
            FunctionParameter.KEYWORD_ONLY,
            annotation=bool,
            default=False,
        )
        param = CommandParameter.from_function_parameter(func_param, bool)
        assert param.default is False
        assert param.is_flag

    def test_from_function_parameter_with_literal_default(self):
        annotation = Literal["debug", "info", "warning", "error"]
        func_param = FunctionParameter(
            "level",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=annotation,
            default="info",
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.default == "info"

    def test_metadata_default_overridden_by_function_default(
        self,
    ):
        annotation = Annotated[int, Default(10), Opt()]
        func_param = FunctionParameter(
            "count",
            FunctionParameter.KEYWORD_ONLY,
            annotation=annotation,
            default=20,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.default == 20


class TestBoolHandling:
    def test_from_function_parameter_bool_with_default_true(self):
        func_param = FunctionParameter(
            "enabled",
            FunctionParameter.KEYWORD_ONLY,
            annotation=bool,
            default=True,
        )
        param = CommandParameter.from_function_parameter(func_param, bool)
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag
        assert param.default is True

    def test_from_function_parameter_bool_with_flag_metadata(self):
        annotation = Annotated[bool, Flag()]
        func_param = FunctionParameter(
            "verbose",
            FunctionParameter.KEYWORD_ONLY,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.is_flag
        assert param.kind == ParameterKind.OPTION

    def test_from_function_parameter_plain_bool_without_default_becomes_option(self):
        func_param = FunctionParameter(
            "verbose",
            FunctionParameter.KEYWORD_ONLY,
            annotation=bool,
        )
        param = CommandParameter.from_function_parameter(func_param, bool)
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag

    def test_from_function_parameter_bool_without_names_becomes_option(self):
        func_param = FunctionParameter(
            "debug",
            FunctionParameter.KEYWORD_ONLY,
            annotation=bool,
        )
        param = CommandParameter.from_function_parameter(func_param, bool)
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag

    def test_from_function_parameter_bool_without_metadata_and_names(self):
        func_param = FunctionParameter(
            "verbose",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=bool,
        )
        param = CommandParameter.from_function_parameter(func_param, bool)
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag

    def test_from_function_parameter_bool_type_without_default(self):
        func_param = FunctionParameter(
            "test",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=bool,
        )
        param = CommandParameter.from_function_parameter(func_param, bool)
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag is True
        assert param.value_type is bool

    def test_bool_from_function_parameter_with_only_long_name(self):
        annotation = Annotated[bool, "--debug"]
        func_param = FunctionParameter(
            "debug",
            FunctionParameter.KEYWORD_ONLY,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.kind == ParameterKind.OPTION
        assert "debug" in param.long


class TestMetadataExtraction:
    def test_from_function_parameter_with_nested_annotated(self):
        inner = Annotated[int, Gt(0)]
        outer = Annotated[inner, Le(100), Opt()]
        func_param = FunctionParameter(
            "value",
            FunctionParameter.KEYWORD_ONLY,
            annotation=outer,
        )
        param = CommandParameter.from_function_parameter(func_param, outer)
        assert param.kind == ParameterKind.OPTION
        gt_found = any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)
        le_found = any(isinstance(m, Le) and m.le == 100 for m in param.metadata)
        assert gt_found
        assert le_found

    def test_from_function_parameter_metadata_preserved_in_order(self):
        annotation = Annotated[int, Gt(0), Le(100), Opt(), "-n"]
        func_param = FunctionParameter(
            "number",
            FunctionParameter.KEYWORD_ONLY,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert len(param.metadata) >= 2
        gt_found = any(isinstance(m, Gt) for m in param.metadata)
        le_found = any(isinstance(m, Le) for m in param.metadata)
        opt_found = any(isinstance(m, Opt) for m in param.metadata)
        assert gt_found
        assert le_found
        assert opt_found

    def test_from_function_parameter_var_positional_with_metadata(self):
        annotation = Annotated[str, Gt(0)]
        func_param = FunctionParameter(
            "args",
            FunctionParameter.VAR_POSITIONAL,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.kind == ParameterKind.POSITIONAL
        gt_found = any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)
        assert gt_found


class TestMetadataOverrides:
    def test_from_function_parameter_with_arg_metadata_overrides_keyword_only(self):
        annotation = Annotated[int, Arg()]
        func_param = FunctionParameter(
            "value",
            FunctionParameter.KEYWORD_ONLY,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.kind == ParameterKind.POSITIONAL

    def test_from_function_parameter_with_opt_metadata_overrides_positional_only(self):
        annotation = Annotated[int, Opt()]
        func_param = FunctionParameter(
            "value",
            FunctionParameter.POSITIONAL_ONLY,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.kind == ParameterKind.OPTION

    def test_from_function_parameter_with_long_name_overrides_positional(self):
        annotation = Annotated[str, "--output"]
        func_param = FunctionParameter(
            "output",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.kind == ParameterKind.OPTION
        assert "output" in param.long

    def test_from_function_parameter_with_short_name_overrides_positional(self):
        annotation = Annotated[str, "-o"]
        func_param = FunctionParameter(
            "output",
            FunctionParameter.POSITIONAL_OR_KEYWORD,
            annotation=annotation,
        )
        param = CommandParameter.from_function_parameter(func_param, annotation)
        assert param.kind == ParameterKind.OPTION
        assert "o" in param.short


class TestKindDetermination:
    def test_from_function_parameter_kind_determination_fallthrough(self):
        func_param = FunctionParameter(
            "kwargs",
            FunctionParameter.VAR_KEYWORD,
            annotation=dict,
        )
        with pytest.raises(TypeError, match="Could not determine parameter type"):
            _ = CommandParameter.from_function_parameter(func_param, dict)

    def test_parameter_kind_resolution_edge_cases(self):
        func_param1 = FunctionParameter(
            "value", FunctionParameter.POSITIONAL_ONLY, annotation=Annotated[int, Opt()]
        )
        param1 = CommandParameter.from_function_parameter(
            func_param1, Annotated[int, Opt()]
        )
        assert param1.kind == ParameterKind.OPTION

        func_param2 = FunctionParameter(
            "args", FunctionParameter.VAR_POSITIONAL, annotation=Annotated[int, Opt()]
        )
        param2 = CommandParameter.from_function_parameter(
            func_param2, Annotated[int, Opt()]
        )
        assert param2.kind == ParameterKind.OPTION

    def test_from_function_parameter_all_kinds(self):
        kw_only = FunctionParameter(
            "kw", FunctionParameter.KEYWORD_ONLY, annotation=int
        )
        param_kw = CommandParameter.from_function_parameter(kw_only, int)
        assert param_kw.kind == ParameterKind.OPTION

        pos_or_kw = FunctionParameter(
            "pk", FunctionParameter.POSITIONAL_OR_KEYWORD, annotation=str
        )
        param_pk = CommandParameter.from_function_parameter(pos_or_kw, str)
        assert param_pk.kind == ParameterKind.POSITIONAL
