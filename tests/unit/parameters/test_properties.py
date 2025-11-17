# pyright: reportAny=false, reportExplicitAny=false

from pathlib import Path
from typing import Annotated, Any

import pytest
from annotated_types import BaseMetadata, Ge, Gt, Le, Lt, MaxLen, MinLen
from hypothesis import given, strategies as st
from typing_inspection.introspection import AnnotationSource

from aclaf import CommandParameter
from aclaf.metadata import (
    Arg,
    AtLeastOne,
    AtMostOne,
    Collect,
    Count,
    Default,
    ErrorOnDuplicate,
    ExactlyOne,
    FirstWins,
    Flag,
    LastWins,
    MetadataType,
    Opt,
    ZeroOrMore,
)
from aclaf.parser import AccumulationMode


def build_annotated(base_type: Any, *metadata: MetadataType) -> Any:
    if not metadata:
        return base_type
    args = (base_type, *metadata)
    return Annotated[args]  # type: ignore[misc]


@st.composite
def simple_types(draw: st.DrawFn) -> type:
    return draw(st.sampled_from([int, str, float, bool, Path]))


@st.composite
def validation_metadata_items(draw: st.DrawFn) -> MetadataType:
    return draw(
        st.one_of(
            st.builds(Gt, st.integers(min_value=-100, max_value=100)),
            st.builds(Ge, st.integers(min_value=-100, max_value=100)),
            st.builds(Lt, st.integers(min_value=-100, max_value=100)),
            st.builds(Le, st.integers(min_value=-100, max_value=100)),
            st.builds(MinLen, st.integers(min_value=0, max_value=100)),
            st.builds(MaxLen, st.integers(min_value=1, max_value=100)),
        )
    )


@st.composite
def arity_metadata_items(draw: st.DrawFn) -> MetadataType:
    return draw(
        st.one_of(
            st.just(ExactlyOne()),
            st.just(AtMostOne()),
            st.just(ZeroOrMore()),
            st.just(AtLeastOne()),
            st.just("1"),
            st.just("?"),
            st.just("*"),
            st.just("+"),
            st.integers(min_value=2, max_value=10),
        )
    )


@st.composite
def accumulation_metadata_items(draw: st.DrawFn) -> MetadataType:
    return draw(
        st.one_of(
            st.just(FirstWins()),
            st.just(LastWins()),
            st.just(ErrorOnDuplicate()),
            st.builds(Collect, st.booleans()),
            st.just(Count()),
        )
    )


@st.composite
def kind_metadata_items(draw: st.DrawFn) -> MetadataType:
    return draw(
        st.one_of(
            st.just(Arg()),
            st.just(Opt()),
            st.builds(
                Flag,
                const=st.none() | st.text(min_size=1, max_size=10),
                falsey=st.none()
                | st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3).map(
                    tuple
                ),
                truthy=st.none()
                | st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3).map(
                    tuple
                ),
                negation=st.none()
                | st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3).map(
                    tuple
                ),
                count=st.booleans(),
            ),
        )
    )


@st.composite
def name_metadata_items(draw: st.DrawFn) -> MetadataType:
    return draw(
        st.one_of(
            # Long names
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-"
                ),
                min_size=3,
                max_size=15,
            )
            .filter(lambda x: x and x[0].isalpha())
            .map(lambda x: f"--{x}"),
            # Short names
            st.text(
                alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
                min_size=1,
                max_size=1,
            ).map(lambda x: f"-{x}"),
        )
    )


@st.composite
def metadata_items(draw: st.DrawFn) -> MetadataType:
    return draw(
        st.one_of(
            validation_metadata_items(),
            arity_metadata_items(),
            accumulation_metadata_items(),
            kind_metadata_items(),
            name_metadata_items(),
        )
    )


@st.composite
def annotated_types(
    draw: st.DrawFn, max_metadata_items: int = 5
) -> tuple[Any, list[MetadataType]]:
    base_type = draw(simple_types())
    metadata_list = draw(
        st.lists(metadata_items(), min_size=1, max_size=max_metadata_items)
    )
    # Build Annotated dynamically (no star unpacking for Python 3.10 compat)
    annotated_type = build_annotated(base_type, *metadata_list)
    return annotated_type, metadata_list


@st.composite
def nested_annotated(
    draw: st.DrawFn, nesting_levels: int = 3
) -> tuple[Any, list[MetadataType]]:
    base_type = draw(simple_types())
    all_metadata: list[MetadataType] = []

    current_type = base_type
    for _ in range(nesting_levels):
        metadata = draw(st.lists(metadata_items(), min_size=1, max_size=3))
        all_metadata.extend(metadata)
        current_type = build_annotated(current_type, *metadata)

    all_metadata.reverse()

    return current_type, all_metadata


@st.composite
def union_with_annotated(
    draw: st.DrawFn,
) -> tuple[Any, list[MetadataType]]:
    base_type = draw(simple_types())
    metadata_list = draw(st.lists(metadata_items(), min_size=1, max_size=3))
    annotated_branch = build_annotated(base_type, *metadata_list)
    union_type = annotated_branch | None
    return union_type, metadata_list


class TestExtractionOrderInvariant:
    @given(nesting_levels=st.integers(min_value=1, max_value=5))
    def test_nested_annotated_preserves_outer_to_inner_order(self, nesting_levels: int):
        base_type = int
        expected_metadata: list[Gt] = []

        current_type = base_type
        for i in range(nesting_levels):
            meta = Gt(i)
            expected_metadata.insert(0, meta)
            current_type = Annotated[current_type, meta]

        current_type = Annotated[current_type, "--test"]

        param = CommandParameter.from_annotation(
            "test", current_type, AnnotationSource.BARE
        )

        extracted_gt = [m for m in param.metadata if isinstance(m, Gt)]
        assert len(extracted_gt) == nesting_levels

        for i, meta in enumerate(extracted_gt):
            assert meta.gt == expected_metadata[i].gt

    @given(nested_data=nested_annotated(nesting_levels=3))
    def test_nested_annotated_order_deterministic(
        self,
        nested_data: tuple[Any, list[MetadataType]],
    ):
        nested_type, _expected_metadata = nested_data

        # Add kind metadata so parameter can be constructed
        nested_type = Annotated[nested_type, "--test"]

        # Extract twice - may fail due to conflicts
        try:
            param1 = CommandParameter.from_annotation(
                "test", nested_type, AnnotationSource.BARE
            )
            param2 = CommandParameter.from_annotation(
                "test", nested_type, AnnotationSource.BARE
            )

            # Order should be identical
            assert param1.metadata == param2.metadata
        except (ValueError, TypeError):
            # Conflicts are acceptable and should be consistent
            with pytest.raises((ValueError, TypeError)):
                _ = CommandParameter.from_annotation(
                    "test", nested_type, AnnotationSource.BARE
                )


# Property 2: Type preservation invariant
class TestTypePreservationInvariant:
    @given(
        base_type=simple_types(),
        metadata_list=st.lists(metadata_items(), max_size=5),
    )
    def test_value_type_matches_base_type(
        self, base_type: type, metadata_list: list[MetadataType]
    ):
        if not metadata_list:
            # Skip empty metadata (would fail parameter construction)
            return

        # Build Annotated dynamically (no star unpacking for Python 3.10)
        annotated_type = build_annotated(base_type, *metadata_list)

        # May fail due to conflicts, which is expected
        try:
            param = CommandParameter.from_annotation(
                "test", annotated_type, AnnotationSource.BARE
            )
            # Type should be preserved
            assert param.value_type == base_type
        except (ValueError, TypeError):
            # Conflicts or invalid combinations are acceptable
            pass

    @given(nested_data=nested_annotated(nesting_levels=4))
    def test_deeply_nested_type_preserved(
        self,
        nested_data: tuple[Any, list[MetadataType]],
    ):
        nested_type, _ = nested_data

        try:
            param = CommandParameter.from_annotation(
                "test", nested_type, AnnotationSource.BARE
            )

            # Extract base type from deeply nested structure
            # All our test cases use simple types at the base
            base_types = {int, str, float, bool, Path}
            assert param.value_type in base_types
        except (ValueError, TypeError):
            # Conflicts are acceptable
            pass


# Property 3: Metadata completeness
class TestMetadataCompleteness:
    @given(nested_data=nested_annotated(nesting_levels=3))
    def test_all_metadata_extracted_from_nested_annotated(
        self,
        nested_data: tuple[Any, list[MetadataType]],
    ):
        nested_type, expected_metadata = nested_data

        try:
            param = CommandParameter.from_annotation(
                "test", nested_type, AnnotationSource.BARE
            )

            # Verify all expected metadata types are present
            expected_types = {type(m) for m in expected_metadata}
            actual_types = {type(m) for m in param.metadata}

            # All expected metadata types should be extracted
            # (accounting for string metadata being converted to attributes)
            expected_basemetadata = {
                t
                for t in expected_types
                if t is not str and issubclass(t, BaseMetadata)
            }
            actual_basemetadata = {
                t for t in actual_types if issubclass(t, BaseMetadata)
            }

            assert expected_basemetadata <= actual_basemetadata, (
                f"Missing metadata types: {expected_basemetadata - actual_basemetadata}"
            )
        except (ValueError, TypeError):
            # Conflicts are expected and acceptable
            pass

    @given(
        inner_metadata=st.lists(validation_metadata_items(), min_size=1, max_size=3),
        outer_metadata=st.lists(name_metadata_items(), min_size=1, max_size=2),
    )
    def test_metadata_from_all_layers_accessible(
        self, inner_metadata: list[MetadataType], outer_metadata: list[MetadataType]
    ):
        base_type = int
        # Build Annotated dynamically (no star unpacking for Python 3.10)
        inner = build_annotated(base_type, *inner_metadata)
        outer = build_annotated(inner, *outer_metadata)

        try:
            param = CommandParameter.from_annotation(
                "test", outer, AnnotationSource.BARE
            )

            # Check inner metadata is present
            for meta in inner_metadata:
                # Validation metadata should be in the list
                assert any(type(m) is type(meta) for m in param.metadata)

            # Check outer metadata is present (string names become attributes)
            for meta in outer_metadata:
                if isinstance(meta, str) and meta.startswith("--"):
                    assert meta[2:] in param.long
                elif isinstance(meta, str) and meta.startswith("-"):
                    assert meta[1:] in param.short
        except (ValueError, TypeError):
            # Conflicts are acceptable
            pass


# Property 4: Conflict detection consistency
class TestConflictDetectionConsistency:
    @given(
        arity1=arity_metadata_items(),
        arity2=arity_metadata_items(),
    )
    def test_multiple_arity_always_raises(
        self, arity1: MetadataType, arity2: MetadataType
    ):
        # Skip if they're the same (not a conflict)
        if arity1 == arity2:
            return

        annotated_type = Annotated[int, arity1, arity2]

        with pytest.raises(ValueError, match="Multiple arity"):
            _ = CommandParameter.from_annotation(
                "test", annotated_type, AnnotationSource.BARE
            )

    @given(
        mode1=accumulation_metadata_items(),
        mode2=accumulation_metadata_items(),
    )
    def test_multiple_accumulation_modes_always_raise(
        self, mode1: MetadataType, mode2: MetadataType
    ):
        # Skip if they're the same (not a conflict)
        if type(mode1) is type(mode2):
            return

        annotated_type = Annotated[int, mode1, mode2, "--test"]

        with pytest.raises(ValueError, match="Multiple accumulation"):
            _ = CommandParameter.from_annotation(
                "test", annotated_type, AnnotationSource.BARE
            )

    @given(base_type=st.sampled_from([str, float, Path]))
    def test_flag_with_non_boolean_type_raises(self, base_type: type):
        annotated_type = Annotated[base_type, Flag()]

        with pytest.raises(ValueError, match="Flag metadata requires bool or int"):
            _ = CommandParameter.from_annotation(
                "test", annotated_type, AnnotationSource.BARE
            )

    @given(base_type=st.sampled_from([str, bool, Path]))
    def test_count_with_non_numeric_type_raises(self, base_type: type):
        annotated_type = Annotated[base_type, Count(), "--test"]

        with pytest.raises(ValueError, match="Count accumulation mode requires"):
            _ = CommandParameter.from_annotation(
                "test", annotated_type, AnnotationSource.BARE
            )


# Property 5: Last-wins semantics
class TestLastWinsSemantics:
    @given(
        gt_values=st.lists(
            st.integers(min_value=0, max_value=100), min_size=2, max_size=5
        )
    )
    def test_metadata_by_type_returns_outermost_instance(self, gt_values: list[int]):
        # Build nested annotation with multiple Gt instances
        base_type = int
        current_type = base_type

        for value in gt_values:
            current_type = Annotated[current_type, Gt(value)]

        try:
            param = CommandParameter.from_annotation(
                "test", current_type, AnnotationSource.BARE
            )

            # metadata_by_type should return the outermost Gt (first in gt_values)
            gt_from_mapping = param.metadata_by_type.get(Gt)
            assert gt_from_mapping is not None
            assert isinstance(gt_from_mapping, Gt)
            assert gt_from_mapping.gt == gt_values[0]
        except (ValueError, TypeError):
            # Conflicts are acceptable
            pass

    @given(
        values=st.lists(
            st.integers(min_value=-100, max_value=100), min_size=2, max_size=4
        )
    )
    def test_last_wins_consistent_across_metadata_types(self, values: list[int]):
        # Create nested with multiple types of metadata
        base_type = int
        current_type = base_type

        for i, value in enumerate(values):
            # Alternate between different comparable metadata types
            if i % 2 == 0:
                current_type = Annotated[current_type, Gt(value)]
            else:
                current_type = Annotated[current_type, Ge(value)]

        try:
            param = CommandParameter.from_annotation(
                "test", current_type, AnnotationSource.BARE
            )

            # First value should win for its type
            if len(values) > 0:
                gt_meta = param.metadata_by_type.get(Gt)
                if gt_meta and isinstance(gt_meta, Gt):
                    assert gt_meta.gt == values[0]

            if len(values) > 1:
                ge_meta = param.metadata_by_type.get(Ge)
                if ge_meta and isinstance(ge_meta, Ge):
                    assert ge_meta.ge == values[1]
        except (ValueError, TypeError):
            # Conflicts are acceptable
            pass


# Property 6: Query interface correctness
class TestQueryInterfaceCorrectness:
    @given(annotated_data=annotated_types(max_metadata_items=5))
    def test_metadata_by_type_keys_match_metadata_types(
        self,
        annotated_data: tuple[Any, list[MetadataType]],
    ):
        annotated_type, _expected_metadata = annotated_data

        try:
            param = CommandParameter.from_annotation(
                "test", annotated_type, AnnotationSource.BARE
            )

            # All keys match metadata types
            for metadata_type in param.metadata_by_type:
                assert any(type(m) is metadata_type for m in param.metadata)
        except (ValueError, TypeError):
            # Conflicts are acceptable
            pass

    @given(nested_data=nested_annotated(nesting_levels=3))
    def test_metadata_by_type_lazy_computation_cached(
        self,
        nested_data: tuple[Any, list[MetadataType]],
    ):
        nested_type, _ = nested_data

        try:
            param = CommandParameter.from_annotation(
                "test", nested_type, AnnotationSource.BARE
            )

            # Access twice
            first_access = param.metadata_by_type
            second_access = param.metadata_by_type

            # Should be the exact same object (identity check)
            assert first_access is second_access
        except (ValueError, TypeError):
            # Conflicts are acceptable
            pass


# Property 7: Idempotency
class TestIdempotency:
    @given(annotated_data=annotated_types(max_metadata_items=5))
    def test_multiple_extractions_yield_same_result(
        self,
        annotated_data: tuple[Any, list[MetadataType]],
    ):
        annotated_type, _ = annotated_data

        try:
            param1 = CommandParameter.from_annotation(
                "test", annotated_type, AnnotationSource.BARE
            )
            param2 = CommandParameter.from_annotation(
                "test", annotated_type, AnnotationSource.BARE
            )

            # Results should be structurally identical
            assert param1.name == param2.name
            assert param1.value_type == param2.value_type
            assert param1.metadata == param2.metadata
            assert param1.kind == param2.kind
            assert param1.long == param2.long
            assert param1.short == param2.short
            assert param1.arity == param2.arity
            assert param1.accumulation_mode == param2.accumulation_mode
            assert param1.is_flag == param2.is_flag
        except (ValueError, TypeError):
            # Conflicts are expected and should be raised consistently
            with pytest.raises((ValueError, TypeError)):
                _ = CommandParameter.from_annotation(
                    "test", annotated_type, AnnotationSource.BARE
                )


# Property 8: Union metadata extraction
class TestUnionMetadataExtraction:
    @given(union_data=union_with_annotated())
    def test_union_metadata_extracted(
        self,
        union_data: tuple[Any, list[MetadataType]],
    ):
        union_type, _expected_metadata = union_data

        try:
            param = CommandParameter.from_annotation(
                "test", union_type, AnnotationSource.BARE
            )

            # Metadata from annotated branch should be present
            # (at least some of it, conflicts may prevent all)
            assert len(param.metadata) > 0
        except (ValueError, TypeError):
            # Conflicts are acceptable
            pass

    @given(
        inner_metadata=st.lists(validation_metadata_items(), min_size=1, max_size=3),
        outer_metadata=st.lists(name_metadata_items(), min_size=1, max_size=2),
    )
    def test_optional_annotated_extracts_both_layers(
        self, inner_metadata: list[MetadataType], outer_metadata: list[MetadataType]
    ):
        base_type = int
        # Build Annotated dynamically (no star unpacking for Python 3.10)
        inner = build_annotated(base_type, *inner_metadata)
        optional = inner | None
        outer = build_annotated(optional, *outer_metadata)

        try:
            param = CommandParameter.from_annotation(
                "test", outer, AnnotationSource.BARE
            )

            # Should have metadata from both inner and outer
            # Check that at least some validation metadata is present
            validation_types = {Gt, Ge, Lt, Le, MinLen, MaxLen}
            has_validation = any(type(m) in validation_types for m in param.metadata)
            assert has_validation or len(inner_metadata) == 0

            # Check that name metadata is present
            for meta in outer_metadata:
                if isinstance(meta, str) and meta.startswith("--"):
                    assert meta[2:] in param.long
                elif isinstance(meta, str) and meta.startswith("-"):
                    assert meta[1:] in param.short
        except (ValueError, TypeError):
            # Conflicts are acceptable
            pass


class TestBoundaryProperties:
    @given(base_type=simple_types())
    def test_single_metadata_item_always_succeeds(self, base_type: type):
        # Use simple name metadata that works with any type
        annotated_type = Annotated[base_type, "--test"]

        # Should never raise for single, compatible metadata
        param = CommandParameter.from_annotation(
            "test", annotated_type, AnnotationSource.BARE
        )

        assert param.value_type == base_type
        assert "--test"[2:] in param.long

    @given(metadata_list=st.lists(validation_metadata_items(), min_size=1, max_size=10))
    def test_validation_metadata_never_conflicts(
        self, metadata_list: list[MetadataType]
    ):
        # Build Annotated dynamically (no star unpacking for Python 3.10)
        annotated_type = build_annotated(int, *metadata_list, "--test")

        # Validation metadata should never conflict
        param = CommandParameter.from_annotation(
            "test", annotated_type, AnnotationSource.BARE
        )

        # All validation metadata should be present
        assert len(param.metadata) >= len(metadata_list)

    @given(
        long_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Lu", "Nd"),
                whitelist_characters="-",
            ),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x and x[0].isalpha())
    )
    def test_arbitrary_length_option_names_accepted(self, long_name: str):
        annotated_type = Annotated[int, f"--{long_name}"]

        param = CommandParameter.from_annotation(
            "test", annotated_type, AnnotationSource.BARE
        )

        assert long_name in param.long

    @given(nesting_levels=st.integers(min_value=1, max_value=10))
    def test_deep_nesting_succeeds(self, nesting_levels: int):
        base_type = int
        current_type = base_type

        for i in range(nesting_levels):
            current_type = Annotated[current_type, Gt(i)]

        # Add kind metadata so parameter can be constructed
        current_type = Annotated[current_type, "--test"]

        # Should handle deep nesting without error
        param = CommandParameter.from_annotation(
            "test", current_type, AnnotationSource.BARE
        )

        # Should extract all metadata
        gt_metadata = [m for m in param.metadata if isinstance(m, Gt)]
        assert len(gt_metadata) == nesting_levels


class TestPropertyRegressions:
    def test_empty_metadata_list_handled(self):
        # This can happen if all metadata is converted to attributes
        annotated_type = Annotated[int, "--test"]

        param = CommandParameter.from_annotation(
            "test", annotated_type, AnnotationSource.BARE
        )

        # Should succeed even though no BaseMetadata instances
        assert param.value_type is int

    def test_mixed_string_and_object_metadata(self):
        annotated_type = Annotated[int, "--long", "-s", Gt(0), Le(100)]

        param = CommandParameter.from_annotation(
            "test", annotated_type, AnnotationSource.BARE
        )

        assert "long" in param.long
        assert "s" in param.short
        assert any(isinstance(m, Gt) for m in param.metadata)
        assert any(isinstance(m, Le) for m in param.metadata)

    def test_default_metadata_with_other_metadata(self):
        annotated_type = Annotated[int, Default(42), "--value", Gt(0)]

        param = CommandParameter.from_annotation(
            "test", annotated_type, AnnotationSource.BARE
        )

        assert param.default == 42
        assert "value" in param.long

    def test_flag_count_sets_accumulation_mode(self):
        annotated_type = Annotated[int, Flag(count=True), "--verbose"]

        param = CommandParameter.from_annotation(
            "test", annotated_type, AnnotationSource.BARE
        )

        assert param.accumulation_mode == AccumulationMode.COUNT

    def test_collect_flatten_attribute_preserved(self):
        annotated_type = Annotated[list[str], Collect(flatten=True), "--items"]

        param = CommandParameter.from_annotation(
            "test", annotated_type, AnnotationSource.BARE
        )

        assert param.flatten_values is True
        assert param.accumulation_mode == AccumulationMode.COLLECT
