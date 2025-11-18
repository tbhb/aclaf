# pyright: reportAny=false, reportExplicitAny=false

from enum import Enum

import pytest

from aclaf.conversion import ConversionError, ConverterRegistry


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Status(Enum):
    PENDING = 1
    APPROVED = 2
    REJECTED = 3


class MixedEnum(Enum):
    FIRST = "first"
    SECOND = 2
    THIRD = 3.0


class TestEnumConversionByValue:
    def test_convert_enum_with_exact_string_value_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("red", Color)
        assert result == Color.RED

    def test_convert_enum_with_all_values_succeeds(self):
        registry = ConverterRegistry()
        assert registry.convert("red", Color) == Color.RED
        assert registry.convert("green", Color) == Color.GREEN
        assert registry.convert("blue", Color) == Color.BLUE

    def test_convert_enum_with_numeric_value_as_string_succeeds(self):
        registry = ConverterRegistry()
        # String "1" won't match int value 1, but will match by name
        result = registry.convert("PENDING", Status)
        assert result == Status.PENDING

    def test_convert_enum_with_all_names_succeeds(self):
        registry = ConverterRegistry()
        assert registry.convert("PENDING", Status) == Status.PENDING
        assert registry.convert("APPROVED", Status) == Status.APPROVED
        assert registry.convert("REJECTED", Status) == Status.REJECTED


class TestEnumConversionByName:
    def test_convert_enum_with_exact_name_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("RED", Color)
        assert result == Color.RED

    def test_convert_enum_with_lowercase_name_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("red", Color)
        # Should match value first, but if no value match, tries name
        assert result == Color.RED

    def test_convert_enum_with_mixed_case_name_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("Red", Color)
        # Case-insensitive name matching
        assert result == Color.RED

    def test_convert_enum_with_uppercase_name_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("GREEN", Color)
        assert result == Color.GREEN

    def test_convert_enum_with_all_names_case_insensitive_succeeds(self):
        registry = ConverterRegistry()
        assert registry.convert("PENDING", Status) == Status.PENDING
        assert registry.convert("pending", Status) == Status.PENDING
        assert registry.convert("Pending", Status) == Status.PENDING


class TestEnumConversionPriority:
    def test_convert_enum_tries_value_before_name(self):
        # If value and name could both match, value takes priority
        class Priority(Enum):
            RED = "RED"
            BLUE = "blue"

        registry = ConverterRegistry()
        result = registry.convert("RED", Priority)
        # Should match by value first
        assert result == Priority.RED


class TestEnumConversionErrors:
    def test_convert_enum_with_invalid_value_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match="Invalid value"):
            _ = registry.convert("yellow", Color)

    def test_convert_enum_with_invalid_name_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match="Invalid value"):
            _ = registry.convert("YELLOW", Color)

    def test_convert_enum_with_empty_string_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match="Invalid value"):
            _ = registry.convert("", Color)

    def test_convert_enum_with_int_raises_conversion_error(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match="Cannot convert int"):
            _ = registry.convert(1, Color)

    def test_convert_enum_with_bool_raises_conversion_error(self):
        registry = ConverterRegistry()
        bool_val = True
        with pytest.raises(ConversionError, match="Cannot convert bool"):
            _ = registry.convert(bool_val, Color)

    def test_convert_enum_error_message_includes_valid_values(self):
        registry = ConverterRegistry()
        with pytest.raises(ConversionError, match="red, green, blue"):
            _ = registry.convert("invalid", Color)


class TestEnumConversionWithMixedTypes:
    def test_convert_mixed_enum_with_string_value_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("first", MixedEnum)
        assert result == MixedEnum.FIRST

    def test_convert_mixed_enum_by_name_succeeds(self):
        registry = ConverterRegistry()
        # Use names instead of values for numeric enums
        result = registry.convert("SECOND", MixedEnum)
        assert result == MixedEnum.SECOND

    def test_convert_mixed_enum_third_by_name_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("THIRD", MixedEnum)
        assert result == MixedEnum.THIRD

    def test_convert_mixed_enum_with_name_succeeds(self):
        registry = ConverterRegistry()
        assert registry.convert("FIRST", MixedEnum) == MixedEnum.FIRST
        assert registry.convert("SECOND", MixedEnum) == MixedEnum.SECOND
        assert registry.convert("THIRD", MixedEnum) == MixedEnum.THIRD


class TestEnumWithSpecialCharacters:
    def test_convert_enum_with_dash_in_value(self):
        class Environment(Enum):
            DEV = "dev-environment"
            PROD = "prod-environment"
            STAGING = "staging-environment"

        registry = ConverterRegistry()
        result = registry.convert("dev-environment", Environment)
        assert result == Environment.DEV

    def test_convert_enum_with_underscore_in_name(self):
        class LogLevel(Enum):
            LOG_DEBUG = "debug"
            LOG_INFO = "info"
            LOG_ERROR = "error"

        registry = ConverterRegistry()
        result = registry.convert("LOG_DEBUG", LogLevel)
        assert result == LogLevel.LOG_DEBUG
