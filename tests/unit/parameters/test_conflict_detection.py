from typing import Annotated

import pytest
from annotated_types import Gt
from typing_inspection.introspection import AnnotationSource

from aclaf.metadata import (
    Arg,
    AtLeastOne,
    Collect,
    Count,
    ErrorOnDuplicate,
    ExactlyOne,
    FirstWins,
    Flag,
    LastWins,
    Opt,
    ZeroOrMore,
)
from aclaf.registration import CommandParameter


class TestArityConflicts:
    def test_multiple_arity_specifications_raise_error(self):
        annotation = Annotated[list[str], ExactlyOne(), ZeroOrMore()]
        with pytest.raises(ValueError, match="Multiple arity specifications found"):
            _ = CommandParameter.from_annotation(
                "values", annotation, AnnotationSource.BARE
            )

    def test_multiple_arity_with_string_shortcuts_raise_error(self):
        annotation = Annotated[list[str], "1", "*"]
        with pytest.raises(ValueError, match="Multiple arity specifications found"):
            _ = CommandParameter.from_annotation(
                "values", annotation, AnnotationSource.BARE
            )

    def test_multiple_arity_with_integer_raise_error(self):
        annotation = Annotated[list[str], 2, 3]
        with pytest.raises(ValueError, match="Multiple arity specifications found"):
            _ = CommandParameter.from_annotation(
                "values", annotation, AnnotationSource.BARE
            )

    def test_mixed_arity_types_raise_error(self):
        annotation = Annotated[list[str], AtLeastOne(), 3]
        with pytest.raises(ValueError, match="Multiple arity specifications found"):
            _ = CommandParameter.from_annotation(
                "values", annotation, AnnotationSource.BARE
            )

    def test_single_arity_specification_succeeds(self):
        annotation = Annotated[list[str], Opt(), AtLeastOne()]
        _ = CommandParameter.from_annotation(
            "values", annotation, AnnotationSource.BARE
        )


class TestAccumulationModeConflicts:
    def test_multiple_accumulation_modes_raise_error(self):
        annotation = Annotated[str, FirstWins(), LastWins()]
        with pytest.raises(ValueError, match="Multiple accumulation modes found"):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )

    def test_collect_and_count_conflict(self):
        annotation = Annotated[int, Collect(), Count()]
        with pytest.raises(ValueError, match="Multiple accumulation modes found"):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )

    def test_error_on_duplicate_and_first_wins_conflict(self):
        annotation = Annotated[str, ErrorOnDuplicate(), FirstWins()]
        with pytest.raises(ValueError, match="Multiple accumulation modes found"):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )

    def test_single_accumulation_mode_succeeds(self):
        annotation = Annotated[str, Opt(), LastWins()]
        _ = CommandParameter.from_annotation("value", annotation, AnnotationSource.BARE)


class TestParameterKindConflicts:
    def test_arg_and_opt_are_mutually_exclusive(self):
        annotation = Annotated[int, Arg(), Opt()]
        with pytest.raises(
            ValueError, match="Arg metadata cannot be combined with Opt"
        ):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )

    def test_arg_and_flag_are_mutually_exclusive(self):
        annotation = Annotated[bool, Arg(), Flag()]
        with pytest.raises(ValueError, match="Arg metadata cannot be combined with"):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )


class TestFlagTypeCompatibility:
    def test_flag_with_string_type_raises_error(self):
        annotation = Annotated[str, Flag()]
        with pytest.raises(ValueError, match="Flag metadata requires bool or int"):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )

    def test_flag_with_bool_type_succeeds(self):
        annotation = Annotated[bool, Flag()]
        param = CommandParameter.from_annotation(
            "verbose", annotation, AnnotationSource.BARE
        )
        assert param.is_flag

    def test_flag_with_int_type_succeeds(self):
        annotation = Annotated[int, Flag()]
        param = CommandParameter.from_annotation(
            "verbosity", annotation, AnnotationSource.BARE
        )
        assert param.is_flag

    def test_flag_with_count_raises_error_for_non_numeric(self):
        annotation = Annotated[bool, Flag(count=True)]
        with pytest.raises(
            ValueError, match="Count accumulation mode requires int or float"
        ):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )


class TestCountTypeCompatibility:
    def test_count_with_string_type_raises_error(self):
        annotation = Annotated[str, Opt(), Count()]
        with pytest.raises(
            ValueError, match="Count accumulation mode requires int or float"
        ):
            _ = CommandParameter.from_annotation(
                "value", annotation, AnnotationSource.BARE
            )

    def test_count_with_int_type_succeeds(self):
        annotation = Annotated[int, Opt(), Count()]
        param = CommandParameter.from_annotation(
            "verbosity", annotation, AnnotationSource.BARE
        )
        assert param.accumulation_mode is not None

    def test_count_with_float_type_succeeds(self):
        annotation = Annotated[float, Opt(), Count()]
        param = CommandParameter.from_annotation(
            "score", annotation, AnnotationSource.BARE
        )
        assert param.accumulation_mode is not None


class TestValidMetadataCombinations:
    def test_valid_complex_metadata_no_conflicts(self):
        annotation = Annotated[int, Gt(0), "--count", "-c", Opt()]
        param = CommandParameter.from_annotation(
            "count", annotation, AnnotationSource.BARE
        )
        assert param.kind is not None
        assert len(param.metadata) > 0
