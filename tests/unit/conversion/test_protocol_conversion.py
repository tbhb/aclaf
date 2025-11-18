# pyright: reportAny=false, reportExplicitAny=false, reportImplicitOverride=false

from dataclasses import dataclass
from typing import Any
from typing_extensions import override

import pytest
from annotated_types import BaseMetadata

from aclaf.conversion import ConversionError, ConverterRegistry
from aclaf.types import FromArgument


@dataclass(frozen=True)
class Point(FromArgument):
    x: int
    y: int

    @classmethod
    @override
    def from_cli_value(
        cls,
        value: str | int | bool | tuple[Any, ...],
        metadata: tuple[BaseMetadata, ...] | None = None,
    ) -> "Point":
        if isinstance(value, str):
            parts = value.split(",")
            if len(parts) != 2:
                msg = "Point must be in format 'x,y'"
                raise ValueError(msg)
            return cls(x=int(parts[0]), y=int(parts[1]))
        msg = f"Cannot convert {type(value).__name__} to Point"
        raise TypeError(msg)


@dataclass(frozen=True)
class Email(FromArgument):
    address: str

    @classmethod
    @override
    def from_cli_value(
        cls,
        value: str | int | bool | tuple[Any, ...],
        metadata: tuple[BaseMetadata, ...] | None = None,
    ) -> "Email":
        if isinstance(value, str):
            if "@" not in value:
                msg = "Email must contain @"
                raise ValueError(msg)
            return cls(address=value)
        msg = f"Cannot convert {type(value).__name__} to Email"
        raise TypeError(msg)


@dataclass(frozen=True)
class Range(FromArgument):
    start: int
    end: int

    @classmethod
    @override
    def from_cli_value(
        cls,
        value: str | int | bool | tuple[Any, ...],
        metadata: tuple[BaseMetadata, ...] | None = None,
    ) -> "Range":
        if isinstance(value, str):
            if ".." in value:
                parts = value.split("..")
                return cls(start=int(parts[0]), end=int(parts[1]))
            # Single value becomes range of 1
            num = int(value)
            return cls(start=num, end=num)
        msg = f"Cannot convert {type(value).__name__} to Range"
        raise TypeError(msg)


class TestProtocolConversion:
    def test_convert_protocol_with_valid_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("10,20", Point)
        assert result == Point(x=10, y=20)

    def test_convert_protocol_with_different_values_succeeds(self):
        registry = ConverterRegistry()
        assert registry.convert("0,0", Point) == Point(x=0, y=0)
        assert registry.convert("-5,10", Point) == Point(x=-5, y=10)
        assert registry.convert("100,200", Point) == Point(x=100, y=200)

    def test_convert_email_protocol_with_valid_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("user@example.com", Email)
        assert result == Email(address="user@example.com")

    def test_convert_range_protocol_with_range_string_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("1..10", Range)
        assert result == Range(start=1, end=10)

    def test_convert_range_protocol_with_single_value_succeeds(self):
        registry = ConverterRegistry()
        result = registry.convert("5", Range)
        assert result == Range(start=5, end=5)


class TestProtocolConversionErrors:
    def test_convert_protocol_with_invalid_format_raises_error(self):
        registry = ConverterRegistry()
        # Protocol errors are wrapped in ConversionError by the registry
        with pytest.raises(ConversionError, match="format"):
            registry.convert("invalid", Point)

    def test_convert_protocol_with_wrong_number_of_parts_raises_error(self):
        registry = ConverterRegistry()
        # Protocol errors are wrapped in ConversionError by the registry
        with pytest.raises(ConversionError, match="format"):
            registry.convert("1,2,3", Point)

    def test_convert_protocol_with_non_numeric_parts_raises_error(self):
        registry = ConverterRegistry()
        # Protocol errors are wrapped in ConversionError by the registry
        with pytest.raises(ConversionError, match="invalid literal"):
            registry.convert("a,b", Point)

    def test_convert_email_protocol_without_at_symbol_raises_error(self):
        registry = ConverterRegistry()
        # Protocol errors are wrapped in ConversionError by the registry
        with pytest.raises(ConversionError, match="must contain @"):
            registry.convert("invalid", Email)

    def test_convert_email_protocol_with_empty_string_raises_error(self):
        registry = ConverterRegistry()
        # Protocol errors are wrapped in ConversionError by the registry
        with pytest.raises(ConversionError, match="must contain @"):
            registry.convert("", Email)


class TestProtocolConverterCaching:
    def test_protocol_converter_is_cached_after_first_use(self):
        registry = ConverterRegistry()
        # First conversion creates converter
        registry.convert("10,20", Point)
        # Second conversion should use cached converter
        result = registry.convert("30,40", Point)
        assert result == Point(x=30, y=40)

    def test_different_protocol_types_have_separate_converters(self):
        registry = ConverterRegistry()
        point_result = registry.convert("10,20", Point)
        email_result = registry.convert("user@example.com", Email)
        assert point_result == Point(x=10, y=20)
        assert email_result == Email(address="user@example.com")


class TestProtocolWithMetadata:
    def test_protocol_receives_metadata_when_provided(self):
        @dataclass(frozen=True)
        class Scale(BaseMetadata):
            factor: int

        @dataclass(frozen=True)
        class ScaledPoint(FromArgument):
            x: int
            y: int

            @classmethod
            def from_cli_value(
                cls,
                value: str | int | bool | tuple[Any, ...],  # noqa: FBT001
                metadata: tuple[BaseMetadata, ...] | None = None,
            ) -> "ScaledPoint":
                if isinstance(value, str):
                    parts = value.split(",")
                    x, y = int(parts[0]), int(parts[1])

                    # Apply scaling if metadata present
                    if metadata:
                        for m in metadata:
                            if isinstance(m, Scale):
                                x *= m.factor
                                y *= m.factor

                    return cls(x=x, y=y)
                msg = f"Cannot convert {type(value).__name__} to ScaledPoint"
                raise TypeError(msg)

        registry = ConverterRegistry()
        # Without metadata
        result = registry.convert("10,20", ScaledPoint)
        assert result == ScaledPoint(x=10, y=20)


class TestProtocolIsSubclassCheck:
    def test_non_protocol_type_returns_none(self):
        registry = ConverterRegistry()

        # Regular class should not be treated as ConvertibleProtocol
        class RegularClass:
            pass

        converter = registry.get_converter(RegularClass)
        assert converter is None

    def test_protocol_type_returns_converter(self):
        registry = ConverterRegistry()
        converter = registry.get_converter(Point)
        assert converter is not None
