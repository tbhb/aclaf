from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aclaf.parser.types import ParsedParameterValue


class AclafError(Exception):
    """Base exception for all Aclaf-related errors."""

    def __init__(
        self,
        message: str | None = None,
        detail: str | None = None,
        suggestions: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.detail: str | None = detail
        self.suggestions: list[str] | None = suggestions


class RegistrationError(AclafError):
    """Base exception for errors during command or parameter registration."""

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified registration error occurred."
        super().__init__(message, detail=detail)


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


class ExecutionError(AclafError):
    """Raised when an error occurs during command execution."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified execution error occurred."
        super().__init__(message, detail=detail)


class ResponseError(AclafError):
    """Raised when an error occurs while sending a response."""

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified response error occurred."
        super().__init__(message, detail=detail)
