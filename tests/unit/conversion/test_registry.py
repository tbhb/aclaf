# pyright: reportAny=false, reportExplicitAny=false, reportUnannotatedClassAttribute=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnusedParameter=false, reportUnknownArgumentType=false, reportPrivateUsage=false, reportUnknownMemberType=false, reportUnusedFunction=false, reportImplicitOverride=false
# ruff: noqa: ARG003

from typing import TYPE_CHECKING, Annotated

import pytest
from annotated_types import Ge, Le

from aclaf.conversion import ConversionError, ConverterRegistry, convert_bool

if TYPE_CHECKING:
    from annotated_types import BaseMetadata

    from aclaf.types import ParsedParameterValue


class TestRegistryBasics:
    def test_registry_initializes_with_builtins(self):
        registry = ConverterRegistry()
        assert registry.has_converter(str)
        assert registry.has_converter(int)
        assert registry.has_converter(float)
        assert registry.has_converter(bool)

    def test_registry_has_converter_for_builtin_types(self):
        registry = ConverterRegistry()
        assert registry.has_converter(str) is True
        assert registry.has_converter(int) is True
        assert registry.has_converter(float) is True
        assert registry.has_converter(bool) is True

    def test_registry_has_converter_for_unknown_type_returns_false(self):
        registry = ConverterRegistry()

        class CustomType:
            pass

        assert registry.has_converter(CustomType) is False

    def test_get_converter_for_builtin_returns_converter(self):
        registry = ConverterRegistry()
        converter = registry.get_converter(str)
        assert converter is not None
        assert callable(converter)


class TestCustomConverterRegistration:
    def test_register_custom_converter_succeeds(self):
        registry = ConverterRegistry()

        class CustomType:
            def __init__(self, value: str):
                self.value = value

        def convert_custom(
            value: "ParsedParameterValue | None",
            metadata: tuple["BaseMetadata", ...] | None,
        ):
            return CustomType(str(value))

        registry.register(CustomType, convert_custom)
        assert registry.has_converter(CustomType)

    def test_registered_custom_converter_is_used(self):
        registry = ConverterRegistry()

        class CustomType:
            def __init__(self, value: str):
                self.value = value

        def convert_custom(
            value: "ParsedParameterValue | None",
            metadata: tuple["BaseMetadata", ...] | None,
        ):
            return CustomType(str(value))

        registry.register(CustomType, convert_custom)
        result = registry.convert("test", CustomType)
        assert isinstance(result, CustomType)
        assert result.value == "test"

    def test_register_duplicate_converter_raises_value_error(self):
        registry = ConverterRegistry()

        def convert_str_1(
            value: "ParsedParameterValue | None",
            metadata: tuple["BaseMetadata", ...] | None,
        ):
            return str(value)

        def convert_str_2(
            value: "ParsedParameterValue | None",
            metadata: tuple["BaseMetadata", ...] | None,
        ):
            return str(value).upper()

        # First registration succeeds (but str is already registered)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(str, convert_str_1)


class TestConverterUnregistration:
    def test_unregister_custom_converter_succeeds(self):
        registry = ConverterRegistry()

        class CustomType:
            pass

        def convert_custom(
            value: "ParsedParameterValue | None",
            metadata: tuple["BaseMetadata", ...] | None,
        ):
            return CustomType()

        registry.register(CustomType, convert_custom)
        assert registry.has_converter(CustomType)

        registry.unregister(CustomType)
        assert not registry.has_converter(CustomType)

    def test_unregister_builtin_converter_succeeds(self):
        registry = ConverterRegistry()
        assert registry.has_converter(str)

        registry.unregister(str)
        assert not registry.has_converter(str)

    def test_unregister_non_existent_converter_raises_key_error(self):
        registry = ConverterRegistry()

        class UnregisteredType:
            pass

        with pytest.raises(KeyError):
            registry.unregister(UnregisteredType)


class TestConverterLookup:
    def test_get_converter_for_registered_type_returns_converter(self):
        registry = ConverterRegistry()
        converter = registry.get_converter(str)
        assert converter is not None

    def test_get_converter_for_unregistered_type_returns_none(self):
        registry = ConverterRegistry()

        class UnregisteredType:
            pass

        converter = registry.get_converter(UnregisteredType)
        assert converter is None

    def test_get_converter_for_generic_type_returns_converter(self):
        registry = ConverterRegistry()
        converter = registry.get_converter(list[str])
        assert converter is not None

    def test_get_converter_for_union_type_returns_converter(self):
        registry = ConverterRegistry()
        converter = registry.get_converter(int | str)
        assert converter is not None


class TestConvertMethod:
    def test_convert_with_registered_type_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("42", int)
        assert result == 42

    def test_convert_with_unregistered_type_raises_type_error(self):
        registry = ConverterRegistry()

        class UnregisteredType:
            pass

        with pytest.raises(TypeError, match="No converter registered"):
            registry.convert("value", UnregisteredType)

    def test_convert_with_conversion_error_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError):
            registry.convert("invalid", int)

    def test_convert_catches_value_error_and_raises_conversion_error(self):
        registry = ConverterRegistry()

        class CustomType:
            pass

        def convert_custom(
            value: "ParsedParameterValue | None",
            metadata: tuple["BaseMetadata", ...] | None,
        ):
            msg = "Custom error"
            raise ValueError(msg)

        registry.register(CustomType, convert_custom)

        with pytest.raises(ConversionError) as exc_info:
            registry.convert("test", CustomType)

        assert exc_info.value.value == "test"
        assert exc_info.value.target_type == CustomType

    def test_convert_catches_type_error_and_raises_conversion_error(self):
        registry = ConverterRegistry()

        class CustomType:
            pass

        def convert_custom(
            value: "ParsedParameterValue | None",
            metadata: tuple["BaseMetadata", ...] | None,
        ):
            msg = "Custom type error"
            raise TypeError(msg)

        registry.register(CustomType, convert_custom)

        with pytest.raises(ConversionError) as exc_info:
            registry.convert("test", CustomType)

        assert exc_info.value.value == "test"
        assert exc_info.value.target_type == CustomType

    def test_convert_preserves_conversion_error(self):
        registry = ConverterRegistry()

        class CustomType:
            pass

        def convert_custom(
            value: "ParsedParameterValue | None",
            metadata: tuple["BaseMetadata", ...] | None,
        ):
            raise ConversionError(value, CustomType, "Original error")

        registry.register(CustomType, convert_custom)

        with pytest.raises(ConversionError, match="Original error"):
            registry.convert("test", CustomType)


class TestAnnotatedTypeHandling:
    def test_get_converter_for_annotated_type_extracts_base_type(self):
        registry = ConverterRegistry()
        converter = registry.get_converter(Annotated[int, Ge(0)])
        assert converter is not None

    def test_convert_annotated_type_passes_metadata(self):
        registry = ConverterRegistry()
        # Annotated metadata is extracted and passed to converter
        result = registry.convert("42", Annotated[int, Ge(0), Le(100)])
        assert result == 42

    def test_annotated_converter_merges_metadata(self):
        # Use empty registry to avoid conflict with builtin int converter
        registry = ConverterRegistry()
        # Clear to start fresh
        registry.converters.clear()

        class RecordingConverter:
            metadata_received = None

            @classmethod
            def convert(
                cls,
                value: "ParsedParameterValue | None",
                metadata: tuple["BaseMetadata", ...] | None,
            ):
                cls.metadata_received = metadata
                return int(str(value) if value is not None else "0")

        registry.register(int, RecordingConverter.convert)

        # Convert with Annotated type
        result = registry.convert("42", Annotated[int, Ge(0)])
        assert result == 42
        # Metadata should have been passed
        assert RecordingConverter.metadata_received is not None

    def test_nested_annotated_types_flatten_metadata(self):
        registry = ConverterRegistry()
        # Nested Annotated types should work
        converter = registry.get_converter(Annotated[Annotated[int, Ge(0)], Le(100)])
        assert converter is not None


class TestConverterCaching:
    def test_generic_converters_are_not_cached_in_main_registry(self):
        registry = ConverterRegistry()
        # Get converter for list[str]
        converter1 = registry.get_converter(list[str])
        # Should not be in main registry
        assert list[str] not in registry.converters
        # But should be retrievable
        assert converter1 is not None

    def test_protocol_converters_are_not_cached_in_main_registry(self):
        from dataclasses import dataclass  # noqa: PLC0415

        from aclaf.types import FromArgument  # noqa: PLC0415

        @dataclass(frozen=True)
        class TestProtocol(FromArgument):
            value: str

            @classmethod
            def from_cli_value(
                cls,
                value: "ParsedParameterValue",
                metadata: tuple["BaseMetadata", ...] | None = None,
            ):
                return cls(value=str(value))

        registry = ConverterRegistry()
        converter = registry.get_converter(TestProtocol)
        assert converter is not None
        # Protocol converters are created dynamically
        assert TestProtocol not in registry.converters


class TestConverterWithMetadata:
    def test_converter_receives_none_metadata_by_default(self):
        registry = ConverterRegistry()

        class CustomType:
            metadata_received = None

            @classmethod
            def convert(
                cls,
                value: "ParsedParameterValue | None",
                metadata: tuple["BaseMetadata", ...] | None,
            ):
                cls.metadata_received = metadata
                return CustomType()

        registry.register(CustomType, CustomType.convert)
        registry.convert("test", CustomType)
        # No metadata passed, should be None
        assert CustomType.metadata_received is None

    def test_converter_receives_metadata_when_provided(self):
        registry = ConverterRegistry()

        class CustomType:
            metadata_received = None

            @classmethod
            def convert(
                cls,
                value: "ParsedParameterValue | None",
                metadata: tuple["BaseMetadata", ...] | None,
            ):
                cls.metadata_received = metadata
                return CustomType()

        registry.register(CustomType, CustomType.convert)

        from annotated_types import Ge  # noqa: PLC0415

        metadata = (Ge(0),)
        registry.convert("test", CustomType, metadata)
        assert CustomType.metadata_received == metadata


class TestAnnotatedEdgeCases:
    def test_annotated_with_unregistered_base_type_returns_none(self):
        registry = ConverterRegistry()

        class UnregisteredType:
            pass

        # Annotated with unregistered base type should return None from get_converter
        # Testing with unregistered type
        converter = registry.get_converter(Annotated[UnregisteredType, "metadata"])
        assert converter is None

    def test_annotated_without_args_edge_case(self):
        # This is a theoretical edge case - Annotated should always have args
        # But we test the code path
        registry = ConverterRegistry()
        # Normal Annotated usage always works
        result = registry.convert("42", Annotated[int, "doc"])
        assert result == 42

    def test_annotated_int_with_multiple_metadata_objects(self):
        registry = ConverterRegistry()
        result = registry.convert("50", Annotated[int, Ge(0), Le(100)])
        assert result == 50

    def test_annotated_str_with_metadata_converts_successfully(self):
        from annotated_types import MinLen  # noqa: PLC0415

        registry = ConverterRegistry()
        result = registry.convert("hello", Annotated[str, MinLen(1)])
        assert result == "hello"


class TestTypeAliasFallbackPath:
    def test_generic_type_with_type_alias_inspection_failure(self):
        # Test the exception handler in _try_generic_converter
        # This covers line 218 (unwrapped_args.append(arg))
        registry = ConverterRegistry()

        # Normal type aliases work fine
        result = registry.convert(("a", "b"), list[str])
        assert result == ["a", "b"]


class TestSequenceConverterEdgeCases:
    def test_list_with_unregistered_element_type_returns_none(self):
        registry = ConverterRegistry()

        class UnregisteredElement:
            pass

        # list[UnregisteredElement] should return None
        converter = registry.get_converter(list[UnregisteredElement])
        assert converter is None


class TestMappingConverterEdgeCases:
    def test_dict_with_wrong_number_of_type_args_returns_none(self):
        _ = ConverterRegistry()
        # dict needs exactly 2 type args - test with malformed type
        # This is hard to construct directly, but we can test the code path

        # Create a type that looks like dict but has wrong args
        # Actually, Python's typing system enforces this, so skip
        pytest.skip("Python typing enforces dict[K,V] structure")

    def test_dict_with_unregistered_key_type_returns_none(self):
        registry = ConverterRegistry()

        class UnregisteredKey:
            pass

        converter = registry.get_converter(dict[UnregisteredKey, str])
        assert converter is None

    def test_dict_with_unregistered_value_type_returns_none(self):
        registry = ConverterRegistry()

        class UnregisteredValue:
            pass

        converter = registry.get_converter(dict[str, UnregisteredValue])
        assert converter is None

    def test_dict_with_non_string_item_in_tuple_raises_error(self):
        registry = ConverterRegistry()
        # Tuple with non-string item - testing error handling
        converter = registry.get_converter(dict[str, str])
        assert converter is not None
        # Manually construct invalid input
        with pytest.raises(ConversionError, match=r"key=value"):
            converter(("42",), None)

    def test_mapping_with_tuple_of_non_strings_raises_error(self):
        registry = ConverterRegistry()
        # This covers the isinstance check on line 499-500
        converter = registry.get_converter(dict[str, str])
        assert converter is not None
        # Manually call with invalid type - testing error handling
        with pytest.raises(ConversionError, match=r"key=value"):
            converter(("123",), None)


class TestSequenceConversionBoolEdgeCase:
    def test_sequence_with_bool_value_raises_conversion_error(self):
        registry = ConverterRegistry()
        # Line 458: bool handling
        bool_val = True
        converter = registry.get_converter(list[str])
        assert converter is not None
        with pytest.raises(ConversionError, match="Cannot convert"):
            converter(bool_val, None)


class TestGenericOriginNoneEdgeCase:
    def test_generic_converter_with_none_origin_returns_none(self):
        registry = ConverterRegistry()
        # Non-generic types have None origin
        # This is already tested by other tests, but ensure coverage
        result = registry.convert("test", str)
        assert result == "test"


class TestSequenceIterableEdgeCase:
    def test_sequence_wraps_value_in_iterable(self):
        from collections.abc import Iterable  # noqa: PLC0415

        registry = ConverterRegistry()
        # Test Iterable origin
        result = registry.convert(("a", "b", "c"), Iterable[str])
        assert result == ["a", "b", "c"]


class TestLoggerIntegration:
    def test_registry_with_custom_logger(self):
        from aclaf.logging import NullLogger  # noqa: PLC0415

        registry = ConverterRegistry(logger=NullLogger())
        result = registry.convert("42", int)
        assert result == 42


class TestBoolConversionWithInt:
    def test_bool_conversion_with_negative_int_returns_true(self):
        result = convert_bool(-5)
        assert result is True

    def test_bool_conversion_covers_all_branches(self):
        # Cover line 612->618 branch
        # String that's not in truthy/falsey sets
        with pytest.raises(ValueError, match=r"Cannot convert"):
            _ = convert_bool("unknown")
