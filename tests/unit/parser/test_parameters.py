"""Error path tests for parameter validation (_parameters.py).

This module focuses on error cases and boundary conditions in parameter
validation that are not covered by test_spec_validation.py. Specifically,
it tests:

- Empty frozensets for flag values (lines 186-190, 208-212)
- Empty strings within flag value frozensets (lines 194-198, 216-220)
- Edge cases in validation logic
"""

import pytest

from aclaf.parser import OptionSpec


class TestTruthyFlagValueValidation:
    """Test truthy_flag_values validation error paths."""

    def test_empty_frozenset_raises_error(self):
        """Empty truthy_flag_values frozenset raises ValueError.

        This tests the validation at lines 185-190 in _parameters.py.
        An empty frozenset is invalid because it provides no valid truthy
        values for flag coercion.
        """
        with pytest.raises(
            ValueError,
            match=r"truthy_flag_values must not be empty.*at least one truthy value",
        ):
            _ = OptionSpec("verbose", truthy_flag_values=frozenset())

    def test_frozenset_with_empty_string_raises_error(self):
        """Frozenset containing empty string raises ValueError.

        This tests the validation at lines 192-198 in _parameters.py.
        Empty strings are invalid flag values as they cannot meaningfully
        represent true/false.
        """
        with pytest.raises(
            ValueError,
            match=r"truthy_flag_values must contain only non-empty strings.*index 0",
        ):
            _ = OptionSpec("verbose", truthy_flag_values=frozenset({""}))

    def test_frozenset_with_empty_string_among_valid_raises_error(self):
        """Frozenset with mix of valid and empty strings raises ValueError.

        Tests that validation catches empty strings even when mixed with
        valid values. The error message should indicate which index failed.
        """
        with pytest.raises(
            ValueError,
            match=r"truthy_flag_values must contain only non-empty strings.*index \d+",
        ):
            _ = OptionSpec("verbose", truthy_flag_values=frozenset({"yes", ""}))

    def test_none_value_accepted(self):
        """None is accepted for truthy_flag_values (means use defaults).

        This verifies the early return at line 182-183 works correctly.
        """
        opt = OptionSpec("verbose", truthy_flag_values=None)
        assert opt.truthy_flag_values is None


class TestFalseyFlagValueValidation:
    """Test falsey_flag_values validation error paths."""

    def test_empty_frozenset_raises_error(self):
        """Empty falsey_flag_values frozenset raises ValueError.

        This tests the validation at lines 207-212 in _parameters.py.
        An empty frozenset is invalid because it provides no valid falsey
        values for flag coercion.
        """
        with pytest.raises(
            ValueError,
            match=r"falsey_flag_values must not be empty.*at least one falsey value",
        ):
            _ = OptionSpec("verbose", falsey_flag_values=frozenset())

    def test_frozenset_with_empty_string_raises_error(self):
        """Frozenset containing empty string raises ValueError.

        This tests the validation at lines 214-220 in _parameters.py.
        Empty strings are invalid flag values as they cannot meaningfully
        represent true/false.
        """
        with pytest.raises(
            ValueError,
            match=r"falsey_flag_values must contain only non-empty strings.*index 0",
        ):
            _ = OptionSpec("verbose", falsey_flag_values=frozenset({""}))

    def test_frozenset_with_empty_string_among_valid_raises_error(self):
        """Frozenset with mix of valid and empty strings raises ValueError.

        Tests that validation catches empty strings even when mixed with
        valid values. The error message should indicate which index failed.
        """
        with pytest.raises(
            ValueError,
            match=r"falsey_flag_values must contain only non-empty strings.*index \d+",
        ):
            _ = OptionSpec("verbose", falsey_flag_values=frozenset({"no", ""}))

    def test_none_value_accepted(self):
        """None is accepted for falsey_flag_values (means use defaults).

        This verifies the early return at line 204-205 works correctly.
        """
        opt = OptionSpec("verbose", falsey_flag_values=None)
        assert opt.falsey_flag_values is None


class TestFlagValueValidationInteraction:
    """Test interaction between truthy and falsey flag value validation."""

    def test_both_empty_raises_errors(self):
        """Both empty frozensets raise ValueError for falsey first.

        When both are empty, falsey validation runs first (line 93) and raises.
        """
        with pytest.raises(
            ValueError,
            match=r"falsey_flag_values must not be empty",
        ):
            _ = OptionSpec(
                "verbose",
                truthy_flag_values=frozenset(),
                falsey_flag_values=frozenset(),
            )

    def test_truthy_empty_string_falsey_valid(self):
        """Empty string in truthy with valid falsey raises error.

        Falsey validation runs first and passes, then truthy validation raises.
        """
        with pytest.raises(
            ValueError,
            match=r"truthy_flag_values must contain only non-empty strings",
        ):
            _ = OptionSpec(
                "verbose",
                truthy_flag_values=frozenset({""}),
                falsey_flag_values=frozenset({"no"}),
            )

    def test_truthy_valid_falsey_empty_string(self):
        """Valid truthy with empty string in falsey raises error.

        After truthy validation passes, falsey validation runs.
        """
        with pytest.raises(
            ValueError,
            match=r"falsey_flag_values must contain only non-empty strings",
        ):
            _ = OptionSpec(
                "verbose",
                truthy_flag_values=frozenset({"yes"}),
                falsey_flag_values=frozenset({""}),
            )

    def test_both_valid_values_accepted(self):
        """Both valid frozensets are accepted."""
        opt = OptionSpec(
            "verbose",
            truthy_flag_values=frozenset({"yes", "y", "true"}),
            falsey_flag_values=frozenset({"no", "n", "false"}),
        )
        assert opt.truthy_flag_values == frozenset({"yes", "y", "true"})
        assert opt.falsey_flag_values == frozenset({"no", "n", "false"})


class TestFlagValueEdgeCases:
    """Test edge cases in flag value validation."""

    def test_single_char_truthy_values(self):
        """Single character strings are valid truthy values."""
        opt = OptionSpec("verbose", truthy_flag_values=frozenset({"y"}))
        assert opt.truthy_flag_values is not None
        assert "y" in opt.truthy_flag_values

    def test_single_char_falsey_values(self):
        """Single character strings are valid falsey values."""
        opt = OptionSpec("verbose", falsey_flag_values=frozenset({"n"}))
        assert opt.falsey_flag_values is not None
        assert "n" in opt.falsey_flag_values

    def test_numeric_string_truthy_values(self):
        """Numeric strings are valid truthy values."""
        opt = OptionSpec("verbose", truthy_flag_values=frozenset({"1"}))
        assert opt.truthy_flag_values is not None
        assert "1" in opt.truthy_flag_values

    def test_numeric_string_falsey_values(self):
        """Numeric strings are valid falsey values."""
        opt = OptionSpec("verbose", falsey_flag_values=frozenset({"0"}))
        assert opt.falsey_flag_values is not None
        assert "0" in opt.falsey_flag_values

    def test_whitespace_only_string_truthy_values(self):
        """Whitespace-only strings are technically valid (non-empty)."""
        opt = OptionSpec("verbose", truthy_flag_values=frozenset({" "}))
        assert opt.truthy_flag_values is not None
        assert " " in opt.truthy_flag_values

    def test_whitespace_only_string_falsey_values(self):
        """Whitespace-only strings are technically valid (non-empty)."""
        opt = OptionSpec("verbose", falsey_flag_values=frozenset({" "}))
        assert opt.falsey_flag_values is not None
        assert " " in opt.falsey_flag_values
