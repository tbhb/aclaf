from typing_extensions import override

from aclaf.exceptions import AclafError


class ValidationError(AclafError):
    def __init__(self, errors: dict[str, dict[str, tuple[str, ...]]]) -> None:
        super().__init__("Validation failed")
        self.errors: dict[str, dict[str, tuple[str, ...]]] = errors

    @override
    def __str__(self) -> str:
        """Return string representation including detailed error messages."""
        if not self.errors:
            return "Validation failed"

        error_lines = ["Validation failed:"]
        for command_name, param_errors in self.errors.items():
            for param_name, messages in param_errors.items():
                error_lines.extend(
                    f"  {command_name}.{param_name}: {message}" for message in messages
                )

        return "\n".join(error_lines)
