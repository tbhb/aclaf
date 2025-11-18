from aclaf.exceptions import AclafError


class RegistrationError(AclafError):
    """Base exception for errors during command or parameter registration."""

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified registration error occurred."
        super().__init__(message, detail=detail)


class CommandFunctionAlreadyDefinedError(RegistrationError):
    """Raised when attempting to create more than one root command in an application."""


class DuplicateCommandError(RegistrationError):
    """Raised when attempting to register a command with a name that is already in use."""  # noqa: E501

    def __init__(self, command_name: str):
        self.command_name: str = command_name
        msg = f"Command with name '{command_name}' is already registered."
        super().__init__(msg)
