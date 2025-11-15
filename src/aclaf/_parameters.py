import inspect
from dataclasses import dataclass, field
from inspect import Parameter as FunctionParameter
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, TypedDict, Unpack, get_args, get_origin
from typing_extensions import get_annotations

from annotated_types import BaseMetadata
from typing_inspection import typing_objects
from typing_inspection.introspection import (
    UNKNOWN,
    AnnotationSource,
    InspectedAnnotation,
    inspect_annotation,
)

from ._context import Context
from ._internal._metadata import flatten_metadata
from ._runtime import (
    CommandFunctionType,
    ParameterKind,
    RuntimeParameter,
)
from .console import BaseConsole
from .metadata import (
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
    MetadataType,
    Opt,
    ZeroOrMore,
)
from .parser import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    AccumulationMode,
    Arity,
)

if TYPE_CHECKING:
    from ._converters import ConverterFunctionType
    from ._runtime import DefaultFactoryFunction
    from ._types import ParameterValueType
    from ._validation import ParameterValidatorFunctionType


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
    kind: ParameterKind | None
    long: tuple[str, ...]
    metadata: list[MetadataType]
    name: str | None
    negation_words: tuple[str, ...] | None
    qualifiers: set[str]
    short: tuple[str, ...]
    truthy_flag_values: tuple[str, ...] | None
    value_type: "type[ParameterValueType] | None"
    validators: tuple["ParameterValidatorFunctionType", ...]


@dataclass(slots=True)
class CommandParameter(Parameter):
    accumulation_mode: AccumulationMode | None = None
    arity: Arity | None = None
    const_value: str | None = None
    default: "ParameterValueType | None" = None
    default_factory: "DefaultFactoryFunction | None" = None
    falsey_flag_values: tuple[str, ...] | None = None
    flatten_values: bool = False
    help: str | None = None
    is_flag: bool = False
    kind: ParameterKind | None = None
    long: tuple[str, ...] = field(default_factory=tuple)
    metadata: list[MetadataType] = field(default_factory=list)
    negation_words: tuple[str, ...] | None = None
    qualifiers: set[str] = field(default_factory=set)
    short: tuple[str, ...] = field(default_factory=tuple)
    truthy_flag_values: tuple[str, ...] | None = None
    value_type: "type[ParameterValueType] | None" = None

    converter: "ConverterFunctionType | None" = None
    validators: tuple["ParameterValidatorFunctionType", ...] = field(
        default_factory=tuple
    )

    _metadata_by_type: MappingProxyType[type["BaseMetadata"], "BaseMetadata"] | None = (
        field(default=None, init=False, repr=False)
    )

    @property
    def metadata_by_type(
        self,
    ) -> MappingProxyType[type["BaseMetadata"], "BaseMetadata"]:
        if self._metadata_by_type is None:
            mapping = MappingProxyType(
                {
                    type(meta): meta
                    for meta in self.metadata
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
        ann = CommandParameter._inspect_annotation(name, annotation, source)
        metadata: list[MetadataType] = flatten_metadata(ann.metadata)
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
            if attrs.get("long_names") or attrs.get("short_names"):
                attrs["kind"] = ParameterKind.OPTION
            if isinstance(type_expr, bool):
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
        ann = CommandParameter._inspect_annotation(
            func_parameter.name, annotation, AnnotationSource.FUNCTION
        )
        metadata = flatten_metadata(ann.metadata)
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
            if attrs.get("long_names") or attrs.get("short_names"):
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
                annotation,
                annotation_source=source,
                unpack_type_aliases="eager",
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
                    attrs["arity"] = EXACTLY_ONE_ARITY
                case "?" | AtMostOne():
                    attrs["arity"] = ZERO_OR_ONE_ARITY
                case "*" | ZeroOrMore():
                    attrs["arity"] = ZERO_OR_MORE_ARITY
                case "+" | AtLeastOne():
                    attrs["arity"] = ONE_OR_MORE_ARITY

                # Integer arity
                case int(n) if n > 1:
                    attrs["arity"] = Arity(min=n, max=n)

                # Accumulation modes
                case FirstWins():
                    attrs["accumulation_mode"] = AccumulationMode.FIRST_WINS
                case LastWins():
                    attrs["accumulation_mode"] = AccumulationMode.LAST_WINS
                case ErrorOnDuplicate():
                    attrs["accumulation_mode"] = AccumulationMode.ERROR
                case Collect(flatten=flatten):
                    attrs["accumulation_mode"] = AccumulationMode.COLLECT
                    attrs["flatten_values"] = flatten
                case Count():
                    attrs["accumulation_mode"] = AccumulationMode.COUNT

                # Parameter kinds
                case Arg():
                    kind = ParameterKind.POSITIONAL if kind is None else kind
                case Opt():
                    kind = ParameterKind.OPTION if kind is None else kind
                case Flag(
                    const=const,
                    falsey=falsey,
                    truthy=truthy,
                    negation=negation,
                    count=count,
                ):
                    kind = ParameterKind.OPTION if kind is None else kind
                    attrs["is_flag"] = True
                    attrs["const_value"] = const
                    attrs["falsey_flag_values"] = falsey
                    attrs["truthy_flag_values"] = truthy
                    attrs["negation_words"] = negation
                    if count:
                        attrs["accumulation_mode"] = AccumulationMode.COUNT

                # Default values
                case Default() as default_meta:
                    attrs["default"] = default_meta.value

                # Ignore other metadata types
                case _:
                    pass

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
            falsey_flag_values=self.falsey_flag_values,
            truthy_flag_values=self.truthy_flag_values,
            negation_words=self.negation_words,
            const_value=self.const_value,
            flatten_values=self.flatten_values,
            default=self.default,
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

        arity = EXACTLY_ONE_ARITY if self.arity is None else self.arity

        metadata = [meta for meta in self.metadata if isinstance(meta, BaseMetadata)]

        return RuntimeParameter(
            name=self.name,
            kind=self.kind,
            value_type=self.value_type,
            metadata=tuple(metadata),
            arity=arity,
            default=self.default,
            default_factory=self.default_factory,
            help=self.help,
        )


@dataclass(slots=True)
class ContextParameter(Parameter):
    pass


@dataclass(slots=True)
class ConsoleParameter(Parameter):
    pass


def extract_typeddict_parameters(typeddict_type: type) -> dict[str, CommandParameter]:
    parameters: dict[str, CommandParameter] = {}
    annotations = get_annotations(typeddict_type, eval_str=True)
    for name, annotation in annotations.items():  # pyright: ignore[reportAny]
        parameters[name] = CommandParameter.from_annotation(
            name, annotation, AnnotationSource.TYPED_DICT
        )
    return parameters


def extract_function_parameters(
    func: "CommandFunctionType",
) -> dict[str, Parameter]:
    sig = inspect.signature(func)
    parameters: dict[str, Parameter] = {}

    annotations = get_annotations(func, eval_str=True)
    for func_parameter in sig.parameters.values():
        annotation = annotations[func_parameter.name]  # pyright: ignore[reportAny]

        if annotation is Context:
            parameters[func_parameter.name] = ContextParameter(name=func_parameter.name)
            continue
        if isinstance(annotation, BaseConsole):
            parameters[func_parameter.name] = ConsoleParameter(name=func_parameter.name)
            continue

        origin = get_origin(annotation)  # pyright: ignore[reportAny]

        if (
            func_parameter.kind == func_parameter.VAR_KEYWORD
            and typing_objects.is_unpack(origin)
        ):
            parameters.update(
                extract_typeddict_parameters(get_args(annotation.type)[0])  # pyright: ignore[reportAny]
            )

        parameters[func_parameter.name] = CommandParameter.from_function_parameter(
            func_parameter, annotation
        )

    return parameters
