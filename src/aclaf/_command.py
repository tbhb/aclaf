from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    TypedDict,
)
from typing_extensions import override

from aclaf._conversion import ConverterFunctionType, ConverterRegistry
from aclaf._errors import ErrorConfiguration
from aclaf._hooks import Hook, HookRegistry
from aclaf._parameters import (
    CommandParameter,
    Parameter,
    extract_function_parameters,
)
from aclaf.logging import Logger, NullLogger
from aclaf.validation import default_command_validators, default_parameter_validators

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

# Maximum depth allowed for command hierarchy to prevent infinite recursion
MAX_COMMAND_HIERARCHY_DEPTH = 900

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from aclaf.console import Console
    from aclaf.validation import (
        ValidatorFunction,
        ValidatorMetadataType,
        ValidatorRegistry,
        ValidatorRegistryKey,
    )

    from ._response import ResponderProtocol
    from ._runtime import CommandFunctionType
    from .parser import ParserConfiguration


class CommandInput(TypedDict, total=False):
    name: str
    aliases: "Iterable[str]"
    command_validators: "ValidatorRegistry | None"
    console: "Console | None"
    console_param: "str | None"
    context_param: "str | None"
    converters: ConverterRegistry
    error_config: "ErrorConfiguration"
    is_async: bool
    is_mounted: bool
    logger: Logger
    logger_param: "str | None"
    parameter_validators: "ValidatorRegistry | None"
    parameters: dict[str, "Parameter"]
    parent_command: "Command | None"
    parser_config: "ParserConfiguration | None"
    respond: RespondFunctionProtocol
    responders: dict[str, "ResponderProtocol"]
    root_command: "Command | None"
    run_func: "CommandFunctionType | None"
    subcommands: dict[str, "Command"]
    validations: "Sequence[ValidatorMetadataType]"


@dataclass(slots=True)
class Command:
    name: str
    aliases: "Iterable[str]" = field(default_factory=tuple)
    command_validators: "ValidatorRegistry | None" = None
    console: "Console | None" = None
    console_param: "str | None" = None
    context_param: "str | None" = None
    converters: ConverterRegistry = field(default_factory=ConverterRegistry, repr=False)
    error_config: "ErrorConfiguration" = field(default_factory=ErrorConfiguration)
    hooks: "HookRegistry | None" = None
    is_async: bool = False
    is_mounted: bool = False
    logger: Logger = field(default_factory=NullLogger)
    logger_param: "str | None" = None
    parameter_validators: "ValidatorRegistry | None" = None
    parameters: dict[str, "Parameter"] = field(default_factory=dict)
    parent_command: "Command | None" = None
    parser_config: "ParserConfiguration | None" = None
    respond: RespondFunctionProtocol = default_respond
    responders: dict[str, "ResponderProtocol"] = field(default_factory=dict)
    root_command: "Command | None" = None
    run_func: "CommandFunctionType | None" = None
    subcommands: dict[str, "Command"] = field(default_factory=dict)
    validations: list["ValidatorMetadataType"] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_command_name(self.name)

        if self.run_func is not None:
            self.is_async = self._check_run_func_async()

        self.converters.logger = self.logger

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
            f" subcommands={self.subcommands!r},"
            f" validations={self.validations!r},"
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

        parameters = {
            name: param.to_runtime_parameter()
            for name, param in self.command_parameters.items()
        }

        return RuntimeCommand(
            name=self.name,
            aliases=tuple(self.aliases),
            command_validators=self.command_validators,
            console=self.console,
            error_config=self.error_config,
            hooks=self.hooks,
            logger=self.logger,
            parameter_validators=self.parameter_validators,
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
            console_param=self.console_param,
            context_param=self.context_param,
            logger_param=self.logger_param,
            validations=tuple(self.validations),
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
                command_validators=self.command_validators,
                console_param=special_parameters.get("console"),
                context_param=special_parameters.get("context"),
                converters=self.converters,
                is_async=is_async_command_function(func),
                logger=self.logger,
                logger_param=special_parameters.get("logger"),
                name=cmd_name,
                parameter_validators=self.parameter_validators,
                parameters=parameters,
                parent_command=self,
                parser_config=self.parser_config,
                root_command=self.root_command or self,
                run_func=func,
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
        command.is_mounted = True

        if ignore_existing and name in self.subcommands:
            del self.subcommands[name]

        self._add_subcommand(name, command)
        self._cascade_config_recursive(command)
        return command

    def _add_subcommand(self, name: str, command: "Command") -> None:
        if name in self.subcommands:
            raise DuplicateCommandError(name)
        self.subcommands[name] = command

    def _cascade_config_to_command(self, command: "Command") -> None:
        """Apply this command's configuration to the target command.

        This merges the parent command's configuration into the child command.
        For converters and validators, parent values are merged INTO child
        registries, with child values taking precedence (child wins).

        Configuration that is merged:
        - Converters: Parent converters added to child, child converters
          preserved
        - Command validators: Parent validators added to child, child
          validators preserved
        - Parameter validators: Parent validators added to child, child
          validators preserved
        - Logger: Set to parent's logger if child has default logger
        - Parser config: Set to parent's parser config if child has none
        - Root command: Set to parent's root (or parent itself)

        Args:
            command: The command to cascade configuration to.
        """
        command.root_command = self.root_command or self

        # Merge parent's converters into child's registry (child wins)
        command.converters.merge_from(self.converters)

        # Merge parent's command validators into child's registry (child wins)
        if self.command_validators is not None:
            if command.command_validators is None:
                command.command_validators = default_command_validators()
            command.command_validators.merge_from(self.command_validators)

        # Merge parent's parameter validators into child's registry (child wins)
        if self.parameter_validators is not None:
            if command.parameter_validators is None:
                command.parameter_validators = default_parameter_validators()
            command.parameter_validators.merge_from(self.parameter_validators)

        # Always set logger to parent's logger for consistent logging
        command.logger = self.logger

        # Set parser config if child doesn't have one
        if command.parser_config is None:
            command.parser_config = self.parser_config

    def _cascade_config_recursive(self, command: "Command", depth: int = 0) -> None:
        """Cascade configuration from this command to a target and its subcommands.

        This method recursively applies this command's configuration to the target
        command and all of its nested subcommands. Configuration is merged using
        a "child wins" strategy where child-specific converters and validators
        are preserved.

        Configuration that is merged:
        - Converters: Parent converters added to child, child converters preserved
        - Validators: Parent validators added to child, child validators preserved
        - Logger: Set to parent's logger if child has default logger
        - Parser config: Set to parent's parser config if child has none
        - Root command: Set to parent's root (or parent itself)

        Hooks are intentionally NOT cascaded as they should remain command-specific.

        Args:
            command: The command to cascade configuration to (must be a direct
                subcommand of self).
            depth: Current recursion depth (internal use only).

        Raises:
            RecursionError: If the command hierarchy exceeds the maximum depth,
                indicating a potentially infinite recursion or excessively deep
                command structure.
        """
        if depth > MAX_COMMAND_HIERARCHY_DEPTH:
            msg = (
                f"Command hierarchy exceeds maximum depth of "
                f"{MAX_COMMAND_HIERARCHY_DEPTH} levels. "
                f"This indicates either an excessively deep command structure or "
                f"a circular reference in the command tree."
            )
            raise RecursionError(msg)

        self._cascade_config_to_command(command)

        for subcommand in command.subcommands.values():
            self._cascade_config_recursive(subcommand, depth + 1)

    def converter(
        self, type_: type
    ) -> "Callable[[ConverterFunctionType], ConverterFunctionType]":
        def decorator(
            func: "ConverterFunctionType",
        ) -> "ConverterFunctionType":
            self.converters.register(type_, func)
            return func

        return decorator

    def command_validator(
        self, key: "ValidatorRegistryKey"
    ) -> "Callable[[ValidatorFunction], ValidatorFunction]":
        def decorator(
            func: "ValidatorFunction",
        ) -> "ValidatorFunction":
            if self.command_validators is None:
                self.command_validators = default_command_validators()
            # Capture in local variable for type narrowing
            validators = self.command_validators
            validators.register(key, func)
            return func

        return decorator

    def parameter_validator(
        self, key: "ValidatorRegistryKey"
    ) -> "Callable[[ValidatorFunction], ValidatorFunction]":
        def decorator(
            func: "ValidatorFunction",
        ) -> "ValidatorFunction":
            if self.parameter_validators is None:
                self.parameter_validators = default_parameter_validators()
            # Capture in local variable for type narrowing
            validators = self.parameter_validators
            validators.register(key, func)
            return func

        return decorator

    def validate(self, *validations: "ValidatorMetadataType") -> None:
        self.validations.extend(validations)

    def hook(self, hook: "Hook") -> None:
        if self.hooks is None:
            self.hooks = HookRegistry()
        self.hooks.register(hook)
