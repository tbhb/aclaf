from typing_extensions import get_annotations

from typing_inspection.introspection import (
    AnnotationSource,
    InspectedAnnotation,
    inspect_annotation,
)


def inspect_annotations(obj: object) -> dict[str, InspectedAnnotation]:
    return {
        name: inspect_annotation(
            annotation,
            annotation_source=AnnotationSource.ANY,
            unpack_type_aliases="eager",
        )
        for name, annotation in get_annotations(obj, eval_str=True).items()  # pyright: ignore[reportAny]
    }
