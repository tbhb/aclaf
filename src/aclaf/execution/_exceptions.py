from aclaf.exceptions import AclafError


class ExecutionError(AclafError):
    """Raised when an error occurs during command execution."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified execution error occurred."
        super().__init__(message, detail=detail)


class DefaultFactoryError(ExecutionError):
    """Raised when there is an error invoking a default factory."""

    def __init__(self, command_name: str, param_name: str):
        self.command_name: str = command_name
        self.param_name: str = param_name
        msg = (
            f"Error invoking default factory for parameter '{param_name}'"
            f" in command '{command_name}'."
        )
        super().__init__(msg)
