import inspect
import sys
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from dataclasses import dataclass, field
from enum import IntEnum, auto
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Protocol,
    TypeAlias,
    TypedDict,
    cast,
    runtime_checkable,
)
from typing_extensions import override

from aclaf._errors import ErrorConfiguration
from aclaf.exceptions import ConversionError, ValidationError
from aclaf.logging import Logger, NullLogger
from aclaf.validation import (
    ValidatorMetadataType,
    default_command_validators,
    default_parameter_validators,
)

from ._context import Context
from .console import Console, DefaultConsole, SupportsConsole
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
from .types import ParameterValueMappingType, ParameterValueType

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from annotated_types import BaseMetadata

    from aclaf._conversion import ConverterRegistry
    from aclaf._hooks import HookRegistry
    from aclaf.metadata import MetadataByType
    from aclaf.validation import (
        ValidatorFunction,
        ValidatorRegistry,
    )

    from ._conversion import ConverterFunctionType
    from .parser import ParsedParameterValue, ParseResult

DefaultFactoryFunction: TypeAlias = Callable[..., ParameterValueType]


@runtime_checkable
class SupportsPrint(Protocol):
    @override
    def __str__(self) -> str: ...


@runtime_checkable
class SupportsResponse(Protocol):
    def __response__(self, context: "Context") -> None: ...


SupportsResponseType: TypeAlias = SupportsPrint | SupportsConsole | SupportsResponse

SyncResponseType: TypeAlias = (
    SupportsResponseType
    | Generator[SupportsResponseType, None, SupportsResponseType | None]
)

AsyncResponseType: TypeAlias = (
    SupportsResponseType | AsyncGenerator[SupportsResponseType, None]
)

ResponseType: TypeAlias = SyncResponseType | AsyncResponseType

SyncCommandFunctionType: TypeAlias = Callable[..., SyncResponseType]
AsyncCommandFunctionType: TypeAlias = Callable[..., AsyncResponseType]

CommandFunctionType: TypeAlias = SyncCommandFunctionType | AsyncCommandFunctionType

CommandFunctionRunParameters: TypeAlias = dict[
    str, ParameterValueType | None | Context | Console | Logger
]

EMPTY_COMMAND_FUNCTION: CommandFunctionType = lambda: None  # noqa: E731


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


class RuntimeCommandInput(TypedDict, total=False):
    name: str
    run_func: CommandFunctionType
    converters: "ConverterRegistry"
    aliases: tuple[str, ...]
    validations: tuple[ValidatorMetadataType, ...]
    command_validators: "ValidatorRegistry | None"
    console: "Console | None"
    console_param: str | None
    context_param: str | None
    error_config: "ErrorConfiguration"
    hooks: "HookRegistry | None"
    parameter_validators: "ValidatorRegistry | None"
    parameters: "Mapping[str, RuntimeParameter]"
    is_async: bool
    logger: Logger
    logger_param: str | None
    parser_cls: type[BaseParser]
    parser_config: ParserConfiguration | None
    subcommands: "Mapping[str, RuntimeCommand]"


@dataclass(slots=True, frozen=True)
class RuntimeCommand:
    name: str
    run_func: CommandFunctionType
    converters: "ConverterRegistry" = field(repr=False)
    validations: tuple[ValidatorMetadataType, ...] = field(default_factory=tuple)
    aliases: tuple[str, ...] = field(default_factory=tuple)
    command_validators: "ValidatorRegistry | None" = field(repr=False, default=None)
    console: "Console | None" = None
    console_param: str | None = None
    context_param: str | None = None
    error_config: "ErrorConfiguration" = field(default_factory=ErrorConfiguration)
    hooks: "HookRegistry | None" = None
    parameter_validators: "ValidatorRegistry | None" = field(repr=False, default=None)
    parameters: "Mapping[str, RuntimeParameter]" = field(
        default_factory=lambda: MappingProxyType({})
    )
    is_async: bool = False
    logger: Logger = field(default_factory=NullLogger)
    logger_param: str | None = None
    parser_cls: type[BaseParser] = Parser
    parser_config: ParserConfiguration | None = None
    subcommands: "Mapping[str, RuntimeCommand]" = field(
        default_factory=lambda: MappingProxyType({})
    )

    _cached_spec: CommandSpec | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        for attr in ("parameters", "subcommands"):
            value: Mapping[str, RuntimeParameter | RuntimeCommand] = cast(
                "Mapping[str, RuntimeParameter | RuntimeCommand]",
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
            f" run_func={self.run_func!r},"
            f" subcommands={self.subcommands!r},"
            ")"
        )

    def invoke(self, args: "Sequence[str] | None" = None) -> None:
        parse_result = self._parse_arguments(args)
        parameters, conversion_errors = self._convert_parameters(
            parse_result, self.parameters
        )

        errors = self._validate_parameters(
            parameters, self.parameters, conversion_errors, self.validations
        )

        context = self._prepare_root_context(
            args=args or (),
            parse_result=parse_result,
            parameters=parameters,
            errors=errors,
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
        self._respond(result, context)

        if subcommand_dispatch := self._prepare_subcommand_dispatch(context):
            subcommand, subcommand_context = subcommand_dispatch
            subcommand.dispatch(subcommand_context)

    async def dispatch_async(self, context: Context) -> None:
        self._check_context_errors(context)
        result = self._execute_run_func(context)
        if self.is_async:
            if inspect.isasyncgen(result) or inspect.iscoroutine(result):
                await self._respond_async(result, context)
            else:
                msg = "Async command returned non-awaitable result"
                raise TypeError(msg)
        else:
            self._respond(result, context)

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
                parameters,
                subcommand.parameters,
                conversion_errors,
                subcommand.validations,
            )

            subcommand_context = Context(
                command=subcommand.name,
                command_path=(*context.command_path, subcommand.name),
                console=context.console,
                console_param=self.console_param,
                context_param=self.context_param,
                errors=errors,
                logger=context.logger,
                logger_param=self.logger_param,
                parameters=parameters,
                parent=context,
                parse_result=context.parse_result.subcommand,
            )
            return (subcommand, subcommand_context)
        return None

    def _parse_arguments(self, args: "Sequence[str] | None" = None) -> "ParseResult":
        spec = self.to_command_spec()
        parser = self.parser_cls(spec, self.parser_config)
        return parser.parse(args or sys.argv[1:])

    def _convert_parameters(
        self, parse_result: "ParseResult", parameters: "Mapping[str, RuntimeParameter]"
    ) -> tuple[ParameterValueMappingType, dict[str, str]]:
        raw: dict[str, ParsedParameterValue] = {}
        converted: dict[str, ParameterValueType | None] = {}
        errors: dict[str, str] = {}

        for name, parsed in parse_result.options.items():
            raw[name] = parsed.value
        for name, parsed in parse_result.positionals.items():
            raw[name] = parsed.value

        for name, parameter in parameters.items():
            # Check if we should use the default value
            # This happens when:
            # 1. Parameter not in raw (wasn't parsed), OR
            # 2. Parameter is positional with empty value (arity min=0,
            #    no value provided)
            #    - Empty tuple for multi-value arities (max > 1 or unbounded)
            #    - Empty string for single-value arities (max = 1)
            value = raw.get(name)
            should_use_default = name not in raw or (
                parameter.kind == ParameterKind.POSITIONAL
                and parameter.arity is not None
                and parameter.arity.min == 0
                and value in ((), "")
            )

            # Apply default if we should use it
            # Check if a default exists by looking at arity (min=0 implies
            # optional with default) or explicit default/default_factory
            has_default = parameter.default_factory is not None or (
                parameter.arity is not None and parameter.arity.min == 0
            )
            if should_use_default and has_default:
                if parameter.default_factory is not None:
                    converted[name] = parameter.default_factory()
                else:
                    # Use the default value (which can be None)
                    converted[name] = parameter.default
                continue

            type_expr = parameter.value_type
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
        raw: ParameterValueMappingType,
        parameters: "Mapping[str, RuntimeParameter]",
        conversion_errors: dict[str, str],
        validations: tuple[ValidatorMetadataType, ...] | None = None,
    ) -> dict[str, tuple[str, ...]]:
        command_validators = self.command_validators or default_command_validators()
        parameter_validators = (
            self.parameter_validators or default_parameter_validators()
        )

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

            # Skip validation for None values (optional parameters)
            if value is None:
                continue

            value_errors: tuple[str, ...] | None = parameter_validators.validate(
                value, parameter.metadata
            )

            if value_errors:
                errors[name] = tuple(value_errors)

        command_validations = (
            validations if validations is not None else self.validations
        )
        command_errors = command_validators.validate(raw, command_validations)
        if command_errors:
            errors["__command__"] = command_errors

        return errors

    def _prepare_root_context(
        self,
        args: "Sequence[str]",
        parse_result: "ParseResult",
        parameters: ParameterValueMappingType,
        errors: dict[str, tuple[str, ...]],
    ) -> Context:
        return Context(
            args=tuple(args),
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

    def _respond(self, result: "SyncResponseType | None", context: "Context") -> None:
        if result is None:
            return

        if inspect.isgenerator(result):
            try:
                while True:
                    value = cast("SupportsResponseType | None", next(result))
                    if value is not None:
                        self._render_value(value, context)
            except StopIteration as stop:
                stop_value = cast("SupportsResponseType | None", stop.value)
                if stop_value is not None:
                    self._render_value(stop_value, context)
        elif result is not None:
            self._render_value(result, context)

    async def _respond_async(
        self, result: "AsyncResponseType | None", context: "Context"
    ) -> None:
        if result is None:
            return

        if inspect.isasyncgen(result):
            async_gen = cast("AsyncGenerator[SupportsResponseType, None]", result)
            async for value in async_gen:
                if value is not None:
                    self._render_value(value, context)
        elif inspect.iscoroutine(result):
            coroutine = cast(
                "Coroutine[object, object, SupportsResponseType | None]", result
            )
            awaited_result = await coroutine
            if awaited_result is not None:
                self._render_value(awaited_result, context)
        elif result is not None:
            self._render_value(result, context)

    def _render_value(
        self,
        value: SupportsResponseType | None,
        context: "Context",
    ) -> None:
        if value is None:
            return

        if isinstance(value, SupportsConsole):
            value.__console__(context.console)
        elif isinstance(value, SupportsResponse):
            value.__response__(context)
        else:
            context.console.print(value)

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
