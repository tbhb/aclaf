from aclaf.exceptions import AclafError


class ResponseError(AclafError):
    """Raised when an error occurs while sending a response."""

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified response error occurred."
        super().__init__(message, detail=detail)
