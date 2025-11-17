# pyright: reportAny=false, reportExplicitAny=false

from collections.abc import Callable, Mapping
from functools import lru_cache
from types import MappingProxyType, ModuleType
from typing import Any, Literal
from typing_extensions import get_annotations as _get_annotations
from weakref import WeakKeyDictionary

from typing_inspection.introspection import (
    AnnotationSource,
    InspectedAnnotation,
    inspect_annotation as _inspect_annotation,
)

GetAnnotationsType = Callable[..., Any] | type[Any] | ModuleType

_get_annotations_cache: WeakKeyDictionary[GetAnnotationsType, dict[str, Any]] = (
    WeakKeyDictionary()
)


def get_annotations(
    obj: GetAnnotationsType,
    globals: dict[str, object] | None = None,  # noqa: A002
    locals: Mapping[str, object] | None = None,  # noqa: A002
) -> MappingProxyType[str, Any]:
    if globals is None and locals is None:
        annotations = _get_annotations_cache.get(obj)
        if annotations is not None:
            return MappingProxyType(annotations)

    annotations = _get_annotations(obj, globals=globals, locals=locals, eval_str=True)
    if globals is None and locals is None:
        _get_annotations_cache[obj] = annotations
    return MappingProxyType(annotations)


@lru_cache
def inspect_annotation(
    annotation: Any,
    source: AnnotationSource = AnnotationSource.ANY,
    unpack_type_aliases: Literal["eager", "lenient", "skip"] = "eager",
) -> InspectedAnnotation:
    return _inspect_annotation(
        annotation,
        annotation_source=source,
        unpack_type_aliases=unpack_type_aliases,
    )


def inspect_annotations(
    obj: GetAnnotationsType,
    globals: dict[str, object] | None = None,  # noqa: A002
    *,
    locals: Mapping[str, object] | None = None,  # noqa: A002
    source: AnnotationSource = AnnotationSource.ANY,
    unpack_type_aliases: Literal["eager", "lenient", "skip"] = "eager",
) -> MappingProxyType[str, InspectedAnnotation]:
    annotations = get_annotations(obj, globals=globals, locals=locals)
    return MappingProxyType(
        {
            name: inspect_annotation(
                annotation,
                source=source,
                unpack_type_aliases=unpack_type_aliases,
            )
            for name, annotation in annotations.items()
        }
    )
