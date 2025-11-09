"""Property-based tests for value flattening feature.

Uses Hypothesis to verify invariants of the value flattening implementation:
- Length preservation: total value count matches before/after flattening
- Order preservation: flattening maintains value order
- Idempotency: single occurrence behaves identically with/without flattening
- No nested tuples: flattened results contain no nested tuple structures
- Applicability: non-applicable options are unaffected
"""

import warnings

from hypothesis import given, strategies as st

from aclaf.parser import CommandSpec, OptionSpec, Parser
from aclaf.parser.types import AccumulationMode, Arity

# Strategy for generating valid value counts (1-10 values per occurrence)
value_counts = st.integers(min_value=1, max_value=10)

# Strategy for generating occurrence counts (1-20 occurrences)
occurrence_counts = st.integers(min_value=1, max_value=20)

# Strategy for generating string values
values = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        min_codepoint=ord("A"),
        max_codepoint=ord("z"),
    ),
    min_size=1,
    max_size=10,
)


class TestLengthPreservation:
    """Verify that flattening preserves total value count."""

    @given(
        occurrences=st.lists(
            st.lists(values, min_size=1, max_size=10),
            min_size=2,
            max_size=20,
        )
    )
    def test_flatten_preserves_total_value_count(
        self, occurrences: list[list[str]]
    ) -> None:
        """Total count of values must match before and after flattening."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="items",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,
            ),
        )
        parser = Parser(spec=spec)

        # Build argument list: --items v1 v2 --items v3 ...
        args: list[str] = []
        total_count = 0
        for occurrence in occurrences:
            args.append("--items")
            args.extend(occurrence)
            total_count += len(occurrence)

        result = parser.parse(args)

        # Verify total count matches
        assert isinstance(result.options["items"].value, tuple)
        assert len(result.options["items"].value) == total_count

    @given(
        occurrences=st.lists(
            st.lists(values, min_size=0, max_size=10),  # Allow 0 values
            min_size=2,
            max_size=20,
        )
    )
    def test_flatten_with_zero_values_preserves_nonzero_count(
        self, occurrences: list[list[str]]
    ) -> None:
        """Empty occurrences are filtered, preserving only actual values."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="items",
                arity=Arity(0, None),  # Allows 0 values
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,
            ),
        )
        parser = Parser(spec=spec)

        # Build argument list: --items v1 v2 --items --items v3 ...
        args: list[str] = []
        total_count = 0
        for occurrence in occurrences:
            args.append("--items")
            if occurrence:  # Only add values if non-empty
                args.extend(occurrence)
            total_count += len(occurrence)

        result = parser.parse(args)

        # Verify count matches non-empty values
        assert isinstance(result.options["items"].value, tuple)
        assert len(result.options["items"].value) == total_count


class TestOrderPreservation:
    """Verify that flattening preserves value order."""

    @given(
        occurrences=st.lists(
            st.lists(values, min_size=1, max_size=10),
            min_size=2,
            max_size=20,
        )
    )
    def test_flatten_preserves_order(self, occurrences: list[list[str]]) -> None:
        """Flattening must preserve the original order of values."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="items",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,
            ),
        )
        parser = Parser(spec=spec)

        # Build argument list and expected flat order
        args: list[str] = []
        expected_order: list[str] = []
        for occurrence in occurrences:
            args.append("--items")
            args.extend(occurrence)
            expected_order.extend(occurrence)

        result = parser.parse(args)

        # Verify order matches
        assert result.options["items"].value == tuple(expected_order)

    @given(
        occurrences=st.lists(
            st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=5),
            min_size=2,
            max_size=10,
        )
    )
    def test_flatten_maintains_sequence_with_numbers(
        self, occurrences: list[list[int]]
    ) -> None:
        """Order preservation works with numeric string values."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="nums",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,
            ),
        )
        parser = Parser(spec=spec)

        # Convert to strings for command-line args
        args: list[str] = []
        expected_order: list[str] = []
        for occurrence in occurrences:
            args.append("--nums")
            str_values = [str(n) for n in occurrence]
            args.extend(str_values)
            expected_order.extend(str_values)

        result = parser.parse(args)

        assert result.options["nums"].value == tuple(expected_order)


class TestIdempotency:
    """Verify single occurrence behaves identically with/without flattening."""

    @given(values=st.lists(values, min_size=1, max_size=20))
    def test_single_occurrence_same_with_or_without_flatten(
        self, values: list[str]
    ) -> None:
        """Single occurrence with flatten=True unwraps the outer tuple."""
        # With flattening
        spec_flat = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="items",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,
            ),
        )
        parser_flat = Parser(spec=spec_flat)
        result_flat = parser_flat.parse(["--items", *values])

        # Without flattening
        spec_nested = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="items",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=False,
            ),
        )
        parser_nested = Parser(spec=spec_nested)
        result_nested = parser_nested.parse(["--items", *values])

        # With flatten=True: the wrapper tuple is flattened
        assert result_flat.options["items"].value == tuple(values)
        # Without flatten: the wrapper tuple remains
        assert result_nested.options["items"].value == (tuple(values),)


class TestNoNestedTuples:
    """Verify flattened results contain no nested tuple structures."""

    @given(
        occurrences=st.lists(
            st.lists(values, min_size=1, max_size=10),
            min_size=2,
            max_size=20,
        )
    )
    def test_flattened_result_contains_no_tuples(
        self, occurrences: list[list[str]]
    ) -> None:
        """All elements in flattened result should be strings, never tuples."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="items",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,
            ),
        )
        parser = Parser(spec=spec)

        # Build argument list
        args: list[str] = []
        for occurrence in occurrences:
            args.append("--items")
            args.extend(occurrence)

        result = parser.parse(args)

        # Verify no element is a tuple
        assert isinstance(result.options["items"].value, tuple)
        for element in result.options["items"].value:
            assert not isinstance(element, tuple)
            assert isinstance(element, str)

    @given(
        occurrences=st.lists(
            st.lists(values, min_size=1, max_size=5),
            min_size=2,
            max_size=10,
        )
    )
    def test_nested_result_contains_only_tuples_of_strings(
        self, occurrences: list[list[str]]
    ) -> None:
        """Without flattening, result is tuple of tuples of strings."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="items",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=False,
            ),
        )
        parser = Parser(spec=spec)

        # Build argument list
        args: list[str] = []
        for occurrence in occurrences:
            args.append("--items")
            args.extend(occurrence)

        result = parser.parse(args)

        # Verify structure is tuple[tuple[str, ...], ...]
        assert isinstance(result.options["items"].value, tuple)
        for element in result.options["items"].value:
            assert isinstance(element, tuple)
            for item in element:
                assert isinstance(item, str)


class TestApplicability:
    """Verify flattening only applies to appropriate options."""

    @given(
        occurrences=st.lists(
            st.lists(values, min_size=1, max_size=5),
            min_size=2,
            max_size=10,
        )
    )
    def test_non_collect_modes_never_flatten(
        self, occurrences: list[list[str]]
    ) -> None:
        """Non-COLLECT modes should never produce flattened results."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            # Test LAST_WINS
            spec_last = CommandSpec(
                name="cmd",
                options=OptionSpec(
                    name="items",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.LAST_WINS,
                    flatten_values=True,  # Triggers warning but has no effect
                ),
            )
            parser_last = Parser(spec=spec_last)

            args: list[str] = []
            for occurrence in occurrences:
                args.append("--items")
                args.extend(occurrence)

            result = parser_last.parse(args)

            # LAST_WINS returns only last occurrence (as tuple, not nested)
            assert result.options["items"].value == tuple(occurrences[-1])

    @given(
        occurrences=st.lists(
            st.lists(values, min_size=1, max_size=5),
            min_size=2,
            max_size=10,
        )
    )
    def test_single_value_arity_produces_flat_tuple_in_collect(
        self, occurrences: list[list[str]]
    ) -> None:
        """Single-value arity with COLLECT naturally produces flat tuple."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="item",
                arity=Arity(1, 1),  # Single value per occurrence
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,  # Shouldn't matter
            ),
        )
        parser = Parser(spec=spec)

        # Each occurrence has exactly one value
        args: list[str] = []
        expected: list[str] = []
        for occurrence in occurrences:
            args.extend(["--item", occurrence[0]])
            expected.append(occurrence[0])

        result = parser.parse(args)

        # Result is naturally flat (no nesting with max=1)
        assert result.options["item"].value == tuple(expected)

    @given(flag_count=st.integers(min_value=1, max_value=20))
    def test_flags_with_collect_not_affected(self, flag_count: int) -> None:
        """Flag options with COLLECT produce tuple of bools."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="verbose",
                arity=Arity(0, 0),
                accumulation_mode=AccumulationMode.COLLECT,
                is_flag=True,
                flatten_values=True,  # Should have no effect
            ),
        )
        parser = Parser(spec=spec)

        args = ["--verbose"] * flag_count
        result = parser.parse(args)

        # Result is tuple of bools
        value = result.options["verbose"].value
        assert value == (True,) * flag_count
        assert isinstance(value, tuple)
        assert all(isinstance(v, bool) for v in value)


class TestPrecedenceProperties:
    """Verify configuration precedence works correctly."""

    @given(
        occurrences=st.lists(
            st.lists(values, min_size=1, max_size=5),
            min_size=2,
            max_size=10,
        )
    )
    def test_option_level_always_wins(self, occurrences: list[list[str]]) -> None:
        """OptionSpec setting always takes precedence."""
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    name="flat",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,  # Explicit True
                ),
                OptionSpec(
                    name="nested",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=False,  # Explicit False
                ),
            ],
            flatten_option_values=None,  # Different command-level setting
        )
        parser = Parser(
            spec=spec,
            flatten_option_values=False,  # Different parser-level setting
        )

        args: list[str] = []
        for occurrence in occurrences:
            args.extend(["--flat", *occurrence])
            args.extend(["--nested", *occurrence])

        result = parser.parse(args)

        # Verify option-level settings were respected
        flat_value = result.options["flat"].value
        nested_value = result.options["nested"].value

        # flat should be flattened
        assert isinstance(flat_value, tuple)
        assert all(isinstance(v, str) for v in flat_value)

        # nested should be nested
        assert isinstance(nested_value, tuple)
        assert all(isinstance(v, tuple) for v in nested_value)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_occurrence_list(self) -> None:
        """Option never specified produces empty result."""
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="items",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,
            ),
        )
        parser = Parser(spec=spec)

        result = parser.parse([])

        # Option not present
        assert "items" not in result.options

    @given(
        value_count=st.integers(min_value=2, max_value=20),
    )
    def test_fixed_arity_enforces_count_per_occurrence(self, value_count: int) -> None:
        """Fixed multi-value arity (e.g., exactly 2 or 3) works with flattening."""
        # Use arity (2, 2) - exactly 2 values per occurrence
        spec = CommandSpec(
            name="cmd",
            options=OptionSpec(
                name="pairs",
                arity=Arity(2, 2),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,
            ),
        )
        parser = Parser(spec=spec)

        # Generate pairs: --pairs a1 b1 --pairs a2 b2 ...
        occurrence_count = value_count // 2
        args: list[str] = []
        expected: list[str] = []
        for i in range(occurrence_count):
            args.extend(["--pairs", f"a{i}", f"b{i}"])
            expected.extend([f"a{i}", f"b{i}"])

        result = parser.parse(args)

        value = result.options["pairs"].value
        assert value == tuple(expected)
        assert isinstance(value, tuple)
        assert len(value) == occurrence_count * 2
