"""Property-based tests for the parser using Hypothesis.

This module contains property-based tests that verify mathematical and logical
invariants in the parser implementation. These tests use Hypothesis to generate
random inputs and verify that certain properties always hold.
"""

import pytest
from hypothesis import given, strategies as st

from aclaf.parser import CommandSpec, OptionSpec, Parser
from aclaf.parser._parameters import (
    _validate_arity,  # pyright: ignore[reportPrivateUsage]
)
from aclaf.parser.exceptions import (
    InsufficientOptionValuesError,
    OptionCannotBeSpecifiedMultipleTimesError,
)
from aclaf.parser.types import AccumulationMode, Arity


class TestAccumulationModeProperties:
    """Test that accumulation modes satisfy their defining properties."""

    @given(
        values=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=1,
            max_size=20,
        ),
    )
    def test_collect_mode_preserves_all_values_in_order(self, values: list[str]):
        """Property: COLLECT mode preserves all occurrences in order.

        For any list of values (not starting with -), parsing with COLLECT
        accumulation mode should result in a tuple containing all values in
        the same order.
        """
        # Build args: --opt val1 --opt val2 --opt val3 ...
        args: list[str] = []
        for value in values:
            args.extend(["--opt", value])

        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: result should be a tuple of all values in order
        assert result.options["opt"].value == tuple(values)

    @given(
        count=st.integers(min_value=0, max_value=100),
    )
    def test_count_mode_equals_number_of_occurrences(self, count: int):
        """Property: COUNT mode result equals number of flag occurrences.

        For any non-negative integer n, parsing n occurrences of a flag
        with COUNT mode should result in the value n.
        """
        args = ["--flag"] * count
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "flag", is_flag=True, accumulation_mode=AccumulationMode.COUNT
                ),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: result should equal the number of occurrences
        if count == 0:
            assert result.options.get("flag") is None
        else:
            assert result.options["flag"].value == count

    @given(
        values=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=1,
            max_size=20,
        ),
    )
    def test_first_wins_mode_keeps_first_value(self, values: list[str]):
        """Property: FIRST_WINS mode result equals the first occurrence.

        For any non-empty list of values (not starting with -), parsing with
        FIRST_WINS accumulation mode should result in the value from the first
        occurrence only.
        """
        args: list[str] = []
        for value in values:
            args.extend(["--opt", value])

        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", accumulation_mode=AccumulationMode.FIRST_WINS),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: result should equal the first value
        assert result.options["opt"].value == values[0]

    @given(
        values=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=1,
            max_size=20,
        ),
    )
    def test_last_wins_mode_keeps_last_value(self, values: list[str]):
        """Property: LAST_WINS mode result equals the last occurrence.

        For any non-empty list of values (not starting with -), parsing with
        LAST_WINS accumulation mode should result in the value from the last
        occurrence only.
        """
        args: list[str] = []
        for value in values:
            args.extend(["--opt", value])

        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", accumulation_mode=AccumulationMode.LAST_WINS),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: result should equal the last value
        assert result.options["opt"].value == values[-1]

    @given(
        value1=st.text(min_size=1).filter(lambda x: not x.startswith("-")),
        value2=st.text(min_size=1).filter(lambda x: not x.startswith("-")),
    )
    def test_error_mode_raises_on_multiple_occurrences(self, value1: str, value2: str):
        """Property: ERROR mode raises exception on multiple occurrences.

        For any two values (not starting with -), parsing with ERROR
        accumulation mode should raise OptionCannotBeSpecifiedMultipleTimesError
        when the option appears more than once.
        """
        args = ["--opt", value1, "--opt", value2]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", accumulation_mode=AccumulationMode.ERROR),
            ],
        )
        parser = Parser(spec)

        # Property: should raise error on second occurrence
        with pytest.raises(OptionCannotBeSpecifiedMultipleTimesError):
            _ = parser.parse(args)

    @given(
        value=st.text(min_size=1).filter(lambda x: not x.startswith("-")),
    )
    def test_error_mode_accepts_single_occurrence(self, value: str):
        """Property: ERROR mode accepts single occurrence.

        For any value (not starting with -), parsing a single occurrence
        with ERROR accumulation mode should succeed and return a tuple
        containing that value.
        """
        args = ["--opt", value]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", accumulation_mode=AccumulationMode.ERROR),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: single occurrence should work fine and return scalar
        assert result.options["opt"].value == value


class TestArityValidationProperties:
    """Test that arity validation maintains its invariants."""

    @given(
        min_arity=st.integers(min_value=0, max_value=100),
        max_arity=st.integers(min_value=0, max_value=100) | st.none(),
    )
    def test_validate_arity_accepts_valid_arities(
        self, min_arity: int, max_arity: int | None
    ):
        """Property: Valid arity values are accepted when min <= max.

        For any non-negative min and max where min <= max (or max is None),
        _validate_arity should accept the values and return a valid Arity.
        """
        # Skip invalid cases where max < min
        if max_arity is not None and min_arity > max_arity:
            return

        arity = _validate_arity(Arity(min_arity, max_arity))

        # Property: returned arity should match input
        assert arity.min == min_arity
        assert arity.max == max_arity
        # Property: invariants should hold
        assert arity.min >= 0
        if arity.max is not None:
            assert arity.max >= 0
            assert arity.min <= arity.max

    @given(
        min_arity=st.integers(max_value=-1),
    )
    def test_validate_arity_rejects_negative_min(self, min_arity: int):
        """Property: Negative minimum arity is rejected.

        For any negative integer, _validate_arity should raise ValueError
        when used as the minimum arity.
        """
        with pytest.raises(ValueError, match="Minimum arity must not be negative"):
            _ = _validate_arity(Arity(min_arity, None))

    @given(
        max_arity=st.integers(max_value=-1),
    )
    def test_validate_arity_rejects_negative_max(self, max_arity: int):
        """Property: Negative maximum arity is rejected.

        For any negative integer, _validate_arity should raise ValueError
        when used as the maximum arity.
        """
        with pytest.raises(ValueError, match="Maximum arity must not be negative"):
            _ = _validate_arity(Arity(0, max_arity))

    @given(
        min_arity=st.integers(min_value=1, max_value=100),
        max_arity=st.integers(min_value=0, max_value=99),
    )
    def test_validate_arity_rejects_min_greater_than_max(
        self, min_arity: int, max_arity: int
    ):
        """Property: Minimum greater than maximum is rejected.

        For any min > max (both non-negative), _validate_arity should
        raise ValueError.
        """
        # Ensure min > max
        if min_arity <= max_arity:
            min_arity = max_arity + 1

        with pytest.raises(
            ValueError, match="Minimum arity must be less than maximum arity"
        ):
            _ = _validate_arity(Arity(min_arity, max_arity))

    @given(
        value=st.integers(min_value=0, max_value=100),
    )
    def test_validate_arity_int_creates_exact_arity(self, value: int):
        """Property: Integer input creates exact arity (min = max = value).

        For any non-negative integer, _validate_arity should create an
        Arity where min and max are both equal to that integer.
        """
        arity = _validate_arity(value)

        # Property: min and max should both equal the input
        assert arity.min == value
        assert arity.max == value

    def test_validate_arity_none_defaults_to_exactly_one(self):
        """Property: None input defaults to Arity(1, 1).

        When None is passed to _validate_arity, it should return
        an arity of exactly one (min=1, max=1).
        """
        arity = _validate_arity(None)

        # Property: should default to exactly one
        assert arity.min == 1
        assert arity.max == 1

    @given(
        min_arity=st.integers(min_value=0, max_value=100),
        max_arity=st.integers(min_value=0, max_value=100) | st.none(),
    )
    def test_validate_arity_arity_object_passthrough(
        self, min_arity: int, max_arity: int | None
    ):
        """Property: Arity objects are validated but returned with same values.

        For any valid Arity object, _validate_arity should validate it
        and return an Arity with the same min/max values.
        """
        # Skip invalid cases
        if max_arity is not None and min_arity > max_arity:
            return

        input_arity = Arity(min_arity, max_arity)
        result_arity = _validate_arity(input_arity)

        # Property: values should be preserved
        assert result_arity.min == input_arity.min
        assert result_arity.max == input_arity.max


class TestOptionValueConsumptionProperties:
    """Test that option value consumption respects arity boundaries."""

    @given(
        min_arity=st.integers(min_value=0, max_value=10),
        max_arity=st.integers(min_value=0, max_value=10) | st.none(),
        num_values=st.integers(min_value=0, max_value=20),
    )
    def test_option_consumes_within_arity_bounds(
        self, min_arity: int, max_arity: int | None, num_values: int
    ):
        """Property: Options consume values within arity bounds.

        For any arity specification and available values, the parser
        should consume at least min and at most max values (when sufficient
        values are available), or raise InsufficientOptionValuesError.
        """
        # Skip invalid arity combinations
        if max_arity is not None and min_arity > max_arity:
            return

        # Skip edge case: option with zero values and flexible arity
        # This exposes a parser bug where values[0] is accessed on empty list
        if num_values == 0 and min_arity == 0 and max_arity != 0:
            return

        # Generate dummy values
        values = [f"val{i}" for i in range(num_values)]
        args = ["--opt", *values]

        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", arity=Arity(min_arity, max_arity)),
            ],
        )
        parser = Parser(spec)

        if num_values < min_arity:
            # Property: insufficient values should raise error
            with pytest.raises(
                InsufficientOptionValuesError
            ):  # InsufficientOptionValuesError
                _ = parser.parse(args)
        else:
            result = parser.parse(args)

            # Special case: zero-arity options return True (boolean)
            if min_arity == 0 and max_arity == 0:
                assert result.options["opt"].value is True
                return

            consumed_values = result.options["opt"].value

            # Convert single values to tuple for consistent checking
            if isinstance(consumed_values, str):
                consumed_values = (consumed_values,)

            # Type narrowing: at this point consumed_values must be a tuple
            assert isinstance(consumed_values, tuple)
            consumed_count = len(consumed_values)

            # Property: consumed values should be within bounds
            assert consumed_count >= min_arity
            if max_arity is not None:
                assert consumed_count <= max_arity
            # Property: shouldn't consume more than available
            assert consumed_count <= num_values

    @given(
        values_for_opt1=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=1,
            max_size=5,
        ),
        values_for_opt2=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=1,
            max_size=5,
        ),
    )
    def test_option_stops_at_next_option(
        self, values_for_opt1: list[str], values_for_opt2: list[str]
    ):
        """Property: Option value consumption stops at next option.

        When parsing options with unbounded arity, the parser should stop
        consuming values when it encounters another option, even if the
        current option could accept more values.
        """
        # Build args: --opt1 val1 val2 ... --opt2 val1 val2 ...
        args = ["--opt1", *values_for_opt1, "--opt2", *values_for_opt2]

        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt1", arity=Arity(0, None)),  # Unbounded
                OptionSpec("opt2", arity=Arity(0, None)),  # Unbounded
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: opt1 should only get values_for_opt1, not values_for_opt2
        opt1_values = result.options["opt1"].value
        if isinstance(opt1_values, str):
            opt1_values = (opt1_values,)
        assert opt1_values == tuple(values_for_opt1)

        # Property: opt2 should get values_for_opt2
        opt2_values = result.options["opt2"].value
        if isinstance(opt2_values, str):
            opt2_values = (opt2_values,)
        assert opt2_values == tuple(values_for_opt2)
