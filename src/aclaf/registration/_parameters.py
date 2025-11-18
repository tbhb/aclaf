import inspect
from dataclasses import dataclass, field
from inspect import Parameter as FunctionParameter
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    TypedDict,
    Union,
    Unpack,
    get_args,
    get_origin,
    get_type_hints,
)
from typing_extensions import override

from annotated_types import BaseMetadata
from typing_inspection import typing_objects
from typing_inspection.introspection import (
    UNKNOWN,
    AnnotationSource,
    InspectedAnnotation,
)

from aclaf._internal._inspect import get_annotations, inspect_annotation
from aclaf._internal._metadata import flatten_metadata
from aclaf.console import Console
from aclaf.execution import (
    CommandFunctionType,
    Context,
    RuntimeParameter,
)
from aclaf.logging import Logger
from aclaf.metadata import (
    Arg,
    AtLeastOne,
    AtMostOne,
    Collect,
    Count,
    Default,
    ErrorOnDuplicate,
    ExactlyOne,
    FirstWins,
    Flag,
    LastWins,
    MetadataByType,
    MetadataType,
    Opt,
    ZeroOrMore,
)
from aclaf.parser import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    AccumulationMode,
    Arity,
)
from aclaf.types import ParameterKind

if TYPE_CHECKING:
    from aclaf.conversion import ConverterFunctionType
    from aclaf.execution import DefaultFactoryFunction
    from aclaf.types import ParameterValueType
    from aclaf.validation import ValidatorFunction


class SpecialParameters(TypedDict, total=False):
    context: str
    console: str
    logger: str


def _extract_union_metadata(type_expr: Any) -> list[MetadataType]:  # pyright: ignore[reportExplicitAny, reportAny]
    """Extract metadata from Annotated types within union type arguments.

    typing-inspection library extracts metadata from the outer Annotated layer,
    but does not extract metadata from Annotated types nested inside unions.
    This function handles that case.

    Example:
        Annotated[Annotated[int, Gt(0)] | None, Opt()]
        -> typing-inspection extracts: [Opt()]
        -> this function extracts: [Gt(0)] (from the union's type)
    """
    metadata: list[MetadataType] = []
    origin = get_origin(type_expr)  # pyright: ignore[reportAny]

    # Check if the type expression is a union (Union or UnionType from PEP 604)
    # Union comes from typing.Union, while | syntax creates types.UnionType
    if origin is Union or (origin is not None and typing_objects.is_union(type_expr)):
        # Iterate through union type arguments
        for type_arg in get_args(type_expr):
            arg_origin = get_origin(type_arg)  # pyright: ignore[reportAny]
            # If the union member is an Annotated type, extract its metadata
            if arg_origin is Annotated:
                args = get_args(type_arg)
                if len(args) > 1:
                    # args[0] is base type, args[1:] is metadata
                    metadata.extend(args[1:])

    return metadata


# Sentinel value to distinguish "no default provided" from "default=None"
class _NoDefault:
    """Sentinel value indicating no default was provided."""

    @override
    def __repr__(self) -> str:
        return "<no default>"


NO_DEFAULT: Any = _NoDefault()  # pyright: ignore[reportExplicitAny]


@dataclass(slots=True, kw_only=True)
class Parameter:
    kind: ParameterKind | None = None
    name: str | None = None


class CommandParameterInput(TypedDict, total=False):
    accumulation_mode: AccumulationMode | None
    arity: Arity | None
    const_value: str | None
    converter: "ConverterFunctionType | None"
    default: "ParameterValueType | None"
    default_factory: "DefaultFactoryFunction | None"
    falsey_flag_values: tuple[str, ...] | None
    flatten_values: bool
    help: str | None
    is_flag: bool
    is_required: bool
    kind: ParameterKind | None
    long: tuple[str, ...]
    metadata: list[MetadataType]
    name: str | None
    negation_words: tuple[str, ...] | None
    qualifiers: set[str]
    short: tuple[str, ...]
    truthy_flag_values: tuple[str, ...] | None
    value_type: "type[ParameterValueType] | None"
    validators: tuple["ValidatorFunction", ...]


@dataclass(slots=True)
class CommandParameter(Parameter):
    accumulation_mode: AccumulationMode | None = None
    arity: Arity | None = None
    const_value: str | None = None
    default: "ParameterValueType | Any" = NO_DEFAULT  # pyright: ignore[reportAny, reportExplicitAny]
    default_factory: "DefaultFactoryFunction | None" = None
    falsey_flag_values: tuple[str, ...] | None = None
    flatten_values: bool = False
    help: str | None = None
    is_flag: bool = False
    is_required: bool = False
    kind: ParameterKind | None = None
    long: tuple[str, ...] = field(default_factory=tuple)
    metadata: list[MetadataType] = field(default_factory=list)
    negation_words: tuple[str, ...] | None = None
    qualifiers: set[str] = field(default_factory=set)
    short: tuple[str, ...] = field(default_factory=tuple)
    truthy_flag_values: tuple[str, ...] | None = None
    value_type: "type[ParameterValueType] | None" = None

    converter: "ConverterFunctionType | None" = None
    validators: tuple["ValidatorFunction", ...] = field(default_factory=tuple)

    _metadata_by_type: MetadataByType | None = field(
        default=None, init=False, repr=False
    )

    @property
    def metadata_by_type(
        self,
    ) -> MetadataByType:
        if self._metadata_by_type is None:
            # Iterate in reverse order to implement last-wins semantics:
            # Since metadata is in outer-to-inner order, reversing gives us
            # inner-to-outer iteration, so outer (last in source) overwrites inner
            mapping = MappingProxyType(
                {
                    type(meta): meta
                    for meta in reversed(self.metadata)
                    if isinstance(meta, BaseMetadata)
                }
            )
            object.__setattr__(self, "_metadata_by_type", mapping)
            return mapping
        return self._metadata_by_type

    @staticmethod
    def from_annotation(
        name: str,
        annotation: Any,  # pyright: ignore[reportExplicitAny, reportAny]
        source: AnnotationSource,
        default: "ParameterValueType | None" = None,
    ) -> "CommandParameter":
        # Inspect annotation (handles nested Annotated, type aliases, etc.)
        ann = CommandParameter._inspect_annotation(name, annotation, source)

        # Flatten metadata from inspection
        metadata = flatten_metadata(ann.metadata)

        # Extract metadata from Annotated types inside unions
        # (typing-inspection doesn't do this)
        union_metadata = _extract_union_metadata(ann.type)

        # Combine metadata: outer annotation + union member metadata
        # Union metadata comes second to maintain precedence
        metadata = metadata + union_metadata

        # Reverse to ensure outer-to-inner order per spec requirement
        # (typing-inspection returns inner-to-outer, spec requires outer-to-inner)
        metadata = list(reversed(metadata))

        type_expr = CommandParameter._get_type(name, ann)  # pyright: ignore[reportAny]

        attrs: CommandParameterInput = {
            "name": name,
            "value_type": type_expr,
        }
        attrs = attrs | CommandParameter._extract_metadata_attributes(
            type_expr,  # pyright: ignore[reportAny]
            metadata,
        )

        if attrs.get("kind") is None:
            if attrs.get("long") or attrs.get("short"):
                attrs["kind"] = ParameterKind.OPTION
            elif type_expr is bool:
                attrs["kind"] = ParameterKind.OPTION
                attrs["is_flag"] = True
            else:
                msg = f"Could not determine parameter type for '{name}'"
                raise TypeError(msg)

        if default is not None:
            attrs["default"] = default

        return CommandParameter.from_metadata(metadata, **attrs)

    @staticmethod
    def from_function_parameter(
        func_parameter: FunctionParameter,
        annotation: Any,  # pyright: ignore[reportExplicitAny, reportAny]
    ) -> "CommandParameter":
        kind = func_parameter.kind

        # Inspect annotation (handles nested Annotated, type aliases, etc.)
        ann = CommandParameter._inspect_annotation(
            func_parameter.name, annotation, AnnotationSource.FUNCTION
        )

        # Flatten metadata from inspection
        metadata = flatten_metadata(ann.metadata)

        # Extract metadata from Annotated types inside unions
        # (typing-inspection doesn't do this)
        union_metadata = _extract_union_metadata(ann.type)

        # Combine metadata: outer annotation + union member metadata
        # Union metadata comes second to maintain precedence
        metadata = metadata + union_metadata

        # Reverse to ensure outer-to-inner order per spec requirement
        # (typing-inspection returns inner-to-outer, spec requires outer-to-inner)
        metadata = list(reversed(metadata))

        default = func_parameter.default  # pyright: ignore[reportAny]
        type_expr = CommandParameter._get_type(func_parameter.name, ann)  # pyright: ignore[reportAny]

        attrs: CommandParameterInput = {
            "name": func_parameter.name,
            "value_type": type_expr,
        }
        attrs = attrs | CommandParameter._extract_metadata_attributes(
            type_expr,  # pyright: ignore[reportAny]
            metadata,
            default,  # pyright: ignore[reportAny]
        )

        if attrs.get("kind") is None:
            if attrs.get("long") or attrs.get("short"):
                attrs["kind"] = ParameterKind.OPTION
            elif type_expr is bool:
                attrs["kind"] = ParameterKind.OPTION
                attrs["is_flag"] = True
            elif kind in (
                func_parameter.POSITIONAL_ONLY,
                func_parameter.VAR_POSITIONAL,
            ):
                attrs["kind"] = ParameterKind.POSITIONAL
            elif kind == func_parameter.KEYWORD_ONLY:
                attrs["kind"] = ParameterKind.OPTION
            elif kind == func_parameter.POSITIONAL_OR_KEYWORD:
                attrs["kind"] = ParameterKind.POSITIONAL
            else:
                msg = f"Could not determine parameter type for '{func_parameter.name}'"
                raise TypeError(msg)

        if default is not FunctionParameter.empty:
            attrs["default"] = default

        return CommandParameter.from_metadata(metadata, **attrs)

    @staticmethod
    def _inspect_annotation(
        name: str,
        annotation: Any,  # pyright: ignore[reportExplicitAny, reportAny]
        source: AnnotationSource,
    ) -> InspectedAnnotation:
        try:
            return inspect_annotation(
                annotation,  # pyright: ignore[reportAny]
                source,
            )
        except NameError as e:
            msg = f"Parameter '{name}' type annotation could not be resolved: {e}"
            raise TypeError(msg) from e

    @staticmethod
    def _get_type(name: str, annotation: InspectedAnnotation) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
        type_expr = annotation.type
        if type_expr is UNKNOWN:
            msg = "Command function parameters must be type-annotated"
            raise TypeError(msg)
        if typing_objects.is_typealiastype(type_expr):
            msg = (
                f"Parameter '{name}' type alias '{type_expr}' was not fully resolved."
                " Ensure that all type aliases are properly defined and imported."
            )
        return type_expr

    @staticmethod
    def _extract_metadata_attributes(  # noqa: PLR0912, PLR0915
        type_expr: type["ParameterValueType"],
        metadata: list[MetadataType],
        default: "ParameterValueType | None" = None,
    ) -> CommandParameterInput:
        attrs: CommandParameterInput = {}
        kind: ParameterKind | None = None
        long_names: list[str] = []
        short_names: list[str] = []

        # Track seen metadata categories for conflict detection
        arity_metadata: list[str] = []
        accumulation_metadata: list[str] = []
        kind_metadata: list[str] = []

        if type_expr is bool and default is not None:
            attrs["kind"] = ParameterKind.OPTION
            attrs["is_flag"] = True

        for meta in metadata:
            match meta:
                # String-based patterns (name declarations and arity shortcuts)
                case str(name) if name.startswith("--"):
                    long_names.append(name[2:])
                    kind = ParameterKind.OPTION if kind is None else kind
                case str(name) if name.startswith("-") and len(name) == 2:  # noqa: PLR2004
                    short_names.append(name[1:])
                    kind = ParameterKind.OPTION if kind is None else kind
                case "1" | ExactlyOne():
                    arity_metadata.append("ExactlyOne")
                    attrs["arity"] = EXACTLY_ONE_ARITY
                case "?" | AtMostOne():
                    arity_metadata.append("AtMostOne")
                    attrs["arity"] = ZERO_OR_ONE_ARITY
                case "*" | ZeroOrMore():
                    arity_metadata.append("ZeroOrMore")
                    attrs["arity"] = ZERO_OR_MORE_ARITY
                case "+" | AtLeastOne():
                    arity_metadata.append("AtLeastOne")
                    attrs["arity"] = ONE_OR_MORE_ARITY

                # Integer arity
                case int(n) if n > 1:
                    arity_metadata.append(f"int({n})")
                    attrs["arity"] = Arity(min=n, max=n)

                # Accumulation modes
                case FirstWins():
                    accumulation_metadata.append("FirstWins")
                    attrs["accumulation_mode"] = AccumulationMode.FIRST_WINS
                case LastWins():
                    accumulation_metadata.append("LastWins")
                    attrs["accumulation_mode"] = AccumulationMode.LAST_WINS
                case ErrorOnDuplicate():
                    accumulation_metadata.append("ErrorOnDuplicate")
                    attrs["accumulation_mode"] = AccumulationMode.ERROR
                case Collect(flatten=flatten):
                    accumulation_metadata.append("Collect")
                    attrs["accumulation_mode"] = AccumulationMode.COLLECT
                    attrs["flatten_values"] = flatten
                case Count():
                    accumulation_metadata.append("Count")
                    attrs["accumulation_mode"] = AccumulationMode.COUNT

                # Parameter kinds
                case Arg():
                    kind_metadata.append("Arg")
                    kind = ParameterKind.POSITIONAL if kind is None else kind
                case Opt():
                    kind_metadata.append("Opt")
                    kind = ParameterKind.OPTION if kind is None else kind
                case Flag(
                    const=const,
                    falsey=falsey,
                    truthy=truthy,
                    negation=negation,
                    count=count,
                ):
                    kind_metadata.append("Flag")
                    kind = ParameterKind.OPTION if kind is None else kind
                    attrs["is_flag"] = True
                    attrs["const_value"] = const
                    attrs["falsey_flag_values"] = falsey
                    attrs["truthy_flag_values"] = truthy
                    attrs["negation_words"] = negation
                    if count:
                        accumulation_metadata.append("Count (from Flag)")
                        attrs["accumulation_mode"] = AccumulationMode.COUNT

                # Default values
                case Default() as default_meta:
                    attrs["default"] = default_meta.value

                # Ignore other metadata types
                case _:
                    pass

        # Conflict detection
        if len(arity_metadata) > 1:
            arity_list = ", ".join(arity_metadata)
            msg = f"Multiple arity specifications found: {arity_list}"
            raise ValueError(msg)

        if len(accumulation_metadata) > 1:
            acc_list = ", ".join(accumulation_metadata)
            msg = f"Multiple accumulation modes found: {acc_list}"
            raise ValueError(msg)

        # Check for Arg and Opt being mutually exclusive (Flag can coexist with Opt)
        if "Arg" in kind_metadata and (
            "Opt" in kind_metadata or "Flag" in kind_metadata
        ):
            msg = "Arg metadata cannot be combined with Opt or Flag metadata"
            raise ValueError(msg)

        # Validate Flag metadata compatibility
        if attrs.get("is_flag") and type_expr not in (bool, int):
            type_name = type_expr.__name__
            msg = f"Flag metadata requires bool or int base type, got {type_name}"
            raise ValueError(msg)

        # Validate Count accumulation mode compatibility
        if attrs.get(
            "accumulation_mode"
        ) == AccumulationMode.COUNT and type_expr not in (int, float):
            type_name = type_expr.__name__
            msg = (
                f"Count accumulation mode requires int or float result type, "
                f"got {type_name}"
            )
            raise ValueError(msg)

        if long_names:
            attrs["long"] = tuple(long_names)
        if short_names:
            attrs["short"] = tuple(short_names)
        if kind is not None:
            attrs["kind"] = kind

        return attrs

    @classmethod
    def from_metadata(
        cls,
        metadata: list[MetadataType],
        /,
        **overrides: Unpack[CommandParameterInput],
    ) -> "CommandParameter":
        merged_metadata: list[MetadataType] = []
        merged_kwargs: CommandParameterInput = {}

        for meta in metadata:
            if isinstance(meta, CommandParameter):
                merged_metadata.extend(meta.metadata)
            else:
                merged_metadata.append(meta)

        merged_kwargs.update(overrides)

        if "default" not in merged_kwargs:
            merged_kwargs.update({"is_required": True})

        merged_parameter = cls(**merged_kwargs)
        merged_parameter.metadata = merged_metadata
        return merged_parameter

    def to_runtime_parameter(self) -> "RuntimeParameter":
        if self.kind == ParameterKind.OPTION:
            return self._to_runtime_option()
        if self.kind == ParameterKind.POSITIONAL:
            return self._to_runtime_positional()
        msg = "Parameter kind must be OPTION or POSITIONAL to convert"
        raise TypeError(msg)

    def _to_runtime_option(self) -> "RuntimeParameter":
        if self.kind != ParameterKind.OPTION:
            msg = "Can only convert option parameters to RuntimeOption"
            raise TypeError(msg)

        if self.name is None:
            msg = "Parameter name must be set to convert to RuntimePositional"
            raise ValueError(msg)

        if self.value_type is None:
            msg = "Parameter type must be set to convert to RuntimePositional"
            raise ValueError(msg)

        if self.is_flag:
            arity = ZERO_ARITY
        elif self.arity is None:
            arity = EXACTLY_ONE_ARITY
        else:
            arity = self.arity

        if self.accumulation_mode is None:
            accumulation_mode = AccumulationMode.LAST_WINS
        else:
            accumulation_mode = self.accumulation_mode

        metadata = [meta for meta in self.metadata if isinstance(meta, BaseMetadata)]

        # Convert NO_DEFAULT sentinel back to None for RuntimeParameter
        default = None if self.default is NO_DEFAULT else self.default

        return RuntimeParameter(
            name=self.name,
            kind=self.kind,
            value_type=self.value_type,
            metadata=tuple(metadata),
            long=self.long or (),
            short=self.short or (),
            arity=arity,
            accumulation_mode=accumulation_mode,
            is_flag=self.is_flag,
            is_required=self.is_required,
            falsey_flag_values=self.falsey_flag_values,
            truthy_flag_values=self.truthy_flag_values,
            negation_words=self.negation_words,
            const_value=self.const_value,
            flatten_values=self.flatten_values,
            default=default,
            default_factory=self.default_factory,
            help=self.help,
        )

    def _to_runtime_positional(self) -> "RuntimeParameter":
        if self.kind != ParameterKind.POSITIONAL:
            msg = "Can only convert positional parameters to RuntimePositional"
            raise TypeError(msg)

        if self.name is None:
            msg = "Parameter name must be set to convert to RuntimePositional"
            raise ValueError(msg)

        if self.value_type is None:
            msg = "Parameter type must be set to convert to RuntimePositional"
            raise ValueError(msg)

        # Check if a default was provided (including None) or default_factory
        has_default = self.default is not NO_DEFAULT or self.default_factory is not None
        arity = self.arity or Arity(min=0 if has_default else 1, max=1)

        metadata = [meta for meta in self.metadata if isinstance(meta, BaseMetadata)]

        # Convert NO_DEFAULT sentinel back to None for RuntimeParameter
        default = None if self.default is NO_DEFAULT else self.default

        return RuntimeParameter(
            name=self.name,
            kind=self.kind,
            value_type=self.value_type,
            metadata=tuple(metadata),
            arity=arity,
            default=default,
            default_factory=self.default_factory,
            help=self.help,
            is_required=self.is_required,
        )


def extract_typeddict_parameters(typeddict_type: type) -> dict[str, CommandParameter]:
    parameters: dict[str, CommandParameter] = {}
    # Use get_type_hints to resolve forward references in Python 3.14+
    annotations = get_type_hints(typeddict_type, include_extras=True)
    for name, annotation in annotations.items():  # pyright: ignore[reportAny]
        parameters[name] = CommandParameter.from_annotation(
            name, annotation, AnnotationSource.TYPED_DICT
        )
    return parameters


def extract_function_parameters(
    func: "CommandFunctionType",
) -> tuple[dict[str, Parameter], SpecialParameters]:
    sig = inspect.signature(func)
    parameters: dict[str, Parameter] = {}
    special_parameters: SpecialParameters = {}

    annotations = get_annotations(func)
    for func_parameter in sig.parameters.values():
        annotation = annotations[func_parameter.name]  # pyright: ignore[reportAny]

        if annotation is Context:
            special_parameters["context"] = func_parameter.name
            continue
        if isinstance(annotation, Console):
            special_parameters["console"] = func_parameter.name
            continue
        if isinstance(annotation, Logger):
            special_parameters["logger"] = func_parameter.name
            continue

        origin = get_origin(annotation)  # pyright: ignore[reportAny]

        if (
            func_parameter.kind == func_parameter.VAR_KEYWORD
            and typing_objects.is_unpack(origin)
        ):
            parameters.update(
                extract_typeddict_parameters(get_args(annotation)[0])  # pyright: ignore[reportAny]
            )
            continue

        parameters[func_parameter.name] = CommandParameter.from_function_parameter(
            func_parameter, annotation
        )

    return parameters, special_parameters
