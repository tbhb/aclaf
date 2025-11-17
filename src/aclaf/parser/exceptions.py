from typing import TYPE_CHECKING

from aclaf.exceptions import AclafError

if TYPE_CHECKING:
    from ._parameters import OptionSpec
    from .types import Arity


def _format_option_name(name: str) -> str:
    if len(name) == 1:
        return f"-{name}"
    return f"--{name}"


def _format_arity(arity: "Arity") -> str:
    if arity.min == arity.max:
        return f"{arity.min} value(s)"
    if arity.max is None:
        return f"at least {arity.min} value(s)"
    return f"{arity.min}-{arity.max} values"


class SpecificationError(AclafError):
    """Exception raised for validation errors in command specification.

    This exception is raised during specification construction or validation
    when the command, option, or positional specifications contain invalid
    configurations or violate structural constraints. These errors indicate
    programming mistakes in the specification itself and should be caught
    during development and testing.

    Info: When Raised
        - During [`CommandSpec`][aclaf.parser.CommandSpec] initialization
          with invalid parameters
        - During [`OptionSpec`][aclaf.parser.OptionSpec] initialization with
          conflicting configurations
        - During [`PositionalSpec`][aclaf.parser.PositionalSpec]
          initialization with invalid arity settings
        - When specification validation rules are violated

    Note:
        While SpecificationError exists in the exception hierarchy, many
        specification validation errors are currently raised as ValueError
        by the specification classes for compatibility with Python conventions.
    """

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified specification error occurred."
        super().__init__(message, detail=detail)


class ParserConfigurationError(AclafError):
    """Exception raised for invalid parser configuration settings.

    This exception is raised during parser construction when configuration
    parameters contain invalid values that violate validation rules. These
    errors indicate programming mistakes in parser configuration and should
    be caught during development and testing.

    Info: When Raised
        - During [`Parser`][aclaf.parser.Parser] initialization with invalid
          configuration parameters
        - During [`ParserConfiguration`][aclaf.parser.ParserConfiguration]
          initialization with invalid values
        - When configuration validation rules are violated
    """


class ParseError(AclafError):
    """Base exception for all parsing errors.

    This is the base class for all exceptions raised during command-line
    argument parsing. Applications can catch this exception to handle all
    parsing errors uniformly while still providing specific exception
    types for detailed error handling.

    Info: When Raised
        ParseError is never raised directly. Only its subclasses are raised
        during parsing, including:
        - Unknown option/subcommand errors
        - Option value errors (missing, invalid, insufficient)
        - Positional argument errors
        - Ambiguous name errors (when abbreviations are enabled)

    Note:
        This exception is distinct from SpecValidationError, which is raised
        during specification construction for invalid command configurations.
        ParseError is raised during runtime parsing of user-provided arguments.
    """

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        if not message:
            message = "An unspecified parse error occurred."
        super().__init__(message, detail=detail)


class OptionError(ParseError):
    """Base class for option-related parsing errors.

    This base class allows error handlers to catch all option-related
    parsing errors uniformly while still providing specific exception
    types for detailed error handling.

    Attributes:
        name: The option name as provided by the user, without prefix
            dashes (e.g., `v` for `-v`, `verbose` for `--verbose`).
        option_spec: The option specification for reference.

    Note:
        OptionError is never raised directly. Only its subclasses are raised
        during option parsing.
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        self.name: str = name
        self.option_spec: OptionSpec = option_spec
        super().__init__("")  # Subclasses construct their own messages


class UnknownOptionError(ParseError):
    """Exception raised when an unknown option is encountered.

    This exception is raised when the user specifies an option that does
    not match any option defined in the command specification, taking into
    account configured abbreviation and case sensitivity settings.

    Attributes:
        name: The option name as provided by the user, without prefix dashes
            (e.g., `v` for `-v`, `verbose` for `--verbose`).
        possible_names: Tuple of all valid option names for the command (useful
            for generating suggestions or implementing error recovery).

    Info: When Raised
        - User provides an option not defined in the specification
        - Option name doesn't match when abbreviations are disabled
        - No valid abbreviation match when abbreviations are enabled
    """

    def __init__(self, name: str, possible_names: tuple[str, ...]) -> None:
        self.name: str = name
        self.possible_names: tuple[str, ...] = possible_names
        message = f"Unknown option '{_format_option_name(name)}'."
        super().__init__(message)


class DuplicateOptionError(OptionError):
    """Exception raised when option specified multiple times but not allowed.

    This enforces the accumulation mode setting for options.

    Attributes:
        name: The option name as provided by the user, without prefix dashes
            (e.g., `o` for `-o`, `output` for `--output`).
        option_spec: The option specification for reference.

    Info: When Raised
        - Option has
          [`AccumulationMode.ERROR`][aclaf.parser.AccumulationMode.ERROR]
          (the default)
        - User specifies the same option multiple times
        - Multiple specifications include aliases and different forms
          (short/long)
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        super().__init__(name, option_spec)
        message_name = _format_option_name(name)
        canonical_name = _format_option_name(option_spec.name)
        message = (
            f"Option '{message_name}' ({canonical_name}) cannot be "
            "specified multiple times."
        )
        # Update the message after calling super().__init__
        self.args: tuple[str] = (message,)


class OptionDoesNotAcceptValueError(OptionError):
    """Exception raised when option doesn't accept value but one is provided.

    This applies to options with zero arity (not flags, which have special handling).

    Attributes:
        name: The option name as provided by the user, without prefix dashes
            (e.g., `enable` for `--enable`).
        option_spec: The option specification for reference.

    Info: When Raised
        - Option has arity `(0, 0)` but is not a flag
        - User provides a value using `=` syntax
        - The option is designed to have no associated value
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        super().__init__(name, option_spec)
        message_name = _format_option_name(name)
        canonical_name = _format_option_name(option_spec.name)
        message = f"Option '{message_name}' ({canonical_name}) does not accept a value."
        self.args: tuple[str] = (message,)


class FlagWithValueError(OptionError):
    """Exception raised when flag provided with value but not allowed.

    This exception occurs when a boolean flag (arity 0) is specified using
    the '--flag=value' syntax but the parser configuration doesn't allow
    explicit flag values.

    Attributes:
        name: The flag option name as provided by the user, without prefix dashes
            (e.g., `v` for `-v`, `verbose` for `--verbose`).
        option_spec: The option specification for the flag.

    Info: When Raised
        - Option is defined as a flag (`is_flag=True`)
        - User provides value using `--flag=value` or `-f value` syntax
        - Parser has `allow_equals_for_flags=False` (the default)
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        super().__init__(name, option_spec)
        message_name = _format_option_name(name)
        canonical_name = _format_option_name(option_spec.name)
        message = (
            f"Flag option '{message_name}' ({canonical_name}) does not accept a value. "
            "Enable 'allow_equals_for_flags' to override this behavior "
            "and coerce boolean-like values."
        )
        self.args: tuple[str] = (message,)


class InvalidFlagValueError(ParseError):
    """Exception raised when a flag option is provided with an invalid value.

    This occurs when allow_equals_for_flags=True but the provided value is
    not in the configured truthy or falsey value sets.

    Attributes:
        name: The flag option name as provided by the user, without prefix dashes
            (e.g., `v` for `-v`, `verbose` for `--verbose`).
        value: The invalid value that was provided.
        option_spec: The option specification for the flag.
        true_values: Frozenset of valid truthy values.
        false_values: Frozenset of valid falsey values.

    Info: When Raised
        - Option is a flag and `allow_equals_for_flags=True`
        - User provides a value using `=` syntax
        - Value is not in `truthy_flag_values` or `falsey_flag_values`
        - Empty string is provided as value
    """

    def __init__(
        self,
        name: str,
        value: str,
        option_spec: "OptionSpec",
        true_values: frozenset[str],
        false_values: frozenset[str],
    ) -> None:
        self.name: str = name
        self.value: str = value
        self.option_spec: OptionSpec = option_spec
        self.true_values: frozenset[str] = true_values
        self.false_values: frozenset[str] = false_values

        message_name = _format_option_name(name)
        canonical_name = _format_option_name(option_spec.name)
        message = (
            f"Invalid value '{value}' for option '{message_name}' ({canonical_name}). "
            f"Expected one of: {', '.join(sorted(true_values | false_values))}."
        )
        super().__init__(message)


class InsufficientOptionValuesError(OptionError):
    """Exception raised when option doesn't receive enough values.

    Attributes:
        name: The option name as provided by the user, without prefix dashes
            (e.g., `dimensions` for `--dimensions`).
        option_spec: The option specification for reference.

    Info: When Raised
        - Option has minimum arity `> 0`
        - Not enough values are available after the option
        - Values are consumed by other options or subcommands
        - Inline value provided but minimum arity `> 1`
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        super().__init__(name, option_spec)
        message_name = _format_option_name(name)
        canonical_name = _format_option_name(option_spec.name)
        # Arity should always be present for options, but handle None defensively
        arity_str = _format_arity(option_spec.arity)
        message = (
            f"Insufficient values provided for option '{message_name}' "
            f"({canonical_name}). Expected {arity_str}."
        )
        self.args: tuple[str] = (message,)


class AmbiguousOptionError(ParseError):
    """Exception raised when an option name is ambiguous.

    This exception occurs when abbreviation matching is enabled and the
    provided option name prefix matches multiple valid option names.

    Attributes:
        name: The ambiguous option name/prefix as provided by the user, without
            prefix dashes (e.g., `ver` for `--ver`).
        candidates: Sorted tuple of all option names that match the prefix.

    Info: When Raised
        - Abbreviation matching is enabled (`allow_abbreviated_options=True`)
        - User provides a prefix that matches multiple option names
        - No single unique match can be determined
    """

    def __init__(self, name: str, candidates: list[str]) -> None:
        self.name: str = name
        self.candidates: tuple[str, ...] = tuple(sorted(candidates))
        message = (
            f"Ambiguous option '{_format_option_name(name)}'. "
            f"Possible matches: {', '.join(self.candidates)}."
        )
        super().__init__(message)


class AmbiguousSubcommandError(ParseError):
    """Exception raised when a subcommand name is ambiguous.

    This occurs when abbreviation matching is enabled and the provided
    subcommand name prefix matches multiple valid subcommands.

    Attributes:
        name: The ambiguous subcommand name/prefix as provided by the user
            (e.g., `in` for both `install` and `initialize`).
        candidates: Sorted tuple of all subcommand names that match the prefix.

    Info: When Raised
        - Abbreviation matching is enabled (`allow_abbreviated_subcommands=True`)
        - User provides a prefix that matches multiple subcommand names
        - No single unique match can be determined
    """

    def __init__(self, name: str, candidates: list[str]) -> None:
        self.name: str = name
        self.candidates: tuple[str, ...] = tuple(sorted(candidates))
        candidate_list = ", ".join(self.candidates)
        message = f"Ambiguous subcommand '{name}'. Possible matches: {candidate_list}."
        super().__init__(message)


class UnknownSubcommandError(ParseError):
    """Exception raised when an unknown subcommand is encountered during parsing.

    Attributes:
        name: The unknown subcommand name as provided by the user (e.g., `merge`).
        possible_names: Tuple of all valid subcommand names for the command.

    Info: When Raised
        - User provides a subcommand not defined in the specification
        - Subcommand name doesn't match any defined subcommands or aliases
        - No valid abbreviation match when abbreviations are enabled
    """

    def __init__(self, name: str, possible_names: tuple[str, ...]) -> None:
        self.name: str = name
        self.possible_names: tuple[str, ...] = possible_names

        # Build error message
        message = f"Unknown subcommand '{name}'."
        if possible_names:
            subcommand_list = ", ".join(sorted(possible_names))
            message += f" Available subcommands: {subcommand_list}."

        super().__init__(message)


class InsufficientPositionalArgumentsError(ParseError):
    """Exception raised when insufficient positional arguments provided.

    Attributes:
        spec_name: The name of the positional argument specification.
        expected_min: The minimum number of values expected.
        received: The actual number of values received.

    Info: When Raised
        - Positional argument has minimum arity > 0
        - Not enough arguments remain after parsing options
        - Arguments are consumed by other positional arguments
        - User provides fewer arguments than required
    """

    def __init__(self, spec_name: str, expected_min: int, received: int) -> None:
        self.spec_name: str = spec_name
        self.expected_min: int = expected_min
        self.received: int = received
        message = (
            f"Positional argument '{spec_name}' requires at least {expected_min} "
            f"value(s), got {received}."
        )
        super().__init__(message)


class UnexpectedPositionalArgumentError(ParseError):
    """Exception raised when positional arguments are provided but none are expected.

    Attributes:
        argument: The unexpected positional argument.
        command_name: The name of the command that doesn't accept positionals.

    Info: When Raised
        - Command specification defines no positional arguments
        - User provides arguments that aren't options or subcommands
        - Arguments appear after all options have been parsed

    Note:
        When a command has no explicit positional argument specifications,
        the parser creates an implicit positional spec named `args` with
        unbounded arity `(0, -1)`, so this exception is typically only raised
        when the specification explicitly defines an empty positionals set.
    """

    def __init__(self, argument: str, command_name: str) -> None:
        self.argument: str = argument
        self.command_name: str = command_name
        message = (
            f"Unexpected positional argument '{argument}' "
            f"(command '{command_name}' accepts no positionals)."
        )
        super().__init__(message)
