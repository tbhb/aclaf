# pyright: reportAny=false, reportExplicitAny=false

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Annotated,
    Any,
    TypeAlias,
    TypeVar,
    cast,
    get_args,
    get_origin,
)

from annotated_types import BaseMetadata
from typing_inspection import typing_objects
from typing_inspection.introspection import AnnotationSource

from aclaf.logging import Logger, NullLogger

from ._internal._inspect import inspect_annotation
from .exceptions import ConversionError
from .parser import ParsedParameterValue
from .types import ConvertibleProtocol

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Non-generic converter function type - accepts ParsedParameterValue and
# optional metadata, returns Any since we can't statically know the return
# type at the registry level
ConverterFunctionType: TypeAlias = Callable[
    [ParsedParameterValue, tuple[BaseMetadata, ...] | None], Any
]


@dataclass(slots=True)
class ConverterRegistry:
    """Registry for type converters that transform parsed CLI values to Python types.

    The registry maintains a mapping from types to converter functions and handles
    lookup logic including protocol-based converters and generic type support.

    Note:
        While the registry operations are type-safe at runtime, static type checking
        cannot fully verify correctness since converter lookup is inherently dynamic.
        The type annotations express intent and provide guidance but cannot eliminate
        all runtime type errors.
    """

    _converters: dict[type[Any], ConverterFunctionType] = field(
        default_factory=dict, init=False, repr=False
    )
    logger: Logger = field(default_factory=NullLogger)

    def __post_init__(self) -> None:
        self._register_builtins()

    def register(
        self,
        type_: type[T],
        converter: Callable[[ParsedParameterValue, tuple[BaseMetadata, ...] | None], T],
    ) -> None:
        """Register a converter function for a specific type.

        Args:
            type_: The target type that this converter produces
            converter: Function that converts ParsedParameterValue to the target type

        Raises:
            ValueError: If a converter for this type is already registered
        """
        if type_ in self._converters:
            msg = f"Converter for type '{type_.__name__}' is already registered."
            raise ValueError(msg)
        # Cast is needed because we store all converters as returning Any,
        # even though this specific converter returns T
        self._converters[type_] = cast("ConverterFunctionType", converter)

    def unregister(self, type_: type[Any]) -> None:
        """Remove a registered converter for a type.

        Args:
            type_: The type whose converter should be removed

        Raises:
            KeyError: If no converter is registered for this type
        """
        del self._converters[type_]

    def get_converter(  # noqa: PLR0911
        self, type_: type[T]
    ) -> Callable[[ParsedParameterValue, tuple[BaseMetadata, ...] | None], T] | None:
        """Retrieve a converter function for the given type.

        This method checks for registered converters, protocol-based converters,
        and generic type converters in that order. Successfully found converters
        are cached in the registry for future lookups.

        Args:
            type_: The target type to find a converter for

        Returns:
            A converter function if one exists, None otherwise

        Note:
            The return type annotation expresses the expected contract but cannot
            be statically verified due to the dynamic nature of the registry.
        """
        # Handle Annotated types specially - extract base type and preserve metadata
        origin = get_origin(type_)
        if origin is Annotated:
            args = get_args(type_)
            if args:
                base_type = args[0]
                metadata_from_type = args[1:]  # Rest is metadata

                base_converter = self.get_converter(base_type)
                if base_converter is None:
                    return None

                # Create wrapper that merges Annotated metadata with passed metadata
                def annotated_converter(
                    value: ParsedParameterValue,
                    extra_metadata: tuple[BaseMetadata, ...] | None = None,
                ) -> T:
                    # Merge Annotated metadata with passed metadata
                    combined_metadata = metadata_from_type + (extra_metadata or ())
                    return cast("T", base_converter(value, combined_metadata))

                return annotated_converter

        if type_ in self._converters:
            # We know this converter should return T, but it's stored as returning Any
            return cast(
                "Callable[[ParsedParameterValue, tuple[BaseMetadata, ...] | None], T]",
                self._converters[type_],
            )

        converter = self._try_enum_converter(type_)
        if converter is not None:
            return converter

        converter = self._try_protocol_converter(type_)
        if converter is not None:
            return converter

        converter = self._try_generic_converter(type_)
        if converter is not None:
            return converter

        return None

    def _try_protocol_converter(
        self, type_: type[T]
    ) -> Callable[[ParsedParameterValue, tuple[BaseMetadata, ...] | None], T] | None:
        """Attempt to create a converter for a type implementing ConvertibleProtocol.

        Args:
            type_: The type to check for protocol implementation

        Returns:
            A converter function if the type implements the protocol, None otherwise
        """
        try:
            # Check if type_ is a subclass of ConvertibleProtocol
            if not issubclass(type_, ConvertibleProtocol):
                return None

            def convert_protocol(
                value: ParsedParameterValue,
                metadata: tuple[BaseMetadata, ...] | None = None,
            ) -> T:
                # Call the protocol method - we know type_ has from_cli_value
                # since we verified it's a ConvertibleProtocol subclass
                result = type_.from_cli_value(value, metadata)
                # The protocol guarantees this returns an instance of type_,
                # which is T in this context
                return cast("T", result)
        except TypeError:
            # issubclass can raise TypeError for some types (e.g., generics)
            return None
        else:
            return convert_protocol

    def _try_generic_converter(
        self, type_: type[T]
    ) -> Callable[[ParsedParameterValue, tuple[BaseMetadata, ...] | None], T] | None:
        """Attempt to create a converter for a generic type.

        Handles Union types, sequence types (list, tuple, set, etc.), and mapping types.

        Args:
            type_: The potentially generic type to create a converter for

        Returns:
            A converter function if the type is a supported generic, None otherwise
        """
        origin = get_origin(type_)
        if origin is None:
            return None

        args = get_args(type_)
        unwrapped_args: list[Any] = []
        for arg in args:
            # Try to unwrap ALL args using inspect_annotation, not just TypeAliasType
            # This handles both PEP 613 (TypeAlias) and PEP 695 (type X = Y) aliases
            try:
                ann = inspect_annotation(
                    arg,
                    annotation_source=AnnotationSource.BARE,
                    unpack_type_aliases="eager",
                )
                # Use the unwrapped type
                unwrapped_args.append(ann.type)
            except Exception:  # noqa: BLE001, PERF203
                # Catch broad exceptions: inspect_annotation can raise various types
                # depending on the input type. Performance impact is negligible since
                # loops are short and exceptions rare in normal usage.
                # If inspection fails, use arg as-is
                unwrapped_args.append(arg)
        return self._make_generic_converter(origin, tuple(unwrapped_args))

    def _try_enum_converter(
        self, type_: type[T]
    ) -> Callable[[ParsedParameterValue, tuple[BaseMetadata, ...] | None], T] | None:
        try:
            if not issubclass(type_, Enum):
                return None
        except TypeError:
            return None

        def convert_enum(
            value: ParsedParameterValue,
            _metadata: tuple[BaseMetadata, ...] | None = None,
        ) -> T:
            if isinstance(value, type_):  # Already the enum type
                return value

            if not isinstance(value, str):
                raise ConversionError(
                    value,
                    type_,
                    f"Cannot convert {type(value).__name__} to {type_.__name__}",
                )

            # Try by value first
            for member in type_:
                if member.value == value:
                    return member

            # Try by name (case-insensitive)
            value_upper = value.upper()
            for member in type_:
                if member.name.upper() == value_upper:
                    return member

            # Build helpful error message
            valid_values = [m.value for m in type_]
            raise ConversionError(
                value,
                type_,
                f"Invalid value. Valid values: {', '.join(map(str, valid_values))}",
            )

        return convert_enum

    def has_converter(self, type_: type[Any]) -> bool:
        """Check if a converter exists for the given type.

        Args:
            type_: The type to check

        Returns:
            True if a converter exists or can be created, False otherwise
        """
        return self.get_converter(type_) is not None

    def convert(
        self,
        value: ParsedParameterValue,
        target_type: type[T],
        metadata: tuple[BaseMetadata, ...] | None = None,
    ) -> T:
        """Convert a parsed parameter value to the target type.

        Args:
            value: The parsed value to convert
            target_type: The type to convert to
            metadata: Optional metadata from Annotated types

        Returns:
            The converted value of the target type

        Raises:
            TypeError: If no converter is registered for the target type
            ConversionError: If conversion fails
        """
        converter = self.get_converter(target_type)
        if converter is None:
            msg = f"No converter registered for type '{target_type.__name__}'."
            raise TypeError(msg)

        try:
            return converter(value, metadata)
        except ConversionError:
            raise
        except (ValueError, TypeError) as e:
            raise ConversionError(value, target_type, str(e)) from e

    def _make_generic_converter(  # noqa: PLR0911
        self,
        origin: type[Any],
        args: tuple[type[Any], ...],
    ) -> ConverterFunctionType | None:
        """Create a converter for a generic type based on its origin and arguments.

        Args:
            origin: The origin type (e.g., list for list[int])
            args: Type arguments (e.g., (int,) for list[int])

        Returns:
            A converter function if the generic type is supported, None otherwise
        """
        if typing_objects.is_union(origin):
            return self._make_union_converter(args)

        # Handle sequence types
        if origin in (list, tuple, set, frozenset, Iterable, Sequence):
            element_type: type[Any] = str if not args else args[0]

            element_converter = self.get_converter(element_type)
            if element_converter is None:
                return None

            return self._make_sequence_converter(origin, element_converter)

        # Handle mapping types
        if origin in (dict, Mapping):
            # Mappings require exactly 2 type arguments (key type and value type)
            if len(args) != 2:  # noqa: PLR2004
                return None

            key_type, value_type = args
            key_converter = self.get_converter(key_type)
            value_converter = self.get_converter(value_type)

            if key_converter is None or value_converter is None:
                return None

            return self._make_mapping_converter(key_converter, value_converter)

        return None

    def _make_union_converter(
        self, args: tuple[type[Any], ...]
    ) -> Callable[[ParsedParameterValue, tuple[BaseMetadata, ...] | None], Any]:
        """Create a converter that tries each union member type in order.

        Args:
            args: The union member types

        Returns:
            A converter function that attempts conversion to each member type
        """

        def convert_union(
            value: ParsedParameterValue | None,
            metadata: tuple[BaseMetadata, ...] | None = None,
        ) -> Any:
            errors: list[Exception] = []

            if value is None and type(None) in args:
                return None

            # Try to convert to each non-None member type
            # At this point, value is guaranteed to be ParsedParameterValue (not None)
            # because we handle the None case above
            for member_type in args:
                if member_type is type(None):
                    continue

                converter = self.get_converter(member_type)
                if converter is None:
                    continue

                try:
                    # Type assertion: value is not None (checked at line 376-377)
                    assert value is not None  # noqa: S101
                    return converter(value, metadata)
                except (ConversionError, ValueError, TypeError) as e:
                    errors.append(e)

            # If we get here, conversion to all types failed
            type_names = [t.__name__ for t in args if t is not type(None)]
            # Type assertion: value is not None (checked at line 376-377)
            assert value is not None  # noqa: S101
            # Use object as target_type (no specific type for union failures)
            raise ConversionError(
                value,
                target_type=object,
                reason=(
                    f"Could not convert to any of the union types: "
                    f"{', '.join(type_names)}"
                ),
            )

        return convert_union

    def _make_sequence_converter(
        self, origin: type[Any], element_converter: ConverterFunctionType
    ) -> ConverterFunctionType:
        """Create a converter for sequence types.

        Args:
            origin: The sequence type (list, tuple, set, etc.)
            element_converter: Converter for individual elements

        Returns:
            A converter that produces the appropriate sequence type
        """

        def convert_sequence(  # noqa: PLR0911
            value: ParsedParameterValue,
            metadata: tuple[BaseMetadata, ...] | None = None,
        ) -> Any:
            # Handle already-converted sequences
            if isinstance(value, (list, tuple)):
                converted_elements = [
                    element_converter(elem, metadata) for elem in value
                ]
                # Convert to target collection type
                if origin in (list, Sequence):
                    return converted_elements
                if origin in (tuple,):
                    return tuple(converted_elements)
                if origin in (set, frozenset):
                    # Type ignore: Partially unknown return type due to dynamic type
                    # selection - origin is either set or frozenset, both valid
                    return origin(converted_elements)  # pyright: ignore[reportUnknownVariableType]
                return converted_elements

            # Handle single string value (split or wrap?)
            if isinstance(value, str):
                # Option 1: Wrap in list
                converted = element_converter(value, metadata)
                if origin in (tuple,):
                    return (converted,)
                if origin in (set, frozenset):
                    # Type ignore: Partially unknown return type due to dynamic type
                    # selection - origin is either set or frozenset, both valid
                    return origin([converted])  # pyright: ignore[reportUnknownVariableType]
                return [converted]

            raise ConversionError(
                value, origin, f"Cannot convert {type(value).__name__} to sequence"
            )

        return convert_sequence

    def _make_mapping_converter(
        self,
        key_converter: ConverterFunctionType,
        value_converter: ConverterFunctionType,
    ) -> ConverterFunctionType:
        """Create a converter for mapping types.

        Args:
            key_converter: Converter for mapping keys
            value_converter: Converter for mapping values

        Returns:
            A converter that produces a dict
        """

        def convert_mapping(
            value: ParsedParameterValue,
            metadata: tuple[BaseMetadata, ...] | None = None,
        ) -> dict[Any, Any]:
            # Expect value to be a sequence of "key=value" strings
            if isinstance(value, str):
                # Single "key=value" string
                if "=" not in value:
                    raise ConversionError(
                        value, dict, "Mapping values must be in 'key=value' format"
                    )
                key_str, value_str = value.split("=", 1)
                key = key_converter(key_str, metadata)
                val = value_converter(value_str, metadata)
                return {key: val}

            if isinstance(value, tuple):
                # Multiple "key=value" strings
                result: dict[Any, Any] = {}
                for item in value:
                    if not isinstance(item, str):
                        raise ConversionError(
                            value, dict, f"Expected string, got {type(item).__name__}"
                        )
                    if "=" not in item:
                        raise ConversionError(
                            value, dict, "Mapping values must be in 'key=value' format"
                        )
                    key_str, value_str = item.split("=", 1)
                    key = key_converter(key_str, metadata)
                    val = value_converter(value_str, metadata)
                    result[key] = val
                return result

            raise ConversionError(
                value, dict, f"Cannot convert {type(value).__name__} to mapping"
            )

        return convert_mapping

    def _register_builtins(self) -> None:
        """Register converters for built-in Python types."""
        self.register(str, convert_str)
        self.register(int, convert_int)
        self.register(float, convert_float)
        self.register(bool, convert_bool)
        self.register(Path, convert_path)


def convert_str(
    value: ParsedParameterValue, _metadata: tuple[BaseMetadata, ...] | None = None
) -> str:
    """Convert a parsed value to string.

    Args:
        value: The value to convert
        _metadata: Unused metadata parameter

    Returns:
        The value as a string
    """
    if isinstance(value, str):
        return value
    return str(value)


def convert_int(
    value: ParsedParameterValue, _metadata: tuple[BaseMetadata, ...] | None = None
) -> int:
    """Convert a parsed value to integer.

    Args:
        value: The value to convert
        _metadata: Unused metadata parameter

    Returns:
        The value as an integer

    Raises:
        ValueError: If the value cannot be converted to int
    """
    if isinstance(value, int):
        return value
    # Type ignore: ParsedParameterValue includes tuples, but converter registry
    # ensures this is only called for convertible values (str, bool, int)
    return int(value)  # pyright: ignore[reportArgumentType]


def convert_float(
    value: ParsedParameterValue, _metadata: tuple[BaseMetadata, ...] | None = None
) -> float:
    """Convert a parsed value to float.

    Args:
        value: The value to convert
        _metadata: Unused metadata parameter

    Returns:
        The value as a float

    Raises:
        ValueError: If the value cannot be converted to float
    """
    if isinstance(value, float):
        return value
    # Type ignore: ParsedParameterValue includes tuples, but converter registry
    # ensures this is only called for convertible values (str, bool, int, float)
    return float(value)  # pyright: ignore[reportArgumentType]


def convert_bool(
    value: ParsedParameterValue, _metadata: tuple[BaseMetadata, ...] | None = None
) -> bool:
    """Convert a parsed value to boolean.

    Recognizes common boolean string representations:
    - True: 'true', '1', 'yes', 'on' (case-insensitive)
    - False: 'false', '0', 'no', 'off' (case-insensitive)

    Args:
        value: The value to convert
        _metadata: Unused metadata parameter

    Returns:
        The value as a boolean

    Raises:
        ValueError: If the value cannot be recognized as a boolean
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)  # 0 → False, non-zero → True
    if isinstance(value, str):
        val_lower = value.lower()
        if val_lower in ("true", "1", "yes", "on"):
            return True
        if val_lower in ("false", "0", "no", "off"):
            return False
    msg = f"Cannot convert '{value}' to bool."
    raise ValueError(msg)


def convert_path(
    value: ParsedParameterValue,
    _metadata: tuple[BaseMetadata, ...] | None = None,
) -> Path:
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise ConversionError(value, Path, f"Cannot convert {type(value).__name__} to Path")
