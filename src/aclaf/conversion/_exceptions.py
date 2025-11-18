from typing import TYPE_CHECKING

from aclaf.exceptions import AclafError

if TYPE_CHECKING:
    from aclaf.parser import ParsedParameterValue


class ConversionError(AclafError):
    def __init__(
        self,
        value: "ParsedParameterValue | None",
        target_type: type,
        reason: str | None = None,
    ) -> None:
        self.value: ParsedParameterValue | None = value
        self.target_type: type = target_type
        self.reason: str | None = reason
        msg = f"Failed to convert value '{value}' to type '{target_type.__name__}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)
