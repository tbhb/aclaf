# pyright: reportPrivateUsage=false
from typing import Annotated

import pytest
from annotated_types import Gt
from typing_inspection.introspection import AnnotationSource

from aclaf._parameters import CommandParameter
from aclaf._runtime import ParameterKind
from aclaf.metadata import Arg, Collect, ExactlyOne, Flag, Opt, ZeroOrMore
from aclaf.parser import AccumulationMode


class TestOptionConversion:
    def test_to_runtime_parameter_creates_option(self):
        annotation = Annotated[int, Opt(), Gt(0)]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.name == "count"
        assert runtime_param.kind == ParameterKind.OPTION
        assert runtime_param.value_type is int

    def test_to_runtime_option_with_long_and_short_names(self):
        annotation = Annotated[str, "--output", "-o", Opt()]
        param = CommandParameter.from_annotation(
            "output", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert "output" in runtime_param.long
        assert "o" in runtime_param.short

    def test_to_runtime_option_raises_when_kind_not_option(self):
        annotation = Annotated[str, Arg()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        # Manually change kind to test error
        param.kind = ParameterKind.POSITIONAL
        with pytest.raises(TypeError, match="Can only convert option"):
            _ = param._to_runtime_option()  # noqa: SLF001

    def test_to_runtime_option_raises_when_name_is_none(self):
        param = CommandParameter(kind=ParameterKind.OPTION, name=None, value_type=int)
        with pytest.raises(ValueError, match="Parameter name must be set"):
            _ = param._to_runtime_option()  # noqa: SLF001

    def test_to_runtime_option_raises_when_value_type_is_none(self):
        param = CommandParameter(
            kind=ParameterKind.OPTION, name="test", value_type=None
        )
        with pytest.raises(ValueError, match="Parameter type must be set"):
            _ = param._to_runtime_option()  # noqa: SLF001


class TestPositionalConversion:
    def test_to_runtime_parameter_creates_positional(self):
        annotation = Annotated[str, "--value"]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        param.kind = ParameterKind.POSITIONAL  # Force positional
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.kind == ParameterKind.POSITIONAL

    def test_to_runtime_positional_with_default(self):
        annotation = Annotated[str, "--value"]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE, default="default_val"
        )
        param.kind = ParameterKind.POSITIONAL
        runtime_param = param.to_runtime_parameter()
        # Positional with default has min=0
        assert runtime_param.arity.min == 0
        assert runtime_param.arity.max == 1

    def test_to_runtime_positional_without_default(self):
        annotation = Annotated[str, "--value"]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        param.kind = ParameterKind.POSITIONAL
        runtime_param = param.to_runtime_parameter()
        # Positional without default has min=1
        assert runtime_param.arity.min == 1
        assert runtime_param.arity.max == 1

    def test_to_runtime_positional_with_explicit_arity(self):
        annotation = Annotated[list[str], ExactlyOne(), "--values"]
        param = CommandParameter.from_annotation(
            "values", annotation, AnnotationSource.BARE
        )
        param.kind = ParameterKind.POSITIONAL
        runtime_param = param.to_runtime_parameter()
        # Explicit arity should be used
        assert runtime_param.arity.min == 1
        assert runtime_param.arity.max == 1

    def test_to_runtime_positional_raises_when_kind_not_positional(self):
        annotation = Annotated[int, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        with pytest.raises(TypeError, match="Can only convert positional"):
            _ = param._to_runtime_positional()  # noqa: SLF001

    def test_to_runtime_positional_raises_when_name_is_none(self):
        param = CommandParameter(
            kind=ParameterKind.POSITIONAL, name=None, value_type=int
        )
        with pytest.raises(ValueError, match="Parameter name must be set"):
            _ = param._to_runtime_positional()  # noqa: SLF001

    def test_to_runtime_positional_raises_when_value_type_is_none(self):
        param = CommandParameter(
            kind=ParameterKind.POSITIONAL, name="test", value_type=None
        )
        with pytest.raises(ValueError, match="Parameter type must be set"):
            _ = param._to_runtime_positional()  # noqa: SLF001


class TestFlagHandling:
    def test_to_runtime_option_with_flag(self):
        annotation = Annotated[bool, Flag()]
        param = CommandParameter.from_annotation(
            "verbose", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.is_flag
        assert runtime_param.arity.min == 0
        assert runtime_param.arity.max == 0

    def test_to_runtime_option_with_flag_values(self):
        annotation = Annotated[
            bool,
            Flag(
                falsey=("no", "false"),
                truthy=("yes", "true"),
                negation=("disable", "no"),
            ),
        ]
        param = CommandParameter.from_annotation(
            "enabled", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.falsey_flag_values == ("no", "false")
        assert runtime_param.truthy_flag_values == ("yes", "true")
        assert runtime_param.negation_words == ("disable", "no")


class TestArityDefaults:
    def test_to_runtime_option_default_arity_exactly_one(self):
        annotation = Annotated[int, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.arity.min == 1
        assert runtime_param.arity.max == 1

    def test_to_runtime_option_with_arity(self):
        annotation = Annotated[list[str], ZeroOrMore(), Opt()]
        param = CommandParameter.from_annotation(
            "items", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.arity.min == 0
        assert runtime_param.arity.max is None


class TestAccumulationDefaults:
    def test_to_runtime_option_default_accumulation_mode_last_wins(self):
        annotation = Annotated[int, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.accumulation_mode == AccumulationMode.LAST_WINS

    def test_to_runtime_option_with_accumulation_mode(self):
        annotation = Annotated[list[str], Collect(), Opt()]
        param = CommandParameter.from_annotation(
            "items", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.accumulation_mode == AccumulationMode.COLLECT

    def test_to_runtime_option_with_flatten_values(self):
        annotation = Annotated[list[str], Collect(flatten=True), Opt()]
        param = CommandParameter.from_annotation(
            "items", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.flatten_values is True


class TestMetadataFiltering:
    def test_to_runtime_option_filters_basemetadata(self):
        annotation = Annotated[int, Gt(0), "not_base_metadata", Opt()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        # String metadata should be filtered out, only BaseMetadata remains
        assert all(hasattr(m, "__class__") for m in runtime_param.metadata)
        # Gt should be in metadata
        assert any(isinstance(m, Gt) for m in runtime_param.metadata)


class TestErrorCases:
    def test_to_runtime_parameter_raises_when_kind_is_none(self):
        param = CommandParameter(name="test", value_type=int, kind=None)
        with pytest.raises(TypeError, match="Parameter kind must be"):
            _ = param.to_runtime_parameter()


class TestAttributePreservation:
    def test_to_runtime_parameter_preserves_metadata(self):
        annotation = Annotated[int, Gt(0), Opt()]
        param = CommandParameter.from_annotation(
            "value", annotation, AnnotationSource.BARE
        )
        runtime_param = param.to_runtime_parameter()
        # Metadata should be preserved as tuple
        assert isinstance(runtime_param.metadata, tuple)
        assert any(isinstance(m, Gt) for m in runtime_param.metadata)

    def test_to_runtime_parameter_includes_help(self):
        annotation = Annotated[int, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        param.help = "The count value"
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.help == "The count value"

    def test_to_runtime_parameter_includes_default(self):
        annotation = Annotated[int, Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE, default=42
        )
        runtime_param = param.to_runtime_parameter()
        assert runtime_param.default == 42
