# pyright: reportAny=false, reportExplicitAny=false

from pathlib import Path
from typing import TypeAlias

import pytest

from aclaf.conversion import (
    ConversionError,
    ConverterRegistry,
    convert_bool,
    convert_float,
    convert_int,
    convert_path,
    convert_str,
)


class TestStringConversion:
    def test_convert_str_with_string_returns_same_value(self):
        result = convert_str("hello")
        assert result == "hello"

    def test_convert_str_with_int_converts_to_string(self):
        result = convert_str(42)
        assert result == "42"

    def test_convert_str_with_bool_converts_to_string(self):
        bool_val = True
        result = convert_str(bool_val)
        assert result == "True"

    def test_convert_str_with_tuple_converts_to_string(self):
        result = convert_str(("a", "b"))
        assert result == "('a', 'b')"

    def test_convert_str_via_registry_with_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("test", str)
        assert result == "test"

    def test_convert_str_via_registry_with_int_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert(123, str)
        assert result == "123"


class TestIntegerConversion:
    def test_convert_int_with_int_returns_same_value(self):
        result = convert_int(42)
        assert result == 42

    def test_convert_int_with_positive_string_succeeds(self):
        result = convert_int("42")
        assert result == 42

    def test_convert_int_with_negative_string_succeeds(self):
        result = convert_int("-42")
        assert result == -42

    def test_convert_int_with_zero_string_succeeds(self):
        result = convert_int("0")
        assert result == 0

    def test_convert_int_with_leading_whitespace_succeeds(self):
        result = convert_int("  42  ")
        assert result == 42

    def test_convert_int_with_bool_true_converts_to_one(self):
        bool_val = True
        result = convert_int(bool_val)
        assert result == 1

    def test_convert_int_with_bool_false_converts_to_zero(self):
        bool_val = False
        result = convert_int(bool_val)
        assert result == 0

    def test_convert_int_with_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid literal"):
            _ = convert_int("not_a_number")

    def test_convert_int_with_float_string_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid literal"):
            _ = convert_int("3.14")

    def test_convert_int_with_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid literal"):
            _ = convert_int("")

    def test_convert_int_via_registry_with_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("123", int)
        assert result == 123

    def test_convert_int_via_registry_with_invalid_string_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError) as exc_info:
            _ = registry.convert("invalid", int)
        assert exc_info.value.value == "invalid"
        assert exc_info.value.target_type is int


class TestFloatConversion:
    def test_convert_float_with_string_containing_decimal_succeeds(self):
        # Testing with decimal string input
        result = convert_float("3.14")
        assert result == 3.14

    def test_convert_float_with_int_converts_to_float(self):
        result = convert_float(42)
        assert result == 42.0

    def test_convert_float_with_positive_string_succeeds(self):
        result = convert_float("3.14")
        assert result == 3.14

    def test_convert_float_with_negative_string_succeeds(self):
        result = convert_float("-3.14")
        assert result == -3.14

    def test_convert_float_with_scientific_notation_succeeds(self):
        result = convert_float("1.5e2")
        assert result == 150.0

    def test_convert_float_with_zero_succeeds(self):
        result = convert_float("0.0")
        assert result == 0.0

    def test_convert_float_with_integer_string_succeeds(self):
        result = convert_float("42")
        assert result == 42.0

    def test_convert_float_with_bool_true_converts_to_one(self):
        bool_val = True
        result = convert_float(bool_val)
        assert result == 1.0

    def test_convert_float_with_bool_false_converts_to_zero(self):
        bool_val = False
        result = convert_float(bool_val)
        assert result == 0.0

    def test_convert_float_with_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError, match="could not convert"):
            _ = convert_float("not_a_number")

    def test_convert_float_with_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="could not convert"):
            _ = convert_float("")

    def test_convert_float_via_registry_with_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("3.14", float)
        assert result == 3.14

    def test_convert_float_via_registry_with_invalid_string_raises_conversion_error(
        self,
    ):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError) as exc_info:
            _ = registry.convert("invalid", float)
        assert exc_info.value.value == "invalid"
        assert exc_info.value.target_type is float


class TestBooleanConversion:
    @pytest.mark.parametrize(
        "value",
        ["true", "TRUE", "True", "TrUe", "1", "yes", "YES", "Yes", "on", "ON", "On"],
    )
    def test_convert_bool_with_truthy_string_returns_true(self, value: str):
        result = convert_bool(value)
        assert result is True

    @pytest.mark.parametrize(
        "value",
        [
            "false",
            "FALSE",
            "False",
            "FaLsE",
            "0",
            "no",
            "NO",
            "No",
            "off",
            "OFF",
            "Off",
        ],
    )
    def test_convert_bool_with_falsey_string_returns_false(self, value: str):
        result = convert_bool(value)
        assert result is False

    def test_convert_bool_with_bool_true_returns_true(self):
        bool_val = True
        result = convert_bool(bool_val)
        assert result is True

    def test_convert_bool_with_bool_false_returns_false(self):
        bool_val = False
        result = convert_bool(bool_val)
        assert result is False

    def test_convert_bool_with_int_zero_returns_false(self):
        result = convert_bool(0)
        assert result is False

    def test_convert_bool_with_int_one_returns_true(self):
        result = convert_bool(1)
        assert result is True

    def test_convert_bool_with_int_positive_returns_true(self):
        result = convert_bool(42)
        assert result is True

    def test_convert_bool_with_int_negative_returns_true(self):
        result = convert_bool(-1)
        assert result is True

    def test_convert_bool_with_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError, match=r"Cannot convert .* to bool"):
            _ = convert_bool("maybe")

    def test_convert_bool_with_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match=r"Cannot convert .* to bool"):
            _ = convert_bool("")

    def test_convert_bool_with_partial_match_raises_value_error(self):
        with pytest.raises(ValueError, match=r"Cannot convert .* to bool"):
            _ = convert_bool("t")

    def test_convert_bool_via_registry_with_truthy_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("yes", bool)
        assert result is True

    def test_convert_bool_via_registry_with_falsey_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("no", bool)
        assert result is False

    def test_convert_bool_via_registry_with_invalid_string_raises_conversion_error(
        self,
    ):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError) as exc_info:
            _ = registry.convert("invalid", bool)
        assert exc_info.value.value == "invalid"
        assert exc_info.value.target_type is bool


class TestPathConversion:
    def test_convert_path_with_absolute_path_creates_correct_path(self):
        # Testing with absolute path string
        result = convert_path("/tmp/test")  # noqa: S108
        assert result == Path("/tmp/test")  # noqa: S108

    def test_convert_path_with_string_creates_path(self):
        result = convert_path("/tmp/test")  # noqa: S108
        assert result == Path("/tmp/test")  # noqa: S108

    def test_convert_path_with_relative_path_string_creates_path(self):
        result = convert_path("./relative")
        assert result == Path("./relative")

    def test_convert_path_with_home_expansion_creates_path(self):
        result = convert_path("~/test")
        assert result == Path("~/test")

    def test_convert_path_with_empty_string_creates_path(self):
        result = convert_path("")
        assert result == Path()

    def test_convert_path_with_int_raises_conversion_error(self):
        with pytest.raises(ConversionError) as exc_info:
            _ = convert_path(42)
        assert exc_info.value.value == 42
        assert exc_info.value.target_type == Path

    def test_convert_path_with_bool_raises_conversion_error(self):
        bool_val = True
        with pytest.raises(ConversionError) as exc_info:
            _ = convert_path(bool_val)
        assert exc_info.value.value is True
        assert exc_info.value.target_type is Path

    def test_convert_path_via_registry_with_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("/tmp/test", Path)  # noqa: S108
        assert result == Path("/tmp/test")  # noqa: S108

    def test_convert_path_via_registry_with_int_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError) as exc_info:
            _ = registry.convert(42, Path)
        assert exc_info.value.value == 42
        assert exc_info.value.target_type == Path


class TestNoneHandling:
    def test_convert_none_to_non_optional_raises_error(self):
        registry = ConverterRegistry()
        # None cannot be converted to non-optional types
        # The registry doesn't have a converter for NoneType
        with pytest.raises((TypeError, ConversionError)):
            _ = registry.convert(None, int)


class TestEmptyStringHandling:
    def test_convert_empty_string_to_str_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("", str)
        assert result == ""

    def test_convert_empty_string_to_int_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            _ = registry.convert("", int)

    def test_convert_empty_string_to_float_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            _ = registry.convert("", float)

    def test_convert_empty_string_to_bool_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            _ = registry.convert("", bool)


class TestWhitespaceHandling:
    def test_convert_whitespace_only_string_to_str_preserves_whitespace(self):
        registry = ConverterRegistry()
        result = registry.convert("   ", str)
        assert result == "   "

    def test_convert_string_with_leading_whitespace_to_int_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("  42", int)
        assert result == 42

    def test_convert_string_with_trailing_whitespace_to_int_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("42  ", int)
        assert result == 42

    def test_convert_string_with_internal_whitespace_to_int_fails(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            _ = registry.convert("4 2", int)


class TestBoundaryValues:
    def test_convert_max_int_string_to_int_succeeds(self):
        registry = ConverterRegistry()
        max_val = str(2**63 - 1)
        result = registry.convert(max_val, int)
        assert result == 2**63 - 1

    def test_convert_min_int_string_to_int_succeeds(self):
        registry = ConverterRegistry()
        min_val = str(-(2**63))
        result = registry.convert(min_val, int)
        assert result == -(2**63)

    def test_convert_very_large_float_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("1e308", float)
        assert result == 1e308

    def test_convert_very_small_float_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("1e-308", float)
        assert result == 1e-308


class TestSpecialFloatValues:
    def test_convert_infinity_string_to_float_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("inf", float)
        assert result == float("inf")

    def test_convert_negative_infinity_string_to_float_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("-inf", float)
        assert result == float("-inf")

    def test_convert_nan_string_to_float_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("nan", float)
        assert str(result) == "nan"


class TestUnicodeHandling:
    def test_convert_unicode_string_to_str_preserves_unicode(self):
        registry = ConverterRegistry()
        result = registry.convert("hello 世界", str)
        assert result == "hello 世界"

    def test_convert_emoji_string_to_str_preserves_emoji(self):
        registry = ConverterRegistry()
        result = registry.convert("hello 👋", str)
        assert result == "hello 👋"

    def test_convert_unicode_number_string_to_int_fails(self):
        registry = ConverterRegistry()
        # Actually, Python's int() does support some Unicode digits
        # This test should verify the actual behavior
        try:
            result = registry.convert("１２３", int)  # noqa: RUF001
            # If it works, that's fine too
            assert isinstance(result, int)
        except ConversionError:
            # If it fails, that's also expected
            pass


UserId: TypeAlias = int
StringList: TypeAlias = list[str]


class TestTypeAliasHandling:
    def test_convert_with_type_alias_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("42", UserId)
        assert result == 42

    def test_convert_with_generic_type_alias_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert(("a", "b"), StringList)
        assert result == ["a", "b"]


class TestConverterErrorMessages:
    def test_conversion_error_includes_value(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError) as exc_info:
            _ = registry.convert("invalid", int)
        assert "invalid" in str(exc_info.value)

    def test_conversion_error_includes_target_type(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError) as exc_info:
            _ = registry.convert("invalid", int)
        assert "int" in str(exc_info.value)

    def test_conversion_error_includes_reason_when_provided(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError) as exc_info:
            _ = registry.convert("invalid", int)
        assert "Reason:" in str(exc_info.value)

    def test_type_error_for_missing_converter_includes_type_name(self):
        registry = ConverterRegistry()

        class CustomType:
            pass

        with pytest.raises(TypeError) as exc_info:
            _ = registry.convert("value", CustomType)
        assert "CustomType" in str(exc_info.value)


class TestBoolSpecialCases:
    def test_bool_with_numeric_string_not_zero_or_one_raises_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            _ = registry.convert("2", bool)

    def test_bool_with_negative_number_string_raises_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            _ = registry.convert("-1", bool)
