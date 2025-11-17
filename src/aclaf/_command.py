from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    TypedDict,
)
from typing_extensions import override

from aclaf._conversion import ConverterFunctionType, ConverterRegistry
from aclaf._errors import ErrorConfiguration
from aclaf._parameters import (
    CommandParameter,
    Parameter,
    extract_function_parameters,
)
from aclaf._validation import (
    ParameterValidatorFunctionType,
    ParameterValidatorRegistry,
    ValidatorRegistryKey,
)
from aclaf.console import Console
from aclaf.logging import Logger, NullLogger

from ._runtime import (
    EMPTY_COMMAND_FUNCTION,
    ParameterKind,
    RespondFunctionProtocol,
    RuntimeCommand,
    default_respond,
    is_async_command_function,
)
from .exceptions import CommandFunctionAlreadyDefinedError, DuplicateCommandError
from .parser.utils import validate_command_name

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from ._response import ResponderProtocol
    from ._runtime import CommandFunctionType
    from .parser import ParserConfiguration


class CommandInput(TypedDict, total=False):
    name: str
    aliases: "Iterable[str]"
    console_param: "str | None"
    context_param: "str | None"
    converters: ConverterRegistry
    error_config: "ErrorConfiguration"
    is_async: bool
    is_mounted: bool
    logger: Logger
    logger_param: "str | None"
    parameters: dict[str, "Parameter"]
    parent_command: "Command | None"
    parser_config: "ParserConfiguration | None"
    respond: RespondFunctionProtocol
    responders: dict[str, "ResponderProtocol"]
    root_command: "Command | None"
    run_func: "CommandFunctionType | None"
    subcommands: dict[str, "Command"]
    validators: ParameterValidatorRegistry


@dataclass(slots=True)
class Command:
    name: str
    aliases: "Iterable[str]" = field(default_factory=tuple)
    console: "Console | None" = None
    console_param: "str | None" = None
    context_param: "str | None" = None
    converters: ConverterRegistry = field(default_factory=ConverterRegistry, repr=False)
    error_config: "ErrorConfiguration" = field(default_factory=ErrorConfiguration)
    is_async: bool = False
    is_mounted: bool = False
    logger: Logger = field(default_factory=NullLogger)
    logger_param: "str | None" = None
    parameters: dict[str, "Parameter"] = field(default_factory=dict)
    parent_command: "Command | None" = None
    parser_config: "ParserConfiguration | None" = None
    respond: RespondFunctionProtocol = default_respond
    responders: dict[str, "ResponderProtocol"] = field(default_factory=dict)
    root_command: "Command | None" = None
    run_func: "CommandFunctionType | None" = None
    subcommands: dict[str, "Command"] = field(default_factory=dict)
    validators: ParameterValidatorRegistry = field(
        default_factory=ParameterValidatorRegistry, repr=False
    )

    def __post_init__(self) -> None:
        validate_command_name(self.name)

        if self.run_func is not None:
            self.is_async = self._check_run_func_async()

        self.converters.logger = self.logger
        self.validators.logger = self.logger

    @property
    def command_parameters(self) -> dict[str, "CommandParameter"]:
        return {
            name: param
            for name, param in self.parameters.items()
            if isinstance(param, CommandParameter)
        }

    @property
    def options(self) -> dict[str, "CommandParameter"]:
        return {
            name: param
            for name, param in self.command_parameters.items()
            if param.kind == ParameterKind.OPTION
        }

    @property
    def positionals(self) -> dict[str, "CommandParameter"]:
        return {
            name: param
            for name, param in self.command_parameters.items()
            if param.kind == ParameterKind.POSITIONAL
        }

    @override
    def __repr__(self) -> str:
        return (
            f"Command(name={self.name!r},"
            f" aliases={self.aliases!r},"
            f" console={self.console!r},"
            f" console_param={self.console_param!r},"
            f" context_param={self.context_param!r},"
            f" error_config={self.error_config!r},"
            f" is_async={self.is_async!r},"
            f" is_mounted={self.is_mounted!r},"
            f" logger={self.logger!r},"
            f" logger_param={self.logger_param!r},"
            f" parameters={self.parameters!r},"
            f" parent_command={self.parent_command!r},"
            f" parser_config={self.parser_config!r},"
            f" respond={self.respond!r},"
            f" responders={self.responders!r},"
            f" root_command={self.root_command!r},"
            f" run_func={self.run_func!r},"
            f" subcommands={self.subcommands!r}"
            ")"
        )

    def mounted_commands(self) -> list[str]:
        return [
            name for name, command in self.subcommands.items() if command.is_mounted
        ]

    def non_mounted_commands(self) -> list[str]:
        return [
            name for name, command in self.subcommands.items() if not command.is_mounted
        ]

    def __call__(self, args: "Sequence[str] | None" = None) -> None:
        self.to_runtime_command().invoke(args)

    def to_runtime_command(
        self, responders: dict[str, "ResponderProtocol"] | None = None
    ) -> "RuntimeCommand":
        run_func = self.run_func or (EMPTY_COMMAND_FUNCTION)
        if self.is_async is None:
            self.is_async = self._check_run_func_async()

        parameters = {
            name: param.to_runtime_parameter()
            for name, param in self.command_parameters.items()
        }

        return RuntimeCommand(
            name=self.name,
            aliases=tuple(self.aliases),
            console=self.console,
            error_config=self.error_config,
            logger=self.logger,
            parameters=parameters,
            parser_config=self.parser_config,
            respond=self.respond,
            responders=(responders if responders else {}) | self.responders,
            run_func=run_func,
            subcommands={
                name: cmd_builder.to_runtime_command(self.responders)
                for name, cmd_builder in self.subcommands.items()
            },
            is_async=self.is_async,
            converters=self.converters,
            validators=self.validators,
            console_param=self.console_param,
            context_param=self.context_param,
            logger_param=self.logger_param,
        )

    def _check_run_func_async(self) -> bool:
        if self.run_func is None:
            return False
        return is_async_command_function(self.run_func)

    def handler(
        self,
        name: str | None = None,
        *,
        aliases: tuple[str, ...] | None = None,
    ) -> "Callable[[CommandFunctionType], Command]":
        if self.run_func is not None:
            raise CommandFunctionAlreadyDefinedError()

        def decorator(
            func: "CommandFunctionType",
        ) -> "Command":
            parameters, special_parameters = extract_function_parameters(func)
            self.name = name or self.name or func.__name__
            self.aliases = aliases or self.aliases
            self.parameters = parameters
            self.run_func = func
            self.is_async = self._check_run_func_async()
            self.context_param = special_parameters.get("context")
            self.console_param = special_parameters.get("console")
            self.logger_param = special_parameters.get("logger")
            return self

        return decorator

    def command(
        self,
        name: str | None = None,
        *,
        aliases: "Iterable[str] | None" = None,
    ) -> "Callable[[CommandFunctionType], Command]":
        def decorator(
            func: "CommandFunctionType",
        ) -> "Command":
            parameters, special_parameters = extract_function_parameters(func)
            cmd_name = name or func.__name__
            command = Command(
                aliases=aliases or (),
                console_param=special_parameters.get("console"),
                context_param=special_parameters.get("context"),
                converters=self.converters,
                is_async=is_async_command_function(func),
                logger=self.logger,
                logger_param=special_parameters.get("logger"),
                name=cmd_name,
                parameters=parameters,
                parent_command=self,
                parser_config=self.parser_config,
                root_command=self.root_command or self,
                run_func=func,
                validators=self.validators,
            )
            self._add_subcommand(cmd_name, command)
            return command

        return decorator

    def mount(
        self,
        command: "Command",
        *,
        name: str | None = None,
        ignore_existing: bool = False,
    ) -> "Command":
        name = name or command.name
        command.name = name
        command.parent_command = self
        # TODO(tony): All of this needs to cascade recursively to subcommands of the
        # mounted command
        command.root_command = self.root_command or self
        command.is_mounted = True
        command.validators = self.validators
        command.converters = self.converters
        command.logger = self.logger

        if ignore_existing and name in self.subcommands:
            del self.subcommands[name]

        self._add_subcommand(name, command)
        return command

    def _add_subcommand(self, name: str, command: "Command") -> None:
        if name in self.subcommands:
            raise DuplicateCommandError(name)
        self.subcommands[name] = command

    def converter(
        self, type_: type
    ) -> "Callable[[ConverterFunctionType], ConverterFunctionType]":
        def decorator(
            func: "ConverterFunctionType",
        ) -> "ConverterFunctionType":
            self.converters.register(type_, func)
            return func

        return decorator

    def validator(
        self, key: ValidatorRegistryKey
    ) -> "Callable[[ParameterValidatorFunctionType], ParameterValidatorFunctionType]":
        def decorator(
            func: "ParameterValidatorFunctionType",
        ) -> "ParameterValidatorFunctionType":
            self.validators.register(key, func)
            return func

        return decorator
