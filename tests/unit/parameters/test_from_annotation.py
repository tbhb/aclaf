# pyright: reportDeprecated=false
from typing import Annotated, Union

from annotated_types import Ge, Gt, Le, Lt
from typing_inspection.introspection import AnnotationSource

from aclaf._parameters import CommandParameter
from aclaf._runtime import ParameterKind
from aclaf.metadata import Arg, Default, ExactlyOne, Flag, Opt, ZeroOrMore


class TestAnnotationSources:
    def test_from_annotation_bare_source(self):
        annotation = Annotated[int, Opt(), Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.name == "count"
        assert param.value_type is int

    def test_from_annotation_function_source(self):
        annotation = Annotated[str, Arg()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.FUNCTION
        )
        assert param.kind == ParameterKind.POSITIONAL

    def test_from_annotation_typeddict_source(self):
        annotation = Annotated[int, "--count", Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.TYPED_DICT
        )
        assert param.kind == ParameterKind.OPTION

    def test_from_annotation_typeddict_source_with_long_name(self):
        annotation = Annotated[str, "--field"]
        param = CommandParameter.from_annotation(
            "field", annotation, AnnotationSource.TYPED_DICT
        )
        assert param.kind == ParameterKind.OPTION


class TestDefaultHandling:
    def test_from_annotation_with_default_sets_is_required_false(self):
        annotation = Annotated[int, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE, default=10
        )
        assert not param.is_required

    def test_from_annotation_without_default_sets_is_required_true(self):
        annotation = Annotated[int, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.is_required

    def test_from_annotation_with_metadata_default(self):
        annotation = Annotated[int, Default(42), Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.default == 42

    def test_from_annotation_function_default_overrides_metadata_default(self):
        annotation = Annotated[int, Default(10), Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE, default=20
        )
        assert param.default == 20


class TestBoolHandling:
    def test_from_annotation_bool_without_names_becomes_flag(self):
        annotation = bool
        param = CommandParameter.from_annotation(
            "flag", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag is True

    def test_from_annotation_bool_with_default_becomes_flag(self):
        annotation = bool
        param = CommandParameter.from_annotation(
            "flag", annotation, AnnotationSource.BARE, default=False
        )
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag is True
        assert param.default is False

    def test_from_annotation_bool_with_opt_and_default_becomes_flag(self):
        annotation = Annotated[bool, Opt()]
        param = CommandParameter.from_annotation(
            "verbose", annotation, AnnotationSource.BARE, default=False
        )
        assert param.kind == ParameterKind.OPTION

    def test_from_annotation_bool_type_without_names(self):
        annotation = bool
        param = CommandParameter.from_annotation(
            "test", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag is True
        assert param.value_type is bool

    def test_from_annotation_bool_with_opt_metadata(self):
        annotation = Annotated[bool, Opt(), "--flag"]
        param = CommandParameter.from_annotation(
            "test", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag is False

    def test_from_annotation_bool_without_long_short_becomes_flag(self):
        annotation = bool
        param = CommandParameter.from_annotation(
            "flag", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert param.is_flag is True

    def test_bool_from_annotation_without_opt_or_arg_with_long_name(self):
        annotation = Annotated[bool, "--verbose"]
        param = CommandParameter.from_annotation(
            "verbose", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION


class TestUnionMetadataExtraction:
    def test_from_annotation_with_union_metadata_extraction(self):
        inner = Annotated[int, Gt(0)]
        annotation = Annotated[inner | None, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        gt_found = any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)
        assert gt_found

    def test_from_annotation_with_optional_annotated(self):
        annotation = Annotated[Annotated[int, Gt(0)] | None, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        gt_found = any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)
        assert gt_found

    def test_from_annotation_nested_union_with_metadata(self):
        inner1 = Annotated[int, Gt(0)]
        inner2 = Annotated[str, Lt(100)]
        annotation = Annotated[Union[inner1, inner2], Opt()]  # type: ignore[misc]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        gt_found = any(isinstance(m, Gt) for m in param.metadata)
        lt_found = any(isinstance(m, Lt) for m in param.metadata)
        assert gt_found
        assert lt_found

    def test_nested_annotated_with_union_extraction(self):
        inner = Annotated[int, Gt(0)]
        outer = Annotated[inner | None, Opt()]
        param = CommandParameter.from_annotation(
            "value", outer, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        gt_found = any(isinstance(m, Gt) for m in param.metadata)
        assert gt_found

    def test_union_metadata_extraction_complex(self):
        type1 = Annotated[int, Gt(0)]
        type2 = Annotated[float, Lt(100.0)]
        union_type = Union[type1, type2]  # type: ignore[misc]
        outer = Annotated[union_type, Opt()]  # type: ignore[misc]
        param = CommandParameter.from_annotation(
            "value", outer, AnnotationSource.BARE
        )
        gt_found = any(isinstance(m, Gt) for m in param.metadata)
        lt_found = any(isinstance(m, Lt) for m in param.metadata)
        assert gt_found
        assert lt_found


class TestNestedMetadata:
    def test_from_annotation_metadata_order_preserved(self):
        annotation = Annotated[int, Opt(), Gt(0), Le(100)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert len(param.metadata) >= 2

    def test_from_annotation_deeply_nested_metadata(self):
        level1 = Annotated[int, Gt(0)]
        level2 = Annotated[level1, Le(100)]
        level3 = Annotated[level2, Ge(5), Opt()]
        param = CommandParameter.from_annotation(
            "value", level3, AnnotationSource.BARE
        )
        gt_found = any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)
        le_found = any(isinstance(m, Le) and m.le == 100 for m in param.metadata)
        ge_found = any(isinstance(m, Ge) and m.ge == 5 for m in param.metadata)
        assert gt_found
        assert le_found
        assert ge_found


class TestComplexMetadata:
    def test_from_annotation_with_multiple_string_names(self):
        annotation = Annotated[str, "--output", "-o", "--out"]
        param = CommandParameter.from_annotation(
            "output", annotation, AnnotationSource.BARE
        )
        assert "output" in param.long
        assert "out" in param.long
        assert "o" in param.short

    def test_from_annotation_with_arity_metadata(self):
        annotation = Annotated[list[str], ExactlyOne(), Opt()]
        param = CommandParameter.from_annotation(
            "items", annotation, AnnotationSource.BARE
        )
        assert param.arity is not None
        assert param.arity.min == 1
        assert param.arity.max == 1

    def test_from_annotation_with_flag_metadata(self):
        annotation = Annotated[bool, Flag()]
        param = CommandParameter.from_annotation(
            "verbose", annotation, AnnotationSource.BARE
        )
        assert param.is_flag
        assert param.kind == ParameterKind.OPTION

    def test_from_annotation_int_with_opt(self):
        annotation = Annotated[int, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert not param.is_flag

    def test_from_annotation_str_with_arg(self):
        annotation = Annotated[str, Arg()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.POSITIONAL

    def test_from_annotation_with_complex_metadata_combination(self):
        annotation = Annotated[
            list[int], "--values", "-v", ZeroOrMore(), Gt(0), Le(100)
        ]
        param = CommandParameter.from_annotation(
            "values", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert "values" in param.long
        assert "v" in param.short
        assert param.arity is not None
        gt_found = any(isinstance(m, Gt) for m in param.metadata)
        le_found = any(isinstance(m, Le) for m in param.metadata)
        assert gt_found
        assert le_found

    def test_from_annotation_with_multiple_metadata_types(self):
        annotation = Annotated[
            int,
            Gt(0),
            Le(100),
            "--count",
            "-c",
            ExactlyOne(),
            Opt(),
        ]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.OPTION
        assert "count" in param.long
        assert "c" in param.short
        assert param.arity is not None
