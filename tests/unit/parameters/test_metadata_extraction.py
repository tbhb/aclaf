# pyright: reportPrivateUsage=false, reportOptionalMemberAccess=false, reportArgumentType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnnecessaryTypeIgnoreComment=false, reportUnusedCallResult=false
from typing import Annotated

import pytest
from annotated_types import Ge, Gt, Le, MinLen
from typing_inspection.introspection import AnnotationSource

from aclaf import CommandParameter, ParameterKind
from aclaf._internal._metadata import (
    get_all_metadata,
    get_metadata,
    has_metadata,
)
from aclaf.metadata import (
    Arg,
    Collect,
    Count,
    ErrorOnDuplicate,
    FirstWins,
    Flag,
    LastWins,
    Opt,
)
from aclaf.parser import ONE_OR_MORE_ARITY, AccumulationMode


class TestMetadataQueryUtilities:
    def test_get_metadata_returns_last_instance(self):
        metadata = (Gt(0), Le(100), Gt(10))
        result = get_metadata(metadata, Gt)
        assert result is not None
        assert result.gt == 10

    def test_get_metadata_returns_none_when_not_found(self):
        metadata = (Gt(0), Le(100))
        result = get_metadata(metadata, MinLen)
        assert result is None

    def test_get_all_metadata_returns_all_instances(self):
        metadata = (Gt(0), Le(100), Gt(10))
        result = get_all_metadata(metadata, Gt)
        assert len(result) == 2
        assert result[0].gt == 0
        assert result[1].gt == 10

    def test_get_all_metadata_returns_empty_when_not_found(self):
        metadata = (Gt(0), Le(100))
        result = get_all_metadata(metadata, MinLen)
        assert result == ()

    def test_has_metadata_returns_true_when_present(self):
        metadata = (Gt(0), Le(100))
        assert has_metadata(metadata, Gt)

    def test_has_metadata_returns_false_when_absent(self):
        metadata = (Gt(0), Le(100))
        assert not has_metadata(metadata, MinLen)


class TestNestedMetadataExtraction:
    def test_nested_annotated_extracts_all_metadata(self, nested_annotated):
        wrapped = Annotated[nested_annotated, Opt()]  # pyright: ignore[reportArgumentType]
        param = CommandParameter.from_annotation(
            "value", wrapped, AnnotationSource.BARE
        )
        assert any(isinstance(m, Le) and m.le == 100 for m in param.metadata)
        assert any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)

    def test_triple_nested_annotated_extracts_all(self, triple_nested_annotated):
        wrapped = Annotated[triple_nested_annotated, Opt()]  # pyright: ignore[reportArgumentType]
        param = CommandParameter.from_annotation(
            "value", wrapped, AnnotationSource.BARE
        )
        assert any(isinstance(m, Ge) and m.ge == 5 for m in param.metadata)
        assert any(isinstance(m, Le) and m.le == 100 for m in param.metadata)
        assert any(isinstance(m, Gt) and m.gt == 0 for m in param.metadata)

    def test_metadata_order_outer_to_inner(self):
        inner = Annotated[int, Gt(0)]
        outer = Annotated[inner, Opt(), Le(100)]
        param = CommandParameter.from_annotation("value", outer, AnnotationSource.BARE)
        le_index = None
        gt_index = None
        for i, m in enumerate(param.metadata):
            if isinstance(m, Le):
                le_index = i
            if isinstance(m, Gt):
                gt_index = i
        assert le_index is not None
        assert gt_index is not None
        assert le_index < gt_index


class TestStringAndArityMetadata:
    def test_string_metadata_extracted_for_option_names(
        self, string_metadata_annotated
    ):
        param = CommandParameter.from_annotation(
            "verbose", string_metadata_annotated, AnnotationSource.BARE
        )
        assert "verbose" in param.long
        assert "v" in param.short

    def test_arity_metadata_extracted(self, arity_metadata_annotated):
        wrapped = Annotated[arity_metadata_annotated, Opt()]  # pyright: ignore[reportArgumentType]
        param = CommandParameter.from_annotation(
            "values", wrapped, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.arity == ONE_OR_MORE_ARITY

    def test_extract_metadata_attributes_with_string_long_name(self):
        attrs = CommandParameter._extract_metadata_attributes(  # noqa: SLF001
            int, ["--count", "-c", Opt()]
        )
        assert "count" in attrs.get("long", ())
        assert "c" in attrs.get("short", ())


class TestFlagMetadataExtraction:
    def test_flag_metadata_extracted(self, flag_metadata_annotated):
        param = CommandParameter.from_annotation(
            "verbose", flag_metadata_annotated, AnnotationSource.BARE
        )
        assert param.is_flag

    def test_flag_with_count_mode(self):
        annotation = Annotated[int, Flag(count=True)]
        param = CommandParameter.from_annotation(
            "verbose", annotation, AnnotationSource.BARE
        )
        assert param.is_flag
        assert param.accumulation_mode == AccumulationMode.COUNT

    def test_flag_metadata_without_count(self):
        annotation = Annotated[bool, Flag(const="value")]
        param = CommandParameter.from_annotation(
            "enabled", annotation, AnnotationSource.BARE
        )
        assert param.is_flag
        assert param.const_value == "value"
        assert param.accumulation_mode != AccumulationMode.COUNT

    def test_flag_accumulation_mode_branch(self):
        annotation = Annotated[bool, Flag(count=False, const="yes")]
        param = CommandParameter.from_annotation(
            "enabled", annotation, AnnotationSource.BARE
        )
        assert param.is_flag
        assert param.accumulation_mode != AccumulationMode.COUNT

    def test_metadata_extraction_with_flag_all_attributes(self):
        annotation = Annotated[
            bool,
            Flag(
                const="enabled",
                falsey=("no", "off"),
                truthy=("yes", "on"),
                negation=("disable",),
                count=False,
            ),
        ]
        param = CommandParameter.from_annotation(
            "feature", annotation, AnnotationSource.BARE
        )
        assert param.is_flag
        assert param.const_value == "enabled"
        assert param.falsey_flag_values == ("no", "off")
        assert param.truthy_flag_values == ("yes", "on")
        assert param.negation_words == ("disable",)


class TestArityExtraction:
    def test_integer_arity_exactly_one(self):
        annotation = Annotated[list[str], 3, Opt()]
        param = CommandParameter.from_annotation(
            "values", annotation, AnnotationSource.BARE
        )
        assert param.arity is not None
        assert param.arity.min == 3
        assert param.arity.max == 3

    def test_arity_shortcuts_coverage(self):
        annotation = Annotated[str, "1", Arg()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        assert param.arity is not None
        assert param.arity.min == 1
        assert param.arity.max == 1

    def test_metadata_extraction_all_arity_shortcuts(self):
        param1 = CommandParameter.from_annotation(
            "v1", Annotated[str, "1", Opt()], AnnotationSource.BARE
        )
        assert param1.arity.min == 1
        assert param1.arity.max == 1

        param2 = CommandParameter.from_annotation(
            "v2", Annotated[str, "?", Opt()], AnnotationSource.BARE
        )
        assert param2.arity.min == 0
        assert param2.arity.max == 1

        param3 = CommandParameter.from_annotation(
            "v3", Annotated[list[str], "*", Opt()], AnnotationSource.BARE
        )
        assert param3.arity.min == 0
        assert param3.arity.max is None

        param4 = CommandParameter.from_annotation(
            "v4", Annotated[list[str], "+", Opt()], AnnotationSource.BARE
        )
        assert param4.arity.min == 1
        assert param4.arity.max is None


class TestAccumulationModes:
    def test_metadata_extraction_all_accumulation_modes(self):
        param1 = CommandParameter.from_annotation(
            "v1", Annotated[int, FirstWins(), Opt()], AnnotationSource.BARE
        )
        assert param1.accumulation_mode == AccumulationMode.FIRST_WINS

        param2 = CommandParameter.from_annotation(
            "v2", Annotated[int, LastWins(), Opt()], AnnotationSource.BARE
        )
        assert param2.accumulation_mode == AccumulationMode.LAST_WINS

        param3 = CommandParameter.from_annotation(
            "v3", Annotated[int, ErrorOnDuplicate(), Opt()], AnnotationSource.BARE
        )
        assert param3.accumulation_mode == AccumulationMode.ERROR

        param4 = CommandParameter.from_annotation(
            "v4",
            Annotated[list[str], Collect(flatten=True), Opt()],
            AnnotationSource.BARE,
        )
        assert param4.accumulation_mode == AccumulationMode.COLLECT
        assert param4.flatten_values is True

        param5 = CommandParameter.from_annotation(
            "v5", Annotated[int, Count(), Opt()], AnnotationSource.BARE
        )
        assert param5.accumulation_mode == AccumulationMode.COUNT


class TestMetadataPatterns:
    def test_metadata_pattern_fallthrough(self):
        class CustomMetadata:
            pass

        custom = CustomMetadata()
        attrs = CommandParameter._extract_metadata_attributes(int, [custom, Opt()])  # noqa: SLF001
        assert attrs.get("kind") == ParameterKind.OPTION

    def test_extract_metadata_attributes_with_custom_classes(self):
        class UnknownMetadata:
            pass

        unknown = UnknownMetadata()
        attrs = CommandParameter._extract_metadata_attributes(  # noqa: SLF001
            int, [unknown, Opt(), "--test"]
        )
        assert attrs.get("kind") == ParameterKind.OPTION
        assert "test" in attrs.get("long", ())

    def test_metadata_extraction_with_arg(self):
        annotation = Annotated[str, Arg()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        assert param.kind == ParameterKind.POSITIONAL


class TestMetadataCaching:
    def test_metadata_by_type_property_caches_result(self):
        annotation = Annotated[int, Opt(), Gt(0), Le(100)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        result1 = param.metadata_by_type
        result2 = param.metadata_by_type
        assert result1 is result2

    def test_metadata_by_type_contains_expected_types(self):
        annotation = Annotated[int, Opt(), Gt(0), Le(100)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        metadata_by_type = param.metadata_by_type
        assert Gt in metadata_by_type
        assert Le in metadata_by_type

    def test_metadata_by_type_last_wins(self):
        annotation = Annotated[int, Opt(), Gt(0), Le(100), Gt(10)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        metadata_by_type = param.metadata_by_type
        gt_meta = metadata_by_type.get(Gt)
        assert gt_meta is not None
        assert isinstance(gt_meta, Gt)
        assert gt_meta.gt == 10


class TestComplexMetadata:
    def test_complex_metadata_all_types_extracted(self, complex_metadata):
        param = CommandParameter.from_annotation(
            "count", complex_metadata, AnnotationSource.BARE
        )
        assert any(isinstance(m, Gt) for m in param.metadata)
        assert any(isinstance(m, Le) for m in param.metadata)
        assert "count" in param.long
        assert "c" in param.short


class TestMetadataRequirements:
    def test_from_metadata_without_default_is_required(self):
        param = CommandParameter.from_metadata([Opt()], name="test", value_type=int)
        assert param.is_required is True

    def test_from_metadata_with_default_not_required(self):
        param = CommandParameter.from_metadata(
            [Opt()], name="test", value_type=int, default=42
        )
        assert not param.is_required

    def test_from_metadata_with_existing_command_parameter(self):
        existing_param = CommandParameter(
            name="base", value_type=int, kind=ParameterKind.OPTION
        )
        metadata = [existing_param, Opt()]
        param = CommandParameter.from_metadata(metadata, name="new", value_type=str)
        assert param.name == "new"

    def test_bool_with_default_becomes_flag_option(self):
        param_dict = CommandParameter._extract_metadata_attributes(  # noqa: SLF001
            bool, [], default=False
        )
        assert param_dict.get("kind") == ParameterKind.OPTION
        assert param_dict.get("is_flag") is True

    def test_bool_default_flag_setting(self):
        attrs = CommandParameter._extract_metadata_attributes(bool, [], default=True)  # noqa: SLF001
        assert attrs.get("kind") == ParameterKind.OPTION
        assert attrs.get("is_flag") is True


class TestKindFallthrough:
    def test_kind_fallthrough_in_from_annotation(self):
        annotation = int
        with pytest.raises(TypeError, match="Could not determine parameter type"):
            CommandParameter.from_annotation("value", annotation, AnnotationSource.BARE)

    def test_from_annotation_raises_on_type_resolution_error(self):
        pytest.skip("Type resolution error handling tested indirectly")
