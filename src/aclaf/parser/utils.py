from .constants import COMMAND_NAME_REGEX


def validate_command_name(name: str) -> None:
    """Validate that a command name is valid.

    Args:
        name: The command name to validate.

    Raises:
        ValueError: If the command name is invalid.
    """
    if not COMMAND_NAME_REGEX.match(name):
        msg = (
            f"Invalid command name: {name!r}. Command names must start with a letter"
            " and can only contain letters, numbers, hyphens, and underscores."
        )
        raise ValueError(msg)
