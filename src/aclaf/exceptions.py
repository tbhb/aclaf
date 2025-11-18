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
