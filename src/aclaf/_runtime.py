import inspect
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum, auto
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Protocol,
    TypeAlias,
    cast,
)
from typing_extensions import override

from aclaf._converters import ConverterRegistry
from aclaf._validation import ParameterValidatorRegistry
from aclaf.exceptions import ConversionError, ValidationError
from aclaf.logging import Logger, NullLogger

from ._context import Context
from ._response import (
    AsyncResponseType,
    ConsoleResponder,
    ResponderProtocol,
    ResponseType,
    SyncResponseType,
)
from ._types import ParameterValueType
from .console import DefaultConsole
from .parser import (
    AccumulationMode,
    Arity,
    BaseParser,
    CommandSpec,
    OptionSpec,
    Parser,
    ParserConfiguration,
    PositionalSpec,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from annotated_types import BaseMetadata

    from aclaf._validation import (
        ParameterSetValidatorFunctionType,
        ParameterValidatorFunctionType,
    )

    from ._converters import ConverterFunctionType
    from .parser import ParsedParameterValue, ParseResult

SyncCommandFunctionType: TypeAlias = Callable[..., SyncResponseType]
AsyncCommandFunctionType: TypeAlias = Callable[..., AsyncResponseType]

CommandFunctionType: TypeAlias = SyncCommandFunctionType | AsyncCommandFunctionType

EMPTY_COMMAND_FUNCTION: CommandFunctionType = lambda: None  # noqa: E731

DefaultFactoryFunction: TypeAlias = Callable[..., ParameterValueType]


class ParameterKind(IntEnum):
    CONSOLE = auto()
    CONTEXT = auto()
    OPTION = auto()
    POSITIONAL = auto()


@dataclass(slots=True, frozen=True)
class RuntimeParameter:
    name: str
    kind: ParameterKind
    value_type: "type[ParameterValueType]"
    arity: Arity
    accumulation_mode: AccumulationMode | None = None
    long: tuple[str, ...] = field(default_factory=tuple)
    short: tuple[str, ...] = field(default_factory=tuple)
    is_flag: bool = False
    falsey_flag_values: tuple[str, ...] | None = None
    truthy_flag_values: tuple[str, ...] | None = None
    negation_words: tuple[str, ...] | None = None
    const_value: str | None = None
    flatten_values: bool = False
    default: "ParameterValueType | None" = None
    default_factory: "DefaultFactoryFunction | None" = None
    help: str | None = None
    metadata: tuple["BaseMetadata", ...] = field(default_factory=tuple)
    converter: "ConverterFunctionType | None" = None
    validators: tuple["ParameterValidatorFunctionType", ...] = field(
        default_factory=tuple
    )

    _metadata_by_type: Mapping[type["BaseMetadata"], "BaseMetadata"] | None = field(
        default=None, init=False, repr=False
    )

    @property
    def metadata_by_type(self) -> Mapping[type["BaseMetadata"], "BaseMetadata"]:
        if self._metadata_by_type is None:
            object.__setattr__(
                self,
                "_metadata_by_type",
                MappingProxyType({type(meta): meta for meta in self.metadata}),
            )
        return MappingProxyType({type(meta): meta for meta in self.metadata})

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


class RespondFunctionProtocol(Protocol):
    def __call__(
        self,
        result: ResponseType | None,
        context: Context,
        command: "RuntimeCommand",
    ) -> ResponderProtocol: ...


DEFAULT_RESPONDER_KEY = "default"


def default_respond(
    result: ResponseType | None,  # noqa: ARG001  # pyright: ignore[reportUnusedParameter]
    context: Context,
    command: "RuntimeCommand",
) -> ResponderProtocol:
    if command.responders and DEFAULT_RESPONDER_KEY in command.responders:
        return command.responders[DEFAULT_RESPONDER_KEY]
    return ConsoleResponder(console=context.console)


@dataclass(slots=True, frozen=True)
class RuntimeCommand:
    name: str
    run_func: CommandFunctionType
    aliases: tuple[str, ...] = field(default_factory=tuple)
    parameters: "Mapping[str, RuntimeParameter]" = field(
        default_factory=lambda: MappingProxyType({})
    )
    is_async: bool = False
    logger: Logger = field(default_factory=NullLogger)
    parser_cls: type[BaseParser] = Parser
    parser_config: ParserConfiguration | None = None
    respond: RespondFunctionProtocol = default_respond
    responders: "Mapping[str, ResponderProtocol]" = field(
        default_factory=lambda: MappingProxyType({})
    )
    subcommands: "Mapping[str, RuntimeCommand]" = field(
        default_factory=lambda: MappingProxyType({})
    )
    validators: tuple["ParameterSetValidatorFunctionType", ...] = field(
        default_factory=tuple
    )

    _cached_spec: CommandSpec | None = field(default=None, init=False, repr=False)
    _validators: "ParameterValidatorRegistry" = field(
        default_factory=lambda: ParameterValidatorRegistry(), repr=False
    )
    _converters: "ConverterRegistry" = field(
        default_factory=lambda: ConverterRegistry(), repr=False
    )

    def __post_init__(self) -> None:
        for attr in ("parameters", "responders", "subcommands"):
            value: Mapping[
                str, ConsoleResponder | RuntimeParameter | RuntimeCommand
            ] = cast(
                "Mapping[str, ConsoleResponder | RuntimeParameter | RuntimeCommand]",
                getattr(self, attr),
            )
            if not isinstance(value, MappingProxyType):
                object.__setattr__(
                    self,
                    attr,
                    MappingProxyType(dict(value)),
                )

    def __call__(self, args: "Sequence[str] | None" = None) -> None:
        self.invoke(args)

    @property
    def options(self) -> MappingProxyType[str, RuntimeParameter]:
        return MappingProxyType(
            {k: v for k, v in self.parameters.items() if v.kind == ParameterKind.OPTION}
        )

    @property
    def positionals(self) -> MappingProxyType[str, RuntimeParameter]:
        return MappingProxyType(
            {
                k: v
                for k, v in self.parameters.items()
                if v.kind == ParameterKind.POSITIONAL
            }
        )

    @override
    def __repr__(self) -> str:
        return (
            f"RuntimeCommand("
            f"name={self.name!r},"
            f" aliases={self.aliases!r},"
            f" is_async={self.is_async!r},"
            f" parameters={self.parameters!r},"
            f" parser_cls={self.parser_cls!r},"
            f" parser_config={self.parser_config!r},"
            f" run_func={self.run_func!r},"
            f" subcommands={self.subcommands!r},"
            f" responders={self.responders!r},"
            ")"
        )

    def invoke(self, args: "Sequence[str] | None" = None) -> None:
        spec = self.to_command_spec()
        parser = self.parser_cls(spec, self.parser_config)
        parse_result = parser.parse(args or sys.argv[1:])

        parameters, conversion_errors = self._convert_parameters(
            parse_result, self.parameters
        )
        errors = self._validate_parameters(
            parameters, self.parameters, conversion_errors
        )

        context = Context(
            command=self.name,
            command_path=(self.name,),
            parse_result=parse_result,
            parameters=parameters,
            errors=errors,
            is_async=self.check_async(parse_result),
            console=DefaultConsole(),
            logger=self.logger,
        )

        if context.is_async:
            import asyncio  # noqa: PLC0415

            asyncio.run(self.dispatch_async(context))
        else:
            self.dispatch(context)

    def check_async(self, parse_result: "ParseResult") -> bool:
        if self.is_async:
            return True
        if parse_result.subcommand:
            subcommand_name = parse_result.subcommand.command
            subcommand = self.subcommands.get(subcommand_name)
            if not subcommand:
                msg = f"Unknown subcommand: {subcommand_name}"
                raise ValueError(msg)
            return subcommand.check_async(parse_result.subcommand)
        return False

    def dispatch(self, context: Context) -> None:
        if context.errors and context.parse_result.subcommand is None:
            all_errors = self._collect_errors(context)
            raise ValidationError(all_errors)

        result = self.run_func(**context.parameters)
        responder = self.respond(result, context, self)
        responder.respond(result, context)

        if subcommand_dispatch := self._prepare_subcommand_dispatch(context):
            subcommand, subcommand_context = subcommand_dispatch
            subcommand.dispatch(subcommand_context)

    async def dispatch_async(self, context: Context) -> None:
        responder = self.respond(None, context, self)
        result = self.run_func(**context.parameters)
        if self.is_async:
            if inspect.isasyncgen(result) or inspect.iscoroutine(result):
                await responder.respond_async(result, context)
            else:
                msg = "Async command returned non-awaitable result"
                raise TypeError(msg)
        else:
            responder.respond(result, context)

        if subcommand_dispatch := self._prepare_subcommand_dispatch(context):
            subcommand, subcommand_context = subcommand_dispatch
            await subcommand.dispatch_async(subcommand_context)

    def _prepare_subcommand_dispatch(
        self, context: Context
    ) -> "tuple[RuntimeCommand, Context] | None":
        """Prepare subcommand dispatch if needed, returning subcommand and context."""
        if (
            self.subcommands
            and context.parse_result.subcommand
            and context.parse_result.subcommand.command
        ):
            subcommand_name = context.parse_result.subcommand.command
            subcommand = self.subcommands[subcommand_name]

            parameters, conversion_errors = self._convert_parameters(
                context.parse_result.subcommand, subcommand.parameters
            )
            errors = self._validate_parameters(
                parameters, subcommand.parameters, conversion_errors
            )

            subcommand_context = Context(
                parent=context,
                command=subcommand.name,
                command_path=(*context.command_path, subcommand.name),
                parse_result=context.parse_result.subcommand,
                parameters=parameters,
                errors=errors,
                console=context.console,
                logger=context.logger,
            )
            return (subcommand, subcommand_context)
        return None

    def _convert_parameters(
        self, parse_result: "ParseResult", parameters: "Mapping[str, RuntimeParameter]"
    ) -> tuple[dict[str, "ParameterValueType"], dict[str, str]]:
        raw: dict[str, ParsedParameterValue] = {}
        converted: dict[str, ParameterValueType] = {}
        errors: dict[str, str] = {}

        for name, parsed in parse_result.options.items():
            raw[name] = parsed.value
        for name, parsed in parse_result.positionals.items():
            raw[name] = parsed.value

        for name, parameter in parameters.items():
            if name not in raw and parameter.default is not None:
                if parameter.default_factory is not None:
                    converted[name] = parameter.default_factory()
                else:
                    converted[name] = parameter.default
                continue

            type_expr = parameter.value_type
            value = raw.get(name)
            if value is None:
                continue
            try:
                if parameter.converter:
                    converted[name] = parameter.converter(value, parameter.metadata)
                else:
                    converted[name] = self._converters.convert(
                        value, type_expr, parameter.metadata
                    )
            except ConversionError as e:
                errors[name] = str(e)

        return converted, errors

    def _validate_parameters(
        self,
        raw: dict[str, "ParameterValueType"],
        parameters: "Mapping[str, RuntimeParameter]",
        conversion_errors: dict[str, str],
    ) -> dict[str, tuple[str, ...]]:
        errors: dict[str, tuple[str, ...]] = {}
        for name, parameter in parameters.items():
            if name in conversion_errors:
                errors[name] = (conversion_errors[name],)
                continue

            value = raw.get(name)
            value_errors: tuple[str, ...] | None = self._validators.validate(
                value, raw, parameter.metadata
            )

            if value_errors:
                errors[name] = tuple(value_errors)

        return errors

    def _collect_errors(
        self, context: Context
    ) -> dict[str, dict[str, tuple[str, ...]]]:
        errors: dict[str, dict[str, tuple[str, ...]]] = {}
        if context.errors:
            errors[self.name] = dict(context.errors)
        if context.parent:
            parent_errors = self._collect_errors(context.parent)
            errors.update(parent_errors)
        return errors

    def to_command_spec(self) -> CommandSpec:
        if self._cached_spec is None:
            object.__setattr__(
                self,
                "_cached_spec",
                CommandSpec(
                    name=self.name,
                    aliases=frozenset(self.aliases),
                    options={
                        param: opt.to_option_spec()
                        for param, opt in self.options.items()
                    },
                    positionals={
                        param: pos.to_positional_spec()
                        for param, pos in self.positionals.items()
                    },
                    subcommands={
                        name: cmd.to_command_spec()
                        for name, cmd in self.subcommands.items()
                    },
                ),
            )
        return cast("CommandSpec", self._cached_spec)


def is_async_command_function(
    func: CommandFunctionType,
) -> bool:
    return bool(inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func))
