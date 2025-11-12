"""Property-based tests for the parser using Hypothesis.

This module contains property-based tests that verify mathematical and logical
invariants in the parser implementation. These tests use Hypothesis to generate
random inputs and verify that certain properties always hold.
"""

import pytest
from hypothesis import example, given, strategies as st

from aclaf.parser import CommandSpec, OptionSpec, Parser, ParserConfiguration
from aclaf.parser._parameters import (
    _validate_arity,  # pyright: ignore[reportPrivateUsage]
)
from aclaf.parser.exceptions import (
    AmbiguousOptionError,
    FlagWithValueError,
    InsufficientOptionValuesError,
    OptionCannotBeSpecifiedMultipleTimesError,
    UnknownOptionError,
)
from aclaf.parser.types import AccumulationMode, Arity

from .strategies import option_lists, option_value_pairs


class TestAccumulationModeProperties:
    """Test that accumulation modes satisfy their defining properties."""

    @example(values=[""])  # Empty string
    @example(values=["a", "b", "c"])  # Simple case
    @given(
        values=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=1,
            max_size=20,  # Limit to 20 for reasonable test runtime
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
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: result should be a tuple of all values in order
        assert result.options["opt"].value == tuple(values)

    @example(count=0)  # No occurrences
    @example(count=1)  # Single occurrence
    @example(count=100)  # Maximum
    @given(
        count=st.integers(
            min_value=0, max_value=100
        ),  # Limit to 100 to avoid excessive argument lists
    )
    def test_count_mode_equals_number_of_occurrences(self, count: int):
        """Property: COUNT mode result equals number of flag occurrences.

        For any non-negative integer n, parsing n occurrences of a flag
        with COUNT mode should result in the value n.
        """
        args = ["--flag"] * count
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag", is_flag=True, accumulation_mode=AccumulationMode.COUNT
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: result should equal the number of occurrences
        if count == 0:
            assert result.options.get("flag") is None
        else:
            assert result.options["flag"].value == count

    @example(values=["first", "second"])  # Two values
    @example(values=["only"])  # Single value (edge case)
    @given(
        values=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=1,
            max_size=20,  # Limit to 20 for reasonable test runtime
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
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.FIRST_WINS)
            },
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
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.LAST_WINS)
            },
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
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.ERROR)
            },
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
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.ERROR)
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: single occurrence should work fine and return scalar
        assert result.options["opt"].value == value

    @given(
        values=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=2,
            max_size=10,  # Limit to 10 for reasonable test runtime
        ),
    )
    def test_first_wins_equals_head_of_collect(self, values: list[str]):
        """Property: FIRST_WINS result equals first element of COLLECT result.

        For any list of values, parsing with FIRST_WINS should give the
        same result as taking the first element of COLLECT mode's tuple.
        """
        args: list[str] = []
        for value in values:
            args.extend(["--opt", value])

        spec_first = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.FIRST_WINS)
            },
        )
        spec_collect = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)
            },
        )

        result_first = Parser(spec_first).parse(args)
        result_collect = Parser(spec_collect).parse(args)

        # Property: FIRST_WINS == COLLECT[0]
        first_value = result_first.options["opt"].value
        collect_value = result_collect.options["opt"].value
        assert isinstance(collect_value, tuple)
        assert first_value == collect_value[0]

    @given(
        values=st.lists(
            st.text(min_size=1).filter(lambda x: not x.startswith("-")),
            min_size=2,
            max_size=10,
        ),
    )
    def test_last_wins_equals_tail_of_collect(self, values: list[str]):
        """Property: LAST_WINS result equals last element of COLLECT result.

        For any list of values, parsing with LAST_WINS should give the
        same result as taking the last element of COLLECT mode's tuple.
        """
        args: list[str] = []
        for value in values:
            args.extend(["--opt", value])

        spec_last = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.LAST_WINS)
            },
        )
        spec_collect = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)
            },
        )

        result_last = Parser(spec_last).parse(args)
        result_collect = Parser(spec_collect).parse(args)

        # Property: LAST_WINS == COLLECT[-1]
        last_value = result_last.options["opt"].value
        collect_value = result_collect.options["opt"].value
        assert isinstance(collect_value, tuple)
        assert last_value == collect_value[-1]

    @given(
        count=st.integers(min_value=1, max_value=50),
    )
    def test_count_equals_length_of_collect(self, count: int):
        """Property: COUNT mode result equals length of COLLECT result.

        For any number of flag occurrences, COUNT mode should return the
        same value as the length of COLLECT mode's tuple.
        """
        args = ["--flag"] * count

        spec_count = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag", is_flag=True, accumulation_mode=AccumulationMode.COUNT
                )
            },
        )
        spec_collect = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag", is_flag=True, accumulation_mode=AccumulationMode.COLLECT
                )
            },
        )

        result_count = Parser(spec_count).parse(args)
        result_collect = Parser(spec_collect).parse(args)

        # Property: COUNT == len(COLLECT)
        count_value = result_count.options["flag"].value
        collect_value = result_collect.options["flag"].value
        assert isinstance(collect_value, tuple)
        assert count_value == len(collect_value)

    @given(
        empty_count=st.integers(min_value=1, max_value=5),
    )
    def test_accumulation_with_empty_string_values(self, empty_count: int):
        """Property: Empty strings are valid values and should be preserved.

        Empty strings ("") are valid option values and should be treated
        the same as non-empty strings by all accumulation modes.
        """
        args: list[str] = []
        for _ in range(empty_count):
            args.extend(["--opt", ""])

        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: should collect all empty strings
        assert result.options["opt"].value == ("",) * empty_count

    def test_empty_string_not_confused_with_missing_value(self):
        """Edge case: Empty string is a value, not a missing value.

        When an option receives an empty string as its value, that's
        different from the option having no value at all.
        """
        args_with_empty = ["--opt", ""]
        args_without_value = ["--opt"]

        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt", arity=Arity(0, 1))},
        )
        parser = Parser(spec)

        result_empty = parser.parse(args_with_empty)
        result_no_value = parser.parse(args_without_value)

        # These should be different
        assert result_empty.options["opt"].value == ""
        assert result_no_value.options["opt"].value != ""

    @given(
        values=st.lists(
            st.text(
                alphabet=st.characters(
                    blacklist_categories=("Cs",)
                ),  # Valid Unicode, no surrogates
                min_size=1,
                max_size=20,
            ).filter(lambda x: not x.startswith("-")),
            min_size=1,
            max_size=10,
        ),
    )
    def test_accumulation_with_unicode_values(self, values: list[str]):
        """Property: Unicode values are handled correctly.

        Options should correctly handle values containing Unicode characters,
        emoji, and other non-ASCII text.
        """
        args: list[str] = []
        for value in values:
            args.extend(["--opt", value])

        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec("opt", accumulation_mode=AccumulationMode.COLLECT)
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: Unicode values preserved exactly
        assert result.options["opt"].value == tuple(values)

    @given(
        whitespace=st.text(alphabet=" \t\n\r", min_size=1, max_size=10),
    )
    def test_accumulation_with_whitespace_values(self, whitespace: str):
        """Property: Whitespace-only values are preserved.

        Values that contain only whitespace characters should be treated
        as valid values, not as empty or missing.
        """
        args = ["--opt", whitespace]

        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt")},
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: whitespace preserved exactly
        assert result.options["opt"].value == whitespace

    @example(value="🎉")
    @example(value="Hello, 世界")
    @example(value="Ñoño")
    @example(value="   ")
    @given(
        value=st.text(min_size=1, max_size=50).filter(lambda x: not x.startswith("-")),
    )
    def test_special_characters_roundtrip(self, value: str):
        """Property: All valid string values survive parsing unchanged.

        Any non-option-like string should be parseable as a value and
        returned unchanged.
        """
        args = ["--opt", value]

        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt")},
        )
        parser = Parser(spec)
        result = parser.parse(args)

        # Property: value unchanged
        assert result.options["opt"].value == value


class TestArityValidationProperties:
    """Test that arity validation maintains its invariants."""

    @example(min_arity=0, max_arity=0)  # Zero-arity (flag-like)
    @example(min_arity=1, max_arity=1)  # Exactly one
    @example(min_arity=0, max_arity=None)  # Unbounded
    @given(
        min_arity=st.integers(
            min_value=0, max_value=100
        ),  # Limit to 100 to avoid extreme edge cases
        max_arity=st.integers(min_value=0, max_value=100)
        | st.none(),  # Limit to 100 to avoid extreme edge cases
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

        _validate_arity(Arity(min_arity, max_arity))

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


class TestParserIdempotenceProperties:
    """Test that parser operations are idempotent where expected."""

    @given(
        # Generate random but valid-looking command-line arguments
        args=st.lists(
            st.one_of(
                # Options
                st.text(min_size=2, max_size=10).map(lambda x: f"--{x}"),
                # Values (non-option-like strings)
                st.text(min_size=1, max_size=20).filter(
                    lambda x: not x.startswith("-")
                ),
            ),
            max_size=20,
        ),
    )
    def test_multiple_parses_are_isolated(self, args: list[str]):
        """Property: Multiple parse calls don't affect each other.

        Parsing the same arguments twice with the same parser should
        produce identical results, proving parser state isolation.
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "opt1": OptionSpec("opt1", arity=Arity(0, None)),
                "opt2": OptionSpec("opt2", is_flag=True),
                "verbose": OptionSpec(
                    "verbose", is_flag=True, accumulation_mode=AccumulationMode.COUNT
                ),
            },
        )
        parser = Parser(spec)

        # Parse twice
        try:
            result1 = parser.parse(args)
            result2 = parser.parse(args)

            # Property: results should be identical
            assert result1.options == result2.options
            assert result1.positionals == result2.positionals
            assert result1.extra_args == result2.extra_args
        except Exception as e1:  # noqa: BLE001
            # If first parse fails, second should fail identically
            with pytest.raises(type(e1)):
                _ = parser.parse(args)


class TestBoundaryValues:
    """Explicit boundary value tests to complement property tests.

    While property tests verify invariants across random inputs,
    these tests explicitly check important boundary values.
    """

    @pytest.mark.parametrize("count", [0, 1, 10, 100, 1000])
    def test_count_mode_at_specific_values(self, count: int):
        """Test COUNT mode at specific boundary values."""
        args = ["--flag"] * count
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    "flag", is_flag=True, accumulation_mode=AccumulationMode.COUNT
                )
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)

        if count == 0:
            assert result.options.get("flag") is None
        else:
            assert result.options["flag"].value == count

    @pytest.mark.parametrize(
        ("min_arity", "max_arity", "num_values", "should_pass"),
        [
            (0, 0, 0, True),  # Zero-arity, no values
            (0, 1, 0, True),  # Optional, no values
            (0, 1, 1, True),  # Optional, one value
            (1, 1, 0, False),  # Required, no values (should fail)
            (1, 1, 1, True),  # Required, one value
            (2, 5, 1, False),  # Too few values
            (2, 5, 3, True),  # Within range
            (2, 5, 5, True),  # At max
            (2, 5, 6, True),  # More than max (should stop at 5)
            (0, None, 100, True),  # Unbounded with many values
        ],
    )
    def test_arity_boundaries(
        self,
        min_arity: int,
        max_arity: int | None,
        num_values: int,
        should_pass: bool,  # noqa: FBT001
    ):
        """Test arity validation at specific boundary combinations."""

        values = [f"val{i}" for i in range(num_values)]
        args = ["--opt", *values]

        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt", arity=Arity(min_arity, max_arity))},
        )
        parser = Parser(spec)

        if should_pass:
            result = parser.parse(args)
            # Verify consumed values are within bounds
            if min_arity == 0 and max_arity == 0:
                assert result.options["opt"].value is True
            else:
                consumed = result.options["opt"].value
                if isinstance(consumed, str):
                    consumed = (consumed,)
                elif not isinstance(consumed, tuple):
                    # Handle empty tuple case
                    consumed = ()
                assert len(consumed) >= min_arity
                if max_arity is not None:
                    assert len(consumed) <= max_arity
        else:
            with pytest.raises(InsufficientOptionValuesError):
                _ = parser.parse(args)


class TestOptionValueConsumptionProperties:
    """Test that option value consumption respects arity boundaries."""

    @example(min_arity=0, max_arity=1, num_values=0)  # Regression: empty value list
    @example(min_arity=1, max_arity=1, num_values=1)  # Exact match
    @example(min_arity=0, max_arity=0, num_values=0)  # Zero-arity
    @given(
        min_arity=st.integers(
            min_value=0, max_value=10
        ),  # Limit to 10 for focused testing
        max_arity=st.integers(min_value=0, max_value=10)
        | st.none(),  # Limit to 10 for focused testing
        num_values=st.integers(
            min_value=0, max_value=20
        ),  # Limit to 20 for reasonable test runtime
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

        # Generate dummy values
        values = [f"val{i}" for i in range(num_values)]
        args = ["--opt", *values]

        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt", arity=Arity(min_arity, max_arity))},
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
            options={
                "opt1": OptionSpec("opt1", arity=Arity(0, None)),  # Unbounded
                "opt2": OptionSpec("opt2", arity=Arity(0, None)),  # Unbounded
            },
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


class TestConfigurationInteractionProperties:
    """Test that parser configuration settings interact correctly."""

    @given(
        case_insensitive=st.booleans(),
        convert_underscores=st.booleans(),
        options=option_lists(min_size=2, max_size=8),
    )
    def test_case_sensitivity_consistency(
        self,
        case_insensitive: bool,  # noqa: FBT001
        convert_underscores: bool,  # noqa: FBT001
        options: list[str],
    ):
        """Property: case sensitivity applies consistently to all options.

        When case_insensitive_options is enabled, all option name matching
        should ignore case. When disabled, matching should be case-sensitive.
        """
        # Use only lowercase names for test, replace underscores/digits
        # Parser regex requires names to match specific patterns
        options = [opt.lower().replace("_", "x").replace("-", "y") for opt in options]
        # Keep only alphabetic names (no digits) to avoid regex validation issues
        options = [opt for opt in options if len(opt) >= 2 and opt.isalpha()]

        if len(options) < 2:
            # Not enough valid options, skip this test
            return

        spec = CommandSpec(
            name="cmd",
            options={opt: OptionSpec(opt, is_flag=True) for opt in options},
        )
        config = ParserConfiguration(
            case_insensitive_options=case_insensitive,
            convert_underscores_to_dashes=convert_underscores,
        )
        parser = Parser(spec, config=config)

        # Try parsing with uppercase versions
        args = [f"--{opt.upper()}" for opt in options[:2]]

        if case_insensitive:
            # Should parse successfully
            result = parser.parse(args)
            assert len(result.options) == 2
        else:
            # Should fail with unknown option
            with pytest.raises(UnknownOptionError):
                _ = parser.parse(args)

    @given(
        abbreviation_enabled=st.booleans(),
        min_length=st.integers(min_value=1, max_value=5),
    )
    def test_abbreviation_configuration_respected(
        self,
        abbreviation_enabled: bool,  # noqa: FBT001
        min_length: int,
    ):
        """Property: abbreviation settings are respected consistently.

        When allow_abbreviated_options is enabled, options can be matched
        by prefix. When disabled, only exact matches should work.
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", is_flag=True),
                "version": OptionSpec("version", is_flag=True),
                "verify": OptionSpec("verify", is_flag=True),
            },
        )
        config = ParserConfiguration(
            allow_abbreviated_options=abbreviation_enabled,
            minimum_abbreviation_length=min_length,
        )
        parser = Parser(spec, config=config)

        # Try to use abbreviation that meets minimum length
        abbrev = "ver" if min_length <= 3 else "verbo"
        args = [f"--{abbrev}"]

        if abbreviation_enabled and len(abbrev) >= min_length:
            # Should match but may be ambiguous
            try:
                result = parser.parse(args)
                # If successful, an option was matched
                assert len(result.options) >= 1
            except AmbiguousOptionError:
                # Ambiguity is expected and acceptable with abbreviations
                pass
        else:
            # Should fail with unknown option
            with pytest.raises(UnknownOptionError):
                _ = parser.parse(args)

    @given(
        strict_mode=st.booleans(),
    )
    def test_strict_options_before_positionals(
        self,
        strict_mode: bool,  # noqa: FBT001
    ):
        """Property: strict mode controls option/positional ordering.

        In strict POSIX mode, options must come before positionals.
        In GNU mode, options can appear anywhere.
        """
        spec = CommandSpec(
            name="cmd",
            options={"flag": OptionSpec("flag", is_flag=True)},
        )
        config = ParserConfiguration(
            strict_options_before_positionals=strict_mode,
        )
        parser = Parser(spec, config=config)

        # Option after a positional
        args = ["positional", "--flag"]

        if strict_mode:
            # In strict mode, --flag is treated as a positional
            result = parser.parse(args)
            assert result.options.get("flag") is None
            # Both should be extra_args or error
        else:
            # In GNU mode, --flag is parsed as an option
            result = parser.parse(args)
            assert result.options["flag"].value is True

    @given(
        allow_negative_numbers=st.booleans(),
    )
    def test_negative_number_configuration(
        self,
        allow_negative_numbers: bool,  # noqa: FBT001
    ):
        """Property: negative number parsing respects configuration.

        When allow_negative_numbers is enabled, numeric strings starting
        with - should be treated as values, not options.
        """
        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt")},
        )
        config = ParserConfiguration(
            allow_negative_numbers=allow_negative_numbers,
        )
        parser = Parser(spec, config=config)

        args = ["--opt", "-123"]

        if allow_negative_numbers:
            # Should parse -123 as a value
            result = parser.parse(args)
            assert result.options["opt"].value == "-123"
        else:
            # Should treat -123 as unknown option or insufficient value
            # (depending on whether -1 is treated as option -1, -12, -123, etc.)
            with pytest.raises((UnknownOptionError, InsufficientOptionValuesError)):
                _ = parser.parse(args)

    @given(
        allow_equals=st.booleans(),
        truthy_values=st.sampled_from(
            [
                None,
                ("true", "yes", "1"),
                ("on", "enabled"),
            ]
        ),
        falsey_values=st.sampled_from(
            [
                None,
                ("false", "no", "0"),
                ("off", "disabled"),
            ]
        ),
    )
    def test_flag_value_configuration(
        self,
        allow_equals: bool,  # noqa: FBT001
        truthy_values: tuple[str, ...] | None,
        falsey_values: tuple[str, ...] | None,
    ):
        """Property: flag value configuration is respected.

        When allow_equals_for_flags is enabled, flags can accept explicit
        true/false values. The configured truthy/falsey values should be
        recognized.
        """
        spec = CommandSpec(
            name="cmd",
            options={"flag": OptionSpec("flag", is_flag=True)},
        )
        config = ParserConfiguration(
            allow_equals_for_flags=allow_equals,
            truthy_flag_values=truthy_values,
            falsey_flag_values=falsey_values,
        )
        parser = Parser(spec, config=config)

        # Use first truthy value if custom, else default
        test_value = truthy_values[0] if truthy_values else "true"
        args = [f"--flag={test_value}"]

        if allow_equals:
            # Should parse successfully
            result = parser.parse(args)
            assert result.options["flag"].value is True
        else:
            # Should fail - flags don't accept values
            with pytest.raises(FlagWithValueError):
                _ = parser.parse(args)

    @given(
        flatten_values=st.booleans(),
        occurrence_count=st.integers(min_value=1, max_value=5),
    )
    def test_value_flattening_with_collect_mode(
        self,
        flatten_values: bool,  # noqa: FBT001
        occurrence_count: int,
    ):
        """Property: value flattening works correctly with COLLECT mode.

        The flatten_values setting should affect how values are collected
        in COLLECT mode when multiple values per occurrence are present.
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt",
                    arity=Arity(0, None),  # Unbounded
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=flatten_values,
                ),
            },
        )
        parser = Parser(spec)

        # Build args with multiple values per occurrence
        args: list[str] = []
        for i in range(occurrence_count):
            args.extend(["--opt", f"val{i}a", f"val{i}b"])

        result = parser.parse(args)

        # Verify the result structure
        value = result.options["opt"].value
        assert isinstance(value, tuple)

        # Flattening only affects multiple occurrences with multiple values
        if flatten_values and occurrence_count > 1:
            # Should be flat tuple of all values
            assert all(isinstance(v, str) for v in value)

    @given(
        convert_underscores=st.booleans(),
        use_underscores=st.booleans(),
    )
    def test_underscore_conversion_consistency(
        self,
        convert_underscores: bool,  # noqa: FBT001
        use_underscores: bool,  # noqa: FBT001
    ):
        """Property: underscore conversion applies consistently.

        When convert_underscores_to_dashes is enabled, options with
        underscores should match specifications with dashes, and vice versa.
        """
        # Define option with dashes
        spec = CommandSpec(
            name="cmd",
            options={
                "foo-bar": OptionSpec("foo-bar", is_flag=True),
            },
        )
        config = ParserConfiguration(
            convert_underscores_to_dashes=convert_underscores,
        )
        parser = Parser(spec, config=config)

        # Use underscores in argument
        args = ["--foo_bar"] if use_underscores else ["--foo-bar"]

        if convert_underscores or not use_underscores:
            # Should match
            result = parser.parse(args)
            assert result.options["foo-bar"].value is True
        else:
            # Should not match
            with pytest.raises(UnknownOptionError):
                _ = parser.parse(args)

    @given(
        abbreviation_length=st.integers(min_value=1, max_value=3),
    )
    def test_minimum_abbreviation_length(
        self,
        abbreviation_length: int,
    ):
        """Property: minimum abbreviation length is enforced.

        When abbreviation is enabled, options must match the minimum
        abbreviation length requirement.
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec("verbose", is_flag=True),
                "version": OptionSpec("version", is_flag=True),
            },
        )
        config = ParserConfiguration(
            allow_abbreviated_options=True,
            minimum_abbreviation_length=abbreviation_length,
        )
        parser = Parser(spec, config=config)

        # Try abbreviations of various lengths
        for length in range(1, 4):
            abbrev = "ver"[:length]
            args = [f"--{abbrev}"]

            if length >= abbreviation_length:
                # Should match (may be ambiguous)
                try:
                    result = parser.parse(args)
                    assert len(result.options) >= 1
                except AmbiguousOptionError:
                    # Ambiguity is expected and acceptable with abbreviations
                    pass
            else:
                # Should not match - too short
                with pytest.raises(UnknownOptionError):
                    _ = parser.parse(args)

    @given(
        pairs=option_value_pairs(min_size=2, max_size=5),
    )
    def test_multiple_configuration_options_interact_correctly(
        self,
        pairs: list[tuple[str, str]],
    ):
        """Property: multiple configuration settings work together.

        When multiple configuration options are enabled, they should
        not interfere with each other.
        """
        # Use all lowercase, simple names - replace special chars
        pairs = [
            (opt.lower().replace("_", "x").replace("-", "y"), val) for opt, val in pairs
        ]
        # Keep only valid pairs where option name is alphabetic with length >= 2
        pairs = [(opt, val) for opt, val in pairs if len(opt) >= 2 and opt.isalpha()]
        if len(pairs) < 2:
            # Not enough valid pairs, skip this test
            return

        spec = CommandSpec(
            name="cmd",
            options={opt: OptionSpec(opt) for opt, _ in pairs},
        )
        config = ParserConfiguration(
            case_insensitive_options=True,
            convert_underscores_to_dashes=True,
            allow_abbreviated_options=False,  # Disable to avoid ambiguity
        )
        parser = Parser(spec, config=config)

        # Build args with uppercase names
        args: list[str] = []
        for opt, val in pairs:
            args.extend([f"--{opt.upper()}", val])

        # Should parse successfully with case-insensitive matching
        result = parser.parse(args)

        # Verify all options were parsed
        assert len(result.options) == len(pairs)

        # Verify values match
        for opt, expected_val in pairs:
            assert result.options[opt].value == expected_val
