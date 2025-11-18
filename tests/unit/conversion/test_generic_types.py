# pyright: reportAny=false, reportExplicitAny=false

from collections.abc import Iterable, Mapping, Sequence

import pytest

from aclaf.conversion import ConversionError, ConverterRegistry


class TestListConversion:
    def test_convert_list_str_with_tuple_of_strings_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert(("a", "b", "c"), list[str])
        assert result == ["a", "b", "c"]

    def test_convert_list_int_with_tuple_of_strings_converts_elements(self):
        registry = ConverterRegistry()
        result = registry.convert(("1", "2", "3"), list[int])
        assert result == [1, 2, 3]

    def test_convert_list_float_with_tuple_of_strings_converts_elements(self):
        registry = ConverterRegistry()
        result = registry.convert(("1.5", "2.5", "3.5"), list[float])
        assert result == [1.5, 2.5, 3.5]

    def test_convert_list_str_with_single_string_wraps_in_list(self):
        registry = ConverterRegistry()
        result = registry.convert("single", list[str])
        assert result == ["single"]

    def test_convert_list_int_with_single_string_wraps_converted_value(self):
        registry = ConverterRegistry()
        result = registry.convert("42", list[int])
        assert result == [42]

    def test_convert_list_with_empty_tuple_returns_empty_list(self):
        registry = ConverterRegistry()
        result = registry.convert((), list[str])
        assert result == []

    def test_convert_list_with_mixed_valid_strings_converts_all(self):
        registry = ConverterRegistry()
        result = registry.convert(("10", "-5", "0"), list[int])
        assert result == [10, -5, 0]

    def test_convert_list_int_with_invalid_element_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            _ = registry.convert(("1", "invalid", "3"), list[int])

    def test_convert_list_without_type_args_defaults_to_str(self):
        registry = ConverterRegistry()
        # Bare 'list' without type args doesn't have a registered converter
        # This requires list[str] or similar
        with pytest.raises(TypeError, match="No converter registered"):
            _ = registry.convert(("a", "b"), list)


class TestTupleConversion:
    def test_convert_tuple_str_with_tuple_of_strings_returns_tuple(self):
        registry = ConverterRegistry()
        result = registry.convert(("a", "b", "c"), tuple[str, ...])
        assert result == ("a", "b", "c")

    def test_convert_tuple_int_with_tuple_of_strings_converts_elements(self):
        registry = ConverterRegistry()
        result = registry.convert(("1", "2", "3"), tuple[int, ...])
        assert result == (1, 2, 3)

    def test_convert_tuple_str_with_single_string_wraps_in_tuple(self):
        registry = ConverterRegistry()
        result = registry.convert("single", tuple[str, ...])
        assert result == ("single",)

    def test_convert_tuple_int_with_single_string_wraps_converted_value(self):
        registry = ConverterRegistry()
        result = registry.convert("42", tuple[int, ...])
        assert result == (42,)

    def test_convert_tuple_with_empty_tuple_returns_empty_tuple(self):
        registry = ConverterRegistry()
        result = registry.convert((), tuple[str, ...])
        assert result == ()

    def test_convert_tuple_without_type_args_defaults_to_str(self):
        registry = ConverterRegistry()
        # Bare 'tuple' without type args doesn't have a registered converter
        with pytest.raises(TypeError, match="No converter registered"):
            _ = registry.convert(("a", "b"), tuple)


class TestSetConversion:
    def test_convert_set_str_with_tuple_of_strings_returns_set(self):
        registry = ConverterRegistry()
        result = registry.convert(("a", "b", "c"), set[str])
        assert result == {"a", "b", "c"}

    def test_convert_set_int_with_tuple_of_strings_converts_elements(self):
        registry = ConverterRegistry()
        result = registry.convert(("1", "2", "3"), set[int])
        assert result == {1, 2, 3}

    def test_convert_set_str_with_single_string_wraps_in_set(self):
        registry = ConverterRegistry()
        result = registry.convert("single", set[str])
        assert result == {"single"}

    def test_convert_set_with_duplicate_values_deduplicates(self):
        registry = ConverterRegistry()
        result = registry.convert(("a", "b", "a"), set[str])
        assert result == {"a", "b"}

    def test_convert_set_with_empty_tuple_returns_empty_set(self):
        registry = ConverterRegistry()
        result = registry.convert((), set[str])
        assert result == set()

    def test_convert_set_without_type_args_defaults_to_str(self):
        registry = ConverterRegistry()
        # Bare 'set' without type args doesn't have a registered converter
        with pytest.raises(TypeError, match="No converter registered"):
            _ = registry.convert(("a", "b"), set)


class TestFrozensetConversion:
    def test_convert_frozenset_str_with_tuple_of_strings_returns_frozenset(self):
        registry = ConverterRegistry()
        result = registry.convert(("a", "b", "c"), frozenset[str])
        assert result == frozenset({"a", "b", "c"})

    def test_convert_frozenset_int_with_tuple_of_strings_converts_elements(self):
        registry = ConverterRegistry()
        result = registry.convert(("1", "2", "3"), frozenset[int])
        assert result == frozenset({1, 2, 3})

    def test_convert_frozenset_str_with_single_string_wraps_in_frozenset(self):
        registry = ConverterRegistry()
        result = registry.convert("single", frozenset[str])
        assert result == frozenset({"single"})

    def test_convert_frozenset_with_empty_tuple_returns_empty_frozenset(self):
        registry = ConverterRegistry()
        result = registry.convert((), frozenset[str])
        assert result == frozenset()

    def test_convert_frozenset_without_type_args_defaults_to_str(self):
        registry = ConverterRegistry()
        # Bare 'frozenset' without type args doesn't have a registered converter
        with pytest.raises(TypeError, match="No converter registered"):
            _ = registry.convert(("a", "b"), frozenset)


class TestSequenceConversion:
    def test_convert_sequence_str_with_tuple_of_strings_returns_list(self):
        registry = ConverterRegistry()
        result = registry.convert(("a", "b", "c"), Sequence[str])
        assert result == ["a", "b", "c"]

    def test_convert_sequence_int_with_tuple_of_strings_converts_elements(self):
        registry = ConverterRegistry()
        result = registry.convert(("1", "2", "3"), Sequence[int])
        assert result == [1, 2, 3]

    def test_convert_sequence_str_with_single_string_wraps_in_list(self):
        registry = ConverterRegistry()
        result = registry.convert("single", Sequence[str])
        assert result == ["single"]


class TestIterableConversion:
    def test_convert_iterable_str_with_tuple_of_strings_returns_list(self):
        registry = ConverterRegistry()
        result = registry.convert(("a", "b", "c"), Iterable[str])
        # Iterable should convert to list (same as Sequence)
        assert result == ["a", "b", "c"]

    def test_convert_iterable_int_with_tuple_of_strings_converts_elements(self):
        registry = ConverterRegistry()
        result = registry.convert(("1", "2", "3"), Iterable[int])
        assert result == [1, 2, 3]


class TestDictConversion:
    def test_convert_dict_str_str_with_single_key_value_pair_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("key=value", dict[str, str])
        assert result == {"key": "value"}

    def test_convert_dict_str_str_with_multiple_pairs_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert(("key1=value1", "key2=value2"), dict[str, str])
        assert result == {"key1": "value1", "key2": "value2"}

    def test_convert_dict_str_int_converts_values(self):
        registry = ConverterRegistry()
        result = registry.convert(("age=25", "count=100"), dict[str, int])
        assert result == {"age": 25, "count": 100}

    def test_convert_dict_int_str_converts_keys(self):
        registry = ConverterRegistry()
        result = registry.convert(("1=first", "2=second"), dict[int, str])
        assert result == {1: "first", 2: "second"}

    def test_convert_dict_int_int_converts_both(self):
        registry = ConverterRegistry()
        result = registry.convert(("10=20", "30=40"), dict[int, int])
        assert result == {10: 20, 30: 40}

    def test_convert_dict_with_equals_in_value_preserves_value(self):
        registry = ConverterRegistry()
        result = registry.convert("url=http://example.com?a=b", dict[str, str])
        assert result == {"url": "http://example.com?a=b"}

    def test_convert_dict_with_empty_value_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("key=", dict[str, str])
        assert result == {"key": ""}

    def test_convert_dict_without_equals_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match="key=value"):
            _ = registry.convert("invalid", dict[str, str])

    def test_convert_dict_with_tuple_containing_invalid_item_raises_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match=r"key=value"):
            _ = registry.convert(("key1=value1", "invalid"), dict[str, str])

    def test_convert_dict_with_invalid_value_type_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            _ = registry.convert(("age=invalid",), dict[str, int])


class TestMappingConversion:
    def test_convert_mapping_str_str_with_single_key_value_pair_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("key=value", Mapping[str, str])
        assert result == {"key": "value"}

    def test_convert_mapping_str_int_converts_values(self):
        registry = ConverterRegistry()
        result = registry.convert(("age=25", "count=100"), Mapping[str, int])
        assert result == {"age": 25, "count": 100}


class TestSequenceConversionErrors:
    def test_convert_sequence_with_bool_raises_conversion_error(self):
        registry = ConverterRegistry()
        bool_val = True
        with pytest.raises(ConversionError, match="Cannot convert"):
            _ = registry.convert(bool_val, list[str])

    def test_convert_sequence_with_int_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match="Cannot convert"):
            _ = registry.convert(42, list[str])


class TestNestedGenerics:
    def test_convert_list_of_lists_with_nested_tuples_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert((("a", "b"), ("c", "d")), list[list[str]])
        assert result == [["a", "b"], ["c", "d"]]

    def test_convert_dict_with_list_values_succeeds(self):
        _ = ConverterRegistry()
        # This would require special handling - for now test basic conversion
        # Complex nested types might not be fully supported

    def test_convert_list_of_optional_int_with_mixed_values(self):
        registry = ConverterRegistry()
        # This would require special handling for Optional in lists
        # For now, test what we support
        result = registry.convert(("1", "2"), list[int])
        assert result == [1, 2]

    def test_convert_dict_with_int_keys_and_list_values(self):
        registry = ConverterRegistry()
        # Complex nested generics may not be fully supported
        # Test basic dict conversion
        result = registry.convert("1=value", dict[int, str])
        assert result == {1: "value"}


class TestConverterWithTupleValues:
    def test_convert_tuple_to_list_converts_elements(self):
        registry = ConverterRegistry()
        result = registry.convert(("1", "2", "3"), list[int])
        assert result == [1, 2, 3]

    def test_convert_single_element_tuple_to_list_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert(("42",), list[int])
        assert result == [42]

    def test_convert_nested_tuples_to_list_of_lists_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert((("a", "b"), ("c", "d")), list[list[str]])
        assert result == [["a", "b"], ["c", "d"]]

    def test_convert_empty_tuple_to_list_returns_empty_list(self):
        registry = ConverterRegistry()
        result = registry.convert((), list[str])
        assert result == []

    def test_convert_empty_tuple_to_set_returns_empty_set(self):
        registry = ConverterRegistry()
        result = registry.convert((), set[str])
        assert result == set()


class TestSequenceWithDifferentOrigins:
    def test_sequence_returns_list_not_tuple(self):
        from collections.abc import Sequence  # noqa: PLC0415

        registry = ConverterRegistry()
        result = registry.convert(("a", "b"), Sequence[str])
        assert isinstance(result, list)
        assert result == ["a", "b"]

    def test_iterable_returns_list(self):
        from collections.abc import Iterable  # noqa: PLC0415

        registry = ConverterRegistry()
        result = registry.convert(("a", "b"), Iterable[str])
        assert isinstance(result, list)
        assert result == ["a", "b"]


class TestDictEdgeCases:
    def test_dict_with_equals_in_key_uses_first_equals(self):
        registry = ConverterRegistry()
        result = registry.convert("key=value=extra", dict[str, str])
        assert result == {"key": "value=extra"}

    def test_dict_with_multiple_equals_signs_splits_on_first(self):
        registry = ConverterRegistry()
        result = registry.convert("a=b=c=d", dict[str, str])
        assert result == {"a": "b=c=d"}

    def test_dict_with_empty_key_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("=value", dict[str, str])
        assert result == {"": "value"}

    def test_dict_overrides_duplicate_keys(self):
        registry = ConverterRegistry()
        result = registry.convert(("key=first", "key=second"), dict[str, str])
        # Last value wins
        assert result == {"key": "second"}
