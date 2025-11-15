from typing import TYPE_CHECKING, cast

from annotated_types import GroupedMetadata

if TYPE_CHECKING:
    from collections.abc import Sequence

    from aclaf.metadata import MetadataType


def flatten_metadata(metadata: "Sequence[MetadataType]") -> list["MetadataType"]:
    flattened: list[MetadataType] = []
    for meta in metadata:
        if isinstance(meta, GroupedMetadata):
            grouped_items = cast("Sequence[MetadataType]", list(meta))
            flattened.extend(flatten_metadata(grouped_items))
        else:
            flattened.append(meta)
    return flattened
