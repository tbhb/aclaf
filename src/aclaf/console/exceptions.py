from aclaf.exceptions import AclafError


class ConsoleError(AclafError):
    """Base exception for errors during console operations."""

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified console error occurred."
        super().__init__(message, detail=detail)
