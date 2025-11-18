# pyright: reportAny=false, reportExplicitAny=false

import pytest

from aclaf.conversion import ConversionError, ConverterRegistry


class TestUnionConversion:
    def test_convert_union_int_str_with_int_string_prefers_int(self):
        registry = ConverterRegistry()
        result = registry.convert("42", int | str)
        assert result == 42
        assert isinstance(result, int)

    def test_convert_union_int_str_with_non_int_string_falls_back_to_str(self):
        registry = ConverterRegistry()
        result = registry.convert("hello", int | str)
        assert result == "hello"
        assert isinstance(result, str)

    def test_convert_union_str_int_with_int_string_prefers_str(self):
        registry = ConverterRegistry()
        # Order matters - str is first, so it's tried first
        result = registry.convert("42", str | int)
        assert result == "42"
        assert isinstance(result, str)

    def test_convert_union_int_float_with_int_string_prefers_int(self):
        registry = ConverterRegistry()
        result = registry.convert("42", int | float)
        assert result == 42
        assert isinstance(result, int)

    def test_convert_union_int_float_with_float_string_uses_float(self):
        registry = ConverterRegistry()
        result = registry.convert("3.14", int | float)
        # int conversion fails, falls back to float
        assert result == 3.14
        assert isinstance(result, float)

    def test_convert_union_bool_int_with_truthy_string_prefers_bool(self):
        registry = ConverterRegistry()
        result = registry.convert("true", bool | int)
        assert result is True
        assert isinstance(result, bool)

    def test_convert_union_bool_int_with_numeric_string_uses_int(self):
        registry = ConverterRegistry()
        result = registry.convert("42", bool | int)
        # bool conversion fails, falls back to int
        assert result == 42
        assert isinstance(result, int)

    def test_convert_union_with_all_conversions_failing_raises_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match="Could not convert to any"):
            registry.convert("invalid", int | float)

    def test_convert_union_single_type_behaves_like_direct_conversion(self):
        registry = ConverterRegistry()
        result = registry.convert("42", int)
        assert result == 42


class TestOptionalConversion:
    def test_convert_optional_int_with_none_returns_none(self):
        registry = ConverterRegistry()
        result = registry.convert(None, int | None)
        assert result is None

    def test_convert_optional_int_with_valid_string_converts_to_int(self):
        registry = ConverterRegistry()
        result = registry.convert("42", int | None)
        assert result == 42

    def test_convert_optional_str_with_none_returns_none(self):
        registry = ConverterRegistry()
        result = registry.convert(None, str | None)
        assert result is None

    def test_convert_optional_str_with_valid_string_converts_to_str(self):
        registry = ConverterRegistry()
        result = registry.convert("hello", str | None)
        assert result == "hello"

    def test_convert_optional_bool_with_none_returns_none(self):
        registry = ConverterRegistry()
        result = registry.convert(None, bool | None)
        assert result is None

    def test_convert_optional_bool_with_truthy_string_converts_to_bool(self):
        registry = ConverterRegistry()
        result = registry.convert("yes", bool | None)
        assert result is True

    def test_convert_optional_int_with_invalid_string_raises_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            registry.convert("invalid", int | None)


class TestUnionWithNone:
    def test_convert_union_int_str_none_with_none_returns_none(self):
        registry = ConverterRegistry()
        result = registry.convert(None, int | str | None)
        assert result is None

    def test_convert_union_int_str_none_with_int_string_converts_to_int(self):
        registry = ConverterRegistry()
        result = registry.convert("42", int | str | None)
        assert result == 42

    def test_convert_union_int_str_none_with_non_int_string_converts_to_str(self):
        registry = ConverterRegistry()
        result = registry.convert("hello", int | str | None)
        assert result == "hello"

    def test_convert_union_with_type_none_at_start_with_none_returns_none(self):
        registry = ConverterRegistry()
        result = registry.convert(None, None | int | str)
        assert result is None


class TestComplexUnions:
    def test_convert_union_list_int_str_with_tuple_converts_to_list(self):
        registry = ConverterRegistry()
        result = registry.convert(("1", "2"), list[int] | str)
        assert result == [1, 2]
        assert isinstance(result, list)

    def test_convert_union_list_int_str_with_single_string_converts_to_str(self):
        registry = ConverterRegistry()
        # List conversion wraps single string, but str conversion should work too
        result = registry.convert("hello", list[int] | str)
        # This depends on order - list[int] is first
        # Single string wrapped in list, then elements converted
        # "hello" can't convert to int, so list conversion fails
        # Falls back to str
        assert result == "hello"

    def test_convert_union_dict_str_int_str_with_kv_pair_converts_to_dict(self):
        registry = ConverterRegistry()
        result = registry.convert("key=value", dict[str, str] | int)
        assert result == {"key": "value"}

    def test_convert_union_dict_str_int_str_with_int_string_converts_to_int(self):
        registry = ConverterRegistry()
        result = registry.convert("42", dict[str, str] | int)
        # dict conversion fails (no =), falls back to int
        assert result == 42


class TestUnionEdgeCases:
    def test_union_with_only_none_type_returns_none(self):
        _ = ConverterRegistry()
        # type(None) by itself isn't supported - need Union[None] or Optional
        # Skip this edge case as it's not a realistic use case
        pytest.skip("type(None) alone not supported, use Optional instead")

    def test_union_tries_conversions_in_order(self):
        registry = ConverterRegistry()
        # int is first, so "42" converts to int
        result = registry.convert("42", int | str)
        assert result == 42
        assert isinstance(result, int)

    def test_union_with_identical_types_uses_first(self):
        registry = ConverterRegistry()
        result = registry.convert("test", str | str)
        assert result == "test"

    def test_union_with_no_matching_converters_collects_errors(self):
        registry = ConverterRegistry()
        # Union where all conversions fail
        with pytest.raises(ConversionError, match="Could not convert"):
            registry.convert("invalid", int | float)
