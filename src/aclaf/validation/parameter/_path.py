from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from aclaf.metadata import ParameterMetadata

if TYPE_CHECKING:
    from collections.abc import Iterable

    from aclaf.types import ParameterValueMappingType, ParameterValueType
    from aclaf.validators._registry import ValidatorMetadataType


@dataclass(slots=True, frozen=True)
class PathExists(ParameterMetadata):
    pass


def validate_path_exists(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("PathExists", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class IsFile(ParameterMetadata):
    pass


def validate_is_file(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("IsFile", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class IsDirectory(ParameterMetadata):
    pass


def validate_is_directory(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("IsDirectory", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class IsReadable(ParameterMetadata):
    pass


def validate_is_readable(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("IsReadable", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class IsWritable(ParameterMetadata):
    pass


def validate_is_writable(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("IsWritable", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class IsExecutable(ParameterMetadata):
    pass


def validate_is_executable(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("IsExecutable", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None


@dataclass(slots=True, frozen=True)
class HasExtensions(ParameterMetadata):
    extensions: "str | Iterable[str]"


def validate_has_extensions(
    value: "ParameterValueType | ParameterValueMappingType | None",
    metadata: "ValidatorMetadataType",
) -> tuple[str, ...] | None:
    metadata = cast("HasExtensions", metadata)
    errors: list[str] = []
    if errors:
        return tuple(errors)
    return None
