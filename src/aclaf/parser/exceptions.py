from typing import TYPE_CHECKING

from aclaf.exceptions import AclafError

from ._utils import full_option_name

if TYPE_CHECKING:
    from ._parameters import OptionSpec
    from .types import Arity


def _format_arity(arity: "Arity") -> str:
    """Format arity as user-friendly text.

    Args:
        arity: The arity specification to format.

    Returns:
        A human-readable string describing the arity requirement.

    Examples:
        >>> _format_arity(Arity(min=2, max=2))
        "2 value(s)"
        >>> _format_arity(Arity(min=1, max=None))
        "at least 1 value(s)"
        >>> _format_arity(Arity(min=2, max=5))
        "2-5 values"
    """
    if arity.min == arity.max:
        return f"{arity.min} value(s)"
    if arity.max is None:
        return f"at least {arity.min} value(s)"
    return f"{arity.min}-{arity.max} values"


class SpecValidationError(AclafError):
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
        While SpecValidationError exists in the exception hierarchy, many
        specification validation errors are currently raised as ValueError
        by the specification classes for compatibility with Python conventions.

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec
        >>> try:
        ...     # Duplicate option names will raise validation error
        ...     spec = CommandSpec(
        ...         name="myapp",
        ...         options=[
        ...             OptionSpec("verbose", long="verbose", short="v"),
        ...             OptionSpec("version", long="verbose", short="V"),  # Duplicate
        ...         ],
        ...     )
        ... except ValueError as e:
        ...     print(f"Specification error: {e}")
    """


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

    Examples:
        >>> from aclaf.parser import CommandSpec, Parser
        >>> spec = CommandSpec(name="myapp")
        >>> try:
        ...     # Invalid minimum_abbreviation_length will raise error
        ...     parser = Parser(spec, minimum_abbreviation_length=0)
        ... except ParserConfigurationError as e:
        ...     print(f"Configuration error: {e}")
        Configuration error: minimum_abbreviation_length must be at least 1, got 0.
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.exceptions import ParseError, UnknownOptionError
        >>> spec = CommandSpec(name="myapp", options=[OptionSpec("verbose", short="v")])
        >>> parser = Parser(spec)
        >>> try:
        ...     result = parser.parse(["--unknown"])
        ... except UnknownOptionError as e:
        ...     print(f"Specific: {e}")
        ... except ParseError as e:
        ...     print(f"General: {e}")
    """


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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.exceptions import OptionError
        >>> spec = CommandSpec(name="myapp", options=[OptionSpec("output", short="o")])
        >>> parser = Parser(spec)
        >>> try:
        ...     result = parser.parse(["-o"])  # Missing value
        ... except OptionError as e:
        ...     print(f"Option error for {e.name!r}: {e}")
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.exceptions import UnknownOptionError
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[
        ...         OptionSpec("verbose", short="v"),
        ...         OptionSpec("output", short="o"),
        ...     ],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     result = parser.parse(["--unknown"])
        ... except UnknownOptionError as e:
        ...     print(f"Unknown option: {e.name}")
        ...     print(f"Valid options: {', '.join(e.possible_names)}")
        Unknown option: unknown
        Valid options: v, verbose, o, output
    """

    def __init__(self, name: str, possible_names: tuple[str, ...]) -> None:
        self.name: str = name
        self.possible_names: tuple[str, ...] = possible_names
        message = f"Unknown option '{full_option_name(name)}'."
        super().__init__(message)


class OptionCannotBeSpecifiedMultipleTimesError(OptionError):
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.types import AccumulationMode
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[
        ...         OptionSpec(
        ...             "output",
        ...             long="output",
        ...             short="o",
        ...             accumulation_mode=AccumulationMode.ERROR,
        ...         )
        ...     ],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["--output", "file1.txt", "-o", "file2.txt"])
        ... except OptionCannotBeSpecifiedMultipleTimesError as e:
        ...     print(f"Option {e.name!r} was already specified")
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        super().__init__(name, option_spec)
        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.types import Arity
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[
        ...         OptionSpec(
        ...             "enable", long="enable", arity=Arity(min=0, max=0)
        ...         )  # Zero arity, non-flag
        ...     ],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["--enable=value"])
        ... except OptionDoesNotAcceptValueError as e:
        ...     print(f"Error: {e}")
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        super().__init__(name, option_spec)
        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[OptionSpec("verbose", long="verbose", is_flag=True)],
        ... )
        >>> parser = Parser(spec)  # allow_equals_for_flags defaults to False
        >>> try:
        ...     parser.parse(["--verbose=true"])
        ... except FlagWithValueError as e:
        ...     print(f"Error: {e}")
        >>> # With allow_equals_for_flags=True, this would work:
        >>> parser_with_flag_values = Parser(spec, allow_equals_for_flags=True)
        >>> result = parser_with_flag_values.parse(["--verbose=true"])
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        super().__init__(name, option_spec)
        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[OptionSpec("verbose", long="verbose", is_flag=True)],
        ... )
        >>> # Default truthy: {"true", "1", "yes", "on"}
        >>> # Default falsey: {"false", "0", "no", "off"}
        >>> parser = Parser(spec, allow_equals_for_flags=True)
        >>> try:
        ...     parser.parse(["--verbose=maybe"])
        ... except InvalidFlagValueError as e:
        ...     print(f"Invalid value: {e.value}")
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

        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.types import Arity
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[
        ...         OptionSpec(
        ...             "dimensions", long="dimensions", arity=Arity(min=2, max=3)
        ...         )  # Requires 2-3 values
        ...     ],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["--dimensions", "800"])  # Only one value
        ... except InsufficientOptionValuesError as e:
        ...     print(f"Expected: {e.option_spec.arity.min} values")
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        super().__init__(name, option_spec)
        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
        # Arity should always be present for options, but handle None defensively
        arity_str = (
            _format_arity(option_spec.arity)
            if option_spec.arity is not None
            else "values"
        )
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[
        ...         OptionSpec("verbose", long="verbose"),
        ...         OptionSpec("version", long="version"),
        ...     ],
        ... )
        >>> parser = Parser(spec, allow_abbreviated_options=True)
        >>> try:
        ...     parser.parse(["--ver"])  # Matches both "verbose" and "version"
        ... except AmbiguousOptionError as e:
        ...     print(f"Did you mean one of: {', '.join(e.candidates)}")
    """

    def __init__(self, name: str, candidates: list[str]) -> None:
        self.name: str = name
        self.candidates: tuple[str, ...] = tuple(sorted(candidates))
        message = (
            f"Ambiguous option '{full_option_name(name)}'. "
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

    Examples:
        >>> from aclaf.parser import CommandSpec, Parser
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     subcommands=[
        ...         CommandSpec(name="install"),
        ...         CommandSpec(name="initialize"),
        ...     ],
        ... )
        >>> parser = Parser(spec, allow_abbreviated_subcommands=True)
        >>> try:
        ...     parser.parse(["in"])  # Matches both "install" and "initialize"
        ... except AmbiguousSubcommandError as e:
        ...     print(f"Please be more specific: {', '.join(e.candidates)}")
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

    Examples:
        >>> from aclaf.parser import CommandSpec, Parser
        >>> spec = CommandSpec(
        ...     name="git",
        ...     subcommands=[
        ...         CommandSpec(name="commit"),
        ...         CommandSpec(name="push"),
        ...         CommandSpec(name="pull"),
        ...     ],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["merge"])
        ... except UnknownSubcommandError as e:
        ...     print(f"Available subcommands: {', '.join(e.possible_names)}")
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

    Examples:
        >>> from aclaf.parser import CommandSpec, PositionalSpec, Parser
        >>> from aclaf.parser.types import Arity
        >>> spec = CommandSpec(
        ...     name="copy",
        ...     positionals=[
        ...         PositionalSpec("source", arity=Arity(min=1, max=None)),
        ...         PositionalSpec("destination", arity=Arity(min=1, max=1)),
        ...     ],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["file1.txt"])  # No destination
        ... except InsufficientPositionalArgumentsError as e:
        ...     print(f"Expected: {e.expected_min}, Received: {e.received}")
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

    Examples:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> spec = CommandSpec(
        ...     name="status",
        ...     options=[OptionSpec("verbose", short="v", is_flag=True)],
        ...     # No positionals defined
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["--verbose", "extra_arg"])
        ... except UnexpectedPositionalArgumentError as e:
        ...     print(f"Unexpected argument: {e.argument}")
    """

    def __init__(self, argument: str, command_name: str) -> None:
        self.argument: str = argument
        self.command_name: str = command_name
        message = (
            f"Unexpected positional argument '{argument}' "
            f"(command '{command_name}' accepts no positionals)."
        )
        super().__init__(message)
