from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    TypedDict,
)
from typing_extensions import override

from aclaf.conversion import ConverterFunctionType, ConverterRegistry
from aclaf.execution import (
    EMPTY_COMMAND_FUNCTION,
    Hook,
    HookRegistry,
    RuntimeCommand,
    is_async_command_function,
)
from aclaf.logging import Logger, NullLogger
from aclaf.parser import validate_command_name
from aclaf.types import ParameterKind
from aclaf.validation import default_command_validators, default_parameter_validators

from ._exceptions import (
    CommandFunctionAlreadyDefinedError,
    DuplicateCommandError,
)
from ._parameters import (
    CommandParameter,
    Parameter,
    extract_function_parameters,
)

# Maximum depth allowed for command hierarchy to prevent infinite recursion
MAX_COMMAND_HIERARCHY_DEPTH = 900

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from aclaf.console import Console
    from aclaf.execution import CommandFunctionType
    from aclaf.parser import ParserConfiguration
    from aclaf.validation import (
        ValidatorFunction,
        ValidatorMetadataType,
        ValidatorRegistry,
        ValidatorRegistryKey,
    )


class CommandInput(TypedDict, total=False):
    name: str
    aliases: "Iterable[str]"
    command_validators: "ValidatorRegistry | None"
    console: "Console | None"
    console_param: "str | None"
    context_param: "str | None"
    converters: ConverterRegistry
    is_async: bool
    is_mounted: bool
    logger: Logger
    logger_param: "str | None"
    parameter_validators: "ValidatorRegistry | None"
    parameters: dict[str, "Parameter"]
    parent_command: "Command | None"
    parser_config: "ParserConfiguration | None"
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
    hooks: "HookRegistry | None" = None
    is_async: bool = False
    is_mounted: bool = False
    logger: Logger = field(default_factory=NullLogger)
    logger_param: "str | None" = None
    parameter_validators: "ValidatorRegistry | None" = None
    parameters: dict[str, "Parameter"] = field(default_factory=dict)
    parent_command: "Command | None" = None
    parser_config: "ParserConfiguration | None" = None
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
            f" is_async={self.is_async!r},"
            f" is_mounted={self.is_mounted!r},"
            f" logger={self.logger!r},"
            f" logger_param={self.logger_param!r},"
            f" parameters={self.parameters!r},"
            f" parent_command={self.parent_command!r},"
            f" parser_config={self.parser_config!r},"
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

    def to_runtime_command(self) -> "RuntimeCommand":
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
            hooks=self.hooks,
            logger=self.logger,
            parameter_validators=self.parameter_validators,
            parameters=parameters,
            parser_config=self.parser_config,
            run_func=run_func,
            subcommands={
                name: cmd_builder.to_runtime_command()
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

        This intelligently shares or merges the parent command's configuration
        with the child command:

        - If child has custom (non-builtin) converters: merge parent converters
          into child's registry (child wins)
        - If child has only builtin converters: share parent's registry directly
        - Validators are always shared by reference
        - Logger is always set to parent's logger
        - Parser config is set if child has none

        Configuration that is shared/cascaded:
        - Converters: Shared if child has no custom converters, merged otherwise
        - Command validators: Shared by reference
        - Parameter validators: Shared by reference
        - Logger: Set to parent's logger
        - Parser config: Set to parent's parser config if child has none
        - Root command: Set to parent's root (or parent itself)

        Args:
            command: The command to cascade configuration to.
        """
        command.root_command = self.root_command or self

        # Determine if child has custom converters beyond builtins
        child_has_custom_converters = self._has_custom_converters(command.converters)

        if child_has_custom_converters:
            # Child has custom converters - merge parent's into child's (child wins)
            command.converters.merge_from(self.converters)
            # Update child's converter logger to match parent logger
            command.converters.logger = self.logger
        else:
            # Child has only builtins - share parent's registry directly
            command.converters = self.converters

        # Handle command validators - share or merge based on child state
        if self.command_validators is not None:
            if command.command_validators is not None:
                # Child has custom validators - merge parent's into child's
                command.command_validators.merge_from(self.command_validators)
                command.command_validators.logger = self.logger
            else:
                # Child has no validators - share parent's registry
                command.command_validators = self.command_validators

        # Handle parameter validators - share or merge based on child state
        if self.parameter_validators is not None:
            if command.parameter_validators is not None:
                # Child has custom validators - merge parent's into child's
                command.parameter_validators.merge_from(self.parameter_validators)
                command.parameter_validators.logger = self.logger
            else:
                # Child has no validators - share parent's registry
                command.parameter_validators = self.parameter_validators

        # Always set logger to parent's logger for consistent logging
        command.logger = self.logger

        # Set parser config if child doesn't have one
        if command.parser_config is None:
            command.parser_config = self.parser_config

    def _has_custom_converters(self, registry: ConverterRegistry) -> bool:
        """Check if a converter registry has custom (non-builtin) converters.

        Args:
            registry: The converter registry to check

        Returns:
            True if the registry has converters beyond the standard builtins
        """
        builtin_types = {str, int, float, bool, Path}
        return any(type_ not in builtin_types for type_ in registry.converters)

    def _cascade_config_recursive(self, command: "Command", depth: int = 0) -> None:
        """Cascade configuration from this command to a target and its subcommands.

        This method recursively shares this command's configuration with the target
        command and all of its nested subcommands. Registries are shared by reference,
        ensuring that changes to parent registries are visible to all children.

        Configuration that is shared/cascaded:
        - Converters: Child uses parent's ConverterRegistry (shared reference)
        - Command validators: Child uses parent's ValidatorRegistry (shared reference)
        - Parameter validators: Child uses parent's ValidatorRegistry (shared reference)
        - Logger: Set to parent's logger
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
