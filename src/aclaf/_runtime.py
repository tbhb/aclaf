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
    TypedDict,
    cast,
)
from typing_extensions import override

from aclaf._errors import ErrorConfiguration
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
from .console import Console, DefaultConsole
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
from .types import ParameterValueType

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from annotated_types import BaseMetadata

    from aclaf._conversion import ConverterRegistry
    from aclaf._validation import (
        ParameterValidatorFunctionType,
        ParameterValidatorRegistry,
    )
    from aclaf.metadata import MetadataByType

    from ._conversion import ConverterFunctionType
    from .parser import ParsedParameterValue, ParseResult

SyncCommandFunctionType: TypeAlias = Callable[..., SyncResponseType]
AsyncCommandFunctionType: TypeAlias = Callable[..., AsyncResponseType]

CommandFunctionType: TypeAlias = SyncCommandFunctionType | AsyncCommandFunctionType

EMPTY_COMMAND_FUNCTION: CommandFunctionType = lambda: None  # noqa: E731

DefaultFactoryFunction: TypeAlias = Callable[..., ParameterValueType]

CommandFunctionRunParameters: TypeAlias = dict[
    str, ParameterValueType | Context | Console | Logger
]


class ParameterKind(IntEnum):
    OPTION = auto()
    POSITIONAL = auto()


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
    validators: tuple["ParameterValidatorFunctionType", ...]


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
    validators: tuple["ParameterValidatorFunctionType", ...] = field(
        default_factory=tuple
    )

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


class RuntimeCommandInput(TypedDict, total=False):
    name: str
    run_func: CommandFunctionType
    converters: "ConverterRegistry"
    validators: "ParameterValidatorRegistry"
    aliases: tuple[str, ...]
    console: "Console | None"
    console_param: str | None
    context_param: str | None
    error_config: "ErrorConfiguration"
    parameters: "Mapping[str, RuntimeParameter]"
    is_async: bool
    logger: Logger
    logger_param: str | None
    parser_cls: type[BaseParser]
    parser_config: ParserConfiguration | None
    respond: RespondFunctionProtocol
    responders: "Mapping[str, ResponderProtocol]"
    subcommands: "Mapping[str, RuntimeCommand]"


@dataclass(slots=True, frozen=True)
class RuntimeCommand:
    name: str
    run_func: CommandFunctionType
    converters: "ConverterRegistry" = field(repr=False)
    validators: "ParameterValidatorRegistry" = field(repr=False)
    aliases: tuple[str, ...] = field(default_factory=tuple)
    console: "Console | None" = None
    console_param: str | None = None
    context_param: str | None = None
    error_config: "ErrorConfiguration" = field(default_factory=ErrorConfiguration)
    parameters: "Mapping[str, RuntimeParameter]" = field(
        default_factory=lambda: MappingProxyType({})
    )
    is_async: bool = False
    logger: Logger = field(default_factory=NullLogger)
    logger_param: str | None = None
    parser_cls: type[BaseParser] = Parser
    parser_config: ParserConfiguration | None = None
    respond: RespondFunctionProtocol = default_respond
    responders: "Mapping[str, ResponderProtocol]" = field(
        default_factory=lambda: MappingProxyType({})
    )
    subcommands: "Mapping[str, RuntimeCommand]" = field(
        default_factory=lambda: MappingProxyType({})
    )

    _cached_spec: CommandSpec | None = field(default=None, init=False, repr=False)

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
            f" console={self.console!r},"
            f" console_param={self.console_param!r},"
            f" context_param={self.context_param!r},"
            f" error_config={self.error_config!r},"
            f" is_async={self.is_async!r},"
            f" logger_param={self.logger_param!r},"
            f" parameters={self.parameters!r},"
            f" parser_cls={self.parser_cls!r},"
            f" parser_config={self.parser_config!r},"
            f" responders={self.responders!r},"
            f" run_func={self.run_func!r},"
            f" subcommands={self.subcommands!r},"
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
            console=self.console or DefaultConsole(),
            console_param=self.console_param,
            context_param=self.context_param,
            errors=errors,
            is_async=self.check_async(parse_result),
            logger=self.logger,
            logger_param=self.logger_param,
            parameters=parameters,
            parse_result=parse_result,
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
        self._check_context_errors(context)
        result = self._execute_run_func(context)
        responder = self.respond(result, context, self)
        responder.respond(result, context)

        if subcommand_dispatch := self._prepare_subcommand_dispatch(context):
            subcommand, subcommand_context = subcommand_dispatch
            subcommand.dispatch(subcommand_context)

    async def dispatch_async(self, context: Context) -> None:
        self._check_context_errors(context)
        responder = self.respond(None, context, self)
        result = self._execute_run_func(context)
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

    def _check_context_errors(self, context: Context) -> None:
        if context.errors and context.parse_result.subcommand is None:
            all_errors = self._collect_errors(context)
            raise ValidationError(all_errors)

    def _execute_run_func(self, context: Context) -> ResponseType | None:
        return self.run_func(**self._make_run_parameters(context))

    def _make_run_parameters(self, context: Context) -> CommandFunctionRunParameters:
        run_params: CommandFunctionRunParameters = {}
        run_params.update(context.parameters)
        if self.context_param:
            run_params[self.context_param] = context
        if self.console_param:
            run_params[self.console_param] = context.console
        if self.logger_param:
            run_params[self.logger_param] = context.logger
        return run_params

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
                console_param=self.console_param,
                context_param=self.context_param,
                logger_param=self.logger_param,
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
                    converted[name] = self.converters.convert(
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

            if name not in raw and parameter.is_required:
                errors[name] = ("is required",)
                continue

            value = raw.get(name)
            if value is None and parameter.is_required:
                errors[name] = ("is required",)
                continue
            value_errors: tuple[str, ...] | None = self.validators.validate(
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
