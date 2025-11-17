from typing import TYPE_CHECKING, TypeVar, cast
from typing_extensions import TypeIs  # noqa: TC003

from annotated_types import BaseMetadata, GroupedMetadata

if TYPE_CHECKING:
    from collections.abc import Sequence

    from aclaf.metadata import MetadataType


M = TypeVar("M", bound=BaseMetadata)


def flatten_metadata(metadata: "Sequence[MetadataType]") -> list["MetadataType"]:
    """Recursively flatten GroupedMetadata into a flat list.

    Args:
        metadata: Sequence of metadata that may include GroupedMetadata instances.

    Returns:
        Flattened list with all GroupedMetadata recursively expanded.

    Example:
        >>> from annotated_types import GroupedMetadata, Gt, Le
        >>> flatten_metadata([GroupedMetadata(Gt(0), Le(100)), "count"])
        [Gt(gt=0), Le(le=100), "count"]
    """
    flattened: list[MetadataType] = []
    for meta in metadata:
        if isinstance(meta, GroupedMetadata):
            grouped_items = cast("Sequence[MetadataType]", list(meta))
            flattened.extend(flatten_metadata(grouped_items))
        else:
            flattened.append(meta)
    return flattened


def get_metadata(
    metadata: tuple[BaseMetadata, ...],
    meta_type: type[M],
) -> M | None:
    """Get the LAST instance of the specified metadata type, or None.

    Uses last-wins semantics consistent with metadata_by_type property.

    Args:
        metadata: Tuple of metadata instances to search.
        meta_type: The metadata type to find.

    Returns:
        The last instance of meta_type, or None if not found.

    Example:
        >>> from annotated_types import Gt, Le
        >>> meta = (Gt(0), Le(100), Gt(10))
        >>> get_metadata(meta, Gt)
        Gt(gt=10)
        >>> get_metadata(meta, MinLen)
        None
    """
    result: M | None = None
    for m in metadata:
        if isinstance(m, meta_type):
            result = m  # Keep last instance
    return result


def get_all_metadata(
    metadata: tuple[BaseMetadata, ...],
    meta_type: type[M],
) -> tuple[M, ...]:
    """Get ALL instances of the specified metadata type in extraction order.

    Args:
        metadata: Tuple of metadata instances to search.
        meta_type: The metadata type to find.

    Returns:
        Tuple of all instances of meta_type (may be empty).

    Example:
        >>> from annotated_types import Gt, Le
        >>> meta = (Gt(0), Le(100), Gt(10))
        >>> get_all_metadata(meta, Gt)
        (Gt(gt=0), Gt(gt=10))
        >>> get_all_metadata(meta, MinLen)
        ()
    """
    return tuple(m for m in metadata if isinstance(m, meta_type))


def has_metadata(
    metadata: tuple[BaseMetadata, ...],
    meta_type: type[BaseMetadata],
) -> TypeIs[tuple[BaseMetadata, ...]]:
    """Check if metadata contains at least one instance of the specified type.

    Uses TypeIs for type narrowing in conditional branches.

    Args:
        metadata: Tuple of metadata instances to search.
        meta_type: The metadata type to check for.

    Returns:
        True if at least one instance exists, False otherwise.

    Example:
        >>> from annotated_types import Gt, Le
        >>> meta = (Gt(0), Le(100))
        >>> if has_metadata(meta, Gt):
        ...     gt_meta = get_metadata(meta, Gt)
        ...     assert gt_meta is not None
    """
    return any(isinstance(m, meta_type) for m in metadata)
