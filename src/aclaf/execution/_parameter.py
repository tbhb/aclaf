from collections.abc import Callable
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    TypeAlias,
    TypedDict,
)
from typing_extensions import override

from aclaf.console import Console
from aclaf.logging import Logger
from aclaf.parser import (
    AccumulationMode,
    Arity,
    OptionSpec,
    PositionalSpec,
)
from aclaf.response import (
    AsyncResponseType,
    SyncResponseType,
)
from aclaf.types import ParameterKind, ParameterValueType

from ._context import Context

if TYPE_CHECKING:
    from annotated_types import BaseMetadata

    from aclaf.conversion import ConverterFunctionType
    from aclaf.metadata import MetadataByType
    from aclaf.validation import (
        ValidatorFunction,
    )

DefaultFactoryFunction: TypeAlias = Callable[..., ParameterValueType]

SyncCommandFunctionType: TypeAlias = Callable[..., SyncResponseType]
AsyncCommandFunctionType: TypeAlias = Callable[..., AsyncResponseType]

CommandFunctionType: TypeAlias = SyncCommandFunctionType | AsyncCommandFunctionType

CommandFunctionRunParameters: TypeAlias = dict[
    str, ParameterValueType | None | Context | Console | Logger
]

EMPTY_COMMAND_FUNCTION: CommandFunctionType = lambda: None  # noqa: E731


class RuntimeParameterInput(TypedDict, total=False):
    name: str
    kind: ParameterKind
    value_type: "type[ParameterValueType]"
    arity: Arity
    accumulation_mode: AccumulationMode | None
    const_value: str | None
    converter: "ConverterFunctionType | None"
    default: "ParameterValueType | None"
    default_factory: "DefaultFactoryFunction | None"
    falsey_flag_values: tuple[str, ...] | None
    flatten_values: bool
    help: str | None
    is_flag: bool
    is_required: bool
    long: tuple[str, ...]
    metadata: tuple["BaseMetadata", ...]
    negation_words: tuple[str, ...] | None
    short: tuple[str, ...]
    truthy_flag_values: tuple[str, ...] | None
    validators: tuple["ValidatorFunction", ...]


@dataclass(slots=True, frozen=True)
class RuntimeParameter:
    name: str
    kind: ParameterKind
    value_type: "type[ParameterValueType]"
    arity: Arity
    accumulation_mode: AccumulationMode | None = None
    const_value: str | None = None
    converter: "ConverterFunctionType | None" = None
    default: "ParameterValueType | None" = None
    default_factory: "DefaultFactoryFunction | None" = None
    falsey_flag_values: tuple[str, ...] | None = None
    flatten_values: bool = False
    help: str | None = None
    is_flag: bool = False
    is_required: bool = False
    long: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple["BaseMetadata", ...] = field(default_factory=tuple)
    negation_words: tuple[str, ...] | None = None
    short: tuple[str, ...] = field(default_factory=tuple)
    truthy_flag_values: tuple[str, ...] | None = None
    validators: tuple["ValidatorFunction", ...] = field(default_factory=tuple)

    _metadata_by_type: "MetadataByType | None" = field(
        default=None, init=False, repr=False
    )

    @property
    def metadata_by_type(
        self,
    ) -> "MetadataByType":
        if self._metadata_by_type is None:
            mapping = MappingProxyType({type(meta): meta for meta in self.metadata})
            object.__setattr__(self, "_metadata_by_type", mapping)
            return mapping
        return self._metadata_by_type

    @override
    def __repr__(self) -> str:
        return (
            f"RuntimeParameter("
            f"accumulation_mode={self.accumulation_mode!r},"
            f" arity={self.arity!r},"
            f" const_value={self.const_value!r},"
            f" converter={self.converter!r},"
            f" default={self.default!r},"
            f" default_factory={self.default_factory!r},"
            f" falsey_flag_values={self.falsey_flag_values!r},"
            f" flatten_values={self.flatten_values!r},"
            f" help={self.help!r},"
            f" is_flag={self.is_flag!r},"
            f" is_required={self.is_required!r},"
            f" kind={self.kind!r},"
            f" long={self.long!r},"
            f" metadata={self.metadata!r},"
            f" name={self.name!r},"
            f" negation_words={self.negation_words!r},"
            f" short={self.short!r},"
            f" truthy_flag_values={self.truthy_flag_values!r},"
            f" validators={self.validators!r},"
            f" value_type={self.value_type!r},"
            f")"
        )

    def to_option_spec(self) -> OptionSpec:
        if self.kind != ParameterKind.OPTION:
            msg = "Can only convert option parameters to OptionSpec"
            raise TypeError(msg)

        accumulation_mode = self.accumulation_mode or AccumulationMode.LAST_WINS

        return OptionSpec(
            name=self.name,
            long=frozenset(self.long or ()),
            short=frozenset(self.short or ()),
            arity=self.arity,
            accumulation_mode=accumulation_mode,
            is_flag=self.is_flag,
            falsey_flag_values=frozenset(self.falsey_flag_values)
            if self.falsey_flag_values
            else None,
            truthy_flag_values=frozenset(self.truthy_flag_values)
            if self.truthy_flag_values
            else None,
            negation_words=frozenset(self.negation_words)
            if self.negation_words
            else None,
            const_value=self.const_value,
            flatten_values=self.flatten_values,
        )

    def to_positional_spec(self) -> PositionalSpec:
        if self.kind != ParameterKind.POSITIONAL:
            msg = "Can only convert positional parameters to PositionalSpec"
            raise TypeError(msg)

        return PositionalSpec(name=self.name, arity=self.arity)
