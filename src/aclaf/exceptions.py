from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aclaf.parser.types import ParsedParameterValue


class AclafError(Exception):
    """Base exception for all Aclaf-related errors."""


class CommandFunctionAlreadyDefinedError(AclafError):
    """Raised when attempting to create more than one root command in an application."""


class DefaultFactoryError(AclafError):
    """Raised when there is an error invoking a default factory."""

    def __init__(self, command_name: str, param_name: str):
        self.command_name: str = command_name
        self.param_name: str = param_name
        msg = (
            f"Error invoking default factory for parameter '{param_name}'"
            f" in command '{command_name}'."
        )
        super().__init__(msg)


class DuplicateCommandError(AclafError):
    """Raised when attempting to register a command with a name that is already in use."""  # noqa: E501

    def __init__(self, command_name: str):
        self.command_name: str = command_name
        msg = f"Command with name '{command_name}' is already registered."
        super().__init__(msg)


class ConversionError(AclafError):
    def __init__(
        self,
        value: "ParsedParameterValue",
        target_type: type,
        reason: str | None = None,
    ) -> None:
        self.value: ParsedParameterValue = value
        self.target_type: type = target_type
        self.reason: str | None = reason
        msg = f"Failed to convert value '{value}' to type '{target_type.__name__}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)


class ValidationError(AclafError):
    def __init__(self, errors: dict[str, dict[str, tuple[str, ...]]]) -> None:
        super().__init__("Validation failed")
        self.errors: dict[str, dict[str, tuple[str, ...]]] = errors
