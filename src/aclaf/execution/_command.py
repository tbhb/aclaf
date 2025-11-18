import inspect
import sys
from dataclasses import dataclass, field
from enum import IntEnum, auto
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    TypedDict,
    cast,
)
from typing_extensions import override

from aclaf.console import Console, DefaultConsole, SupportsConsole
from aclaf.exceptions import ConversionError, ValidationError
from aclaf.logging import Logger, NullLogger
from aclaf.parser import (
    BaseParser,
    CommandSpec,
    Parser,
    ParserConfiguration,
)
from aclaf.types import ParameterValueType
from aclaf.validation import (
    ValidatorMetadataType,
    default_command_validators,
    default_parameter_validators,
)

from ._context import Context

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Coroutine, Mapping, Sequence

    from aclaf._hooks import HookRegistry
    from aclaf.conversion import ConverterRegistry
    from aclaf.parser import ParsedParameterValue, ParseResult
    from aclaf.response import (
        AsyncResponseType,
        ResponseType,
        SyncResponseType,
    )
    from aclaf.types import ParameterValueMappingType
    from aclaf.validation import (
        ValidatorRegistry,
    )

    from ._parameter import RuntimeParameter
    from ._types import CommandFunctionType

CommandFunctionRunParameters = dict[
    str, ParameterValueType | None | Context | Console | Logger
]

EMPTY_COMMAND_FUNCTION: "CommandFunctionType" = lambda: None  # noqa: E731


class ParameterKind(IntEnum):
    OPTION = auto()
    POSITIONAL = auto()


class RuntimeCommandInput(TypedDict, total=False):
    name: str
    run_func: "CommandFunctionType"
    converters: "ConverterRegistry"
    aliases: tuple[str, ...]
    validations: tuple[ValidatorMetadataType, ...]
    command_validators: "ValidatorRegistry | None"
    console: "Console | None"
    console_param: str | None
    context_param: str | None
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
    run_func: "CommandFunctionType"
    converters: "ConverterRegistry" = field(repr=False)
    validations: tuple[ValidatorMetadataType, ...] = field(default_factory=tuple)
    aliases: tuple[str, ...] = field(default_factory=tuple)
    command_validators: "ValidatorRegistry | None" = field(repr=False, default=None)
    console: "Console | None" = None
    console_param: str | None = None
    context_param: str | None = None
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
    def options(self) -> MappingProxyType[str, "RuntimeParameter"]:
        return MappingProxyType(
            {k: v for k, v in self.parameters.items() if v.kind == ParameterKind.OPTION}
        )

    @property
    def positionals(self) -> MappingProxyType[str, "RuntimeParameter"]:
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
        # TODO(tbhb): AroundInvocationHook
        # TODO(tbhb): BeforeInvocationHook
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
        # TODO(tbhb): AfterInvocationHook
        # TODO(tbhb): InvocationErrorHook

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

    def _execute_run_func(self, context: Context) -> "ResponseType | None":
        # TODO(tbhb): AroundExecutionHook
        # TODO(tbhb): BeforeExecutionHook
        return self.run_func(**self._make_run_parameters(context))
        # TODO(tbhb): AfterExecutionHook
        # TODO(tbhb): ExecutionErrorHook

    def _make_run_parameters(self, context: Context) -> "CommandFunctionRunParameters":
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
        # TODO(tbhb): AroundSubcommandDispatchHook
        # TODO(tbhb): BeforeSubcommandDispatchHook
        if (
            self.subcommands
            and context.parse_result.subcommand
            and context.parse_result.subcommand.command
        ):
            # TODO(tbhb): Should all of this just use regular dispatch on
            # the subcommand?
            subcommand_name = context.parse_result.subcommand.command
            subcommand = self.subcommands[subcommand_name]

            parameters, conversion_errors = subcommand._convert_parameters(  # noqa: SLF001
                context.parse_result.subcommand, subcommand.parameters
            )
            errors = subcommand._validate_parameters(  # noqa: SLF001
                parameters,
                subcommand.parameters,
                conversion_errors,
                subcommand.validations,
            )

            # TODO(tbhb): AroundSubcommandContextSetupHook
            # TODO(tbhb): BeforeSubcommandContextSetupHook
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
            # TODO(tbhb): AfterSubcommandContextSetupHook
            # TODO(tbhb): SubcommandContextSetupErrorHook
            return (subcommand, subcommand_context)
        return None
        # TODO(tbhb): AfterSubcommandDispatchHook
        # TODO(tbhb): SubcommandDispatchErrorHook

    def _parse_arguments(self, args: "Sequence[str] | None" = None) -> "ParseResult":
        # TODO(tbhb): AroundParsingHook
        # TODO(tbhb): BeforeParsingHook
        spec = self.to_command_spec()
        parser = self.parser_cls(spec, self.parser_config)
        return parser.parse(args or sys.argv[1:])
        # TODO(tbhb): AfterParsingHook
        # TODO(tbhb): ParsingErrorHook

    def _convert_parameters(
        self, parse_result: "ParseResult", parameters: "Mapping[str, RuntimeParameter]"
    ) -> tuple["ParameterValueMappingType", dict[str, str]]:
        # TODO(tbhb): AroundConversionHook
        # TODO(tbhb): BeforeConversionHook
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
                and parameter.arity.min == 0
                and value in ((), "")
            )

            # Apply default if we should use it
            # Check if a default exists by looking at arity (min=0 implies
            # optional with default) or explicit default/default_factory
            has_default = (
                parameter.default_factory is not None or parameter.arity.min == 0
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
        # TODO(tbhb): AfterConversionHook
        # TODO(tbhb): ConversionErrorHook

    def _validate_parameters(
        self,
        raw: "ParameterValueMappingType",
        parameters: "Mapping[str, RuntimeParameter]",
        conversion_errors: dict[str, str],
        validations: tuple[ValidatorMetadataType, ...] | None = None,
    ) -> dict[str, tuple[str, ...]]:
        # TODO(tbhb): AroundValidationHook
        # TODO(tbhb): BeforeValidationHook
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
        # TODO(tbhb): AfterValidationHook
        # TODO(tbhb): ValidationErrorHook

    def _prepare_root_context(
        self,
        args: "Sequence[str]",
        parse_result: "ParseResult",
        parameters: "ParameterValueMappingType",
        errors: dict[str, tuple[str, ...]],
    ) -> Context:
        # TODO(tbhb): AroundContextSetupHook
        # TODO(tbhb): BeforeContextSetupHook
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
        # TODO(tbhb): AfterContextSetupHook
        # TODO(tbhb): ContextSetupErrorHook

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
        # TODO(tbhb): AroundResponseHook
        # TODO(tbhb): BeforeResponseHook
        if result is None:
            return

        if inspect.isgenerator(result):
            try:
                while True:
                    value = cast("ResponseType | None", next(result))
                    if value is not None:
                        self._render_value(value, context)
                        # TODO(tbhb): AfterResponseYieldedHook
            except StopIteration as stop:
                stop_value = cast("ResponseType | None", stop.value)
                if stop_value is not None:
                    self._render_value(stop_value, context)
                    # TODO(tbhb): AfterResponseHook
        elif result is not None:
            self._render_value(result, context)
            # TODO(tbhb): AfterResponseHook

    async def _respond_async(
        self, result: "AsyncResponseType | None", context: "Context"
    ) -> None:
        # TODO(tbhb): AroundResponseHookAsync
        # TODO(tbhb): BeforeResponseHookAsync
        if result is None:
            return

        if inspect.isasyncgen(result):
            async_gen = cast("AsyncGenerator[ResponseType, None]", result)
            async for value in async_gen:
                if value is not None:
                    self._render_value(value, context)
                    # TODO(tbhb): AfterResponseYieldedHookAsync
        elif inspect.iscoroutine(result):
            coroutine = cast("Coroutine[object, object, ResponseType | None]", result)
            awaited_result = await coroutine
            if awaited_result is not None:
                self._render_value(awaited_result, context)
            # TODO(tbhb): AfterResponseHookAsync
        elif result is not None:
            self._render_value(result, context)
            # TODO(tbhb): AfterResponseHookAsync

    def _render_value(
        self,
        value: "ResponseType | None",
        context: "Context",
    ) -> None:
        if value is None:
            return

        if isinstance(value, SupportsConsole):
            value.__console__(context.console)
        else:
            context.console.print(value)

    def to_command_spec(self) -> CommandSpec:
        # TODO(tbhb): AroundCommandSpecConversionHook
        # TODO(tbhb): BeforeCommandSpecConversionHook
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
        # TODO(tbhb): AfterCommandSpecConversionHook
        # TODO(tbhb): CommandSpecConversionErrorHook


def is_async_command_function(
    func: "CommandFunctionType",
) -> bool:
    return bool(inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func))
