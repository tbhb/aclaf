from difflib import get_close_matches
from typing import TYPE_CHECKING

from aclaf.exceptions import AclafError

from ._utils import full_option_name

if TYPE_CHECKING:
    from ._parameters import OptionSpec


class SpecValidationError(AclafError):
    """Exception raised for validation errors in command specification.

    This exception is raised during specification construction or validation
    when the command, option, or positional specifications contain invalid
    configurations or violate structural constraints. These errors indicate
    programming mistakes in the specification itself and should be caught
    during development and testing.

    When Raised:
        - During CommandSpec initialization with invalid parameters
        - During OptionSpec initialization with conflicting configurations
        - During PositionalSpec initialization with invalid arity settings
        - When specification validation rules are violated

    Note:
        While SpecValidationError exists in the exception hierarchy, many
        specification validation errors are currently raised as ValueError
        by the specification classes for compatibility with Python conventions.

    Example:
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


class ParseError(AclafError):
    """Base exception for all parsing errors.

    This is the base class for all exceptions raised during command-line
    argument parsing. Applications can catch this exception to handle all
    parsing errors uniformly.
    """


class ArityMismatchError(ParseError):
    """Exception raised when provided arguments don't match expected arity.

    This exception occurs when an option or positional parameter receives
    a different number of values than its arity specification requires.
    This is a general arity validation exception that can occur for both
    options and positional parameters.

    Attributes:
        name: The name of the parameter that received incorrect arity.
        expected: The expected number of arguments.
        received: The actual number of arguments received.

    When Raised:
        - Internal validation detects arity mismatch
        - Number of values doesn't match arity specification
        - Used as a general-purpose arity validation error

    Example:
        >>> from aclaf.parser.exceptions import ArityMismatchError
        >>> # Typically raised internally by the parser
        >>> try:
        ...     raise ArityMismatchError("output", expected=2, received=1)
        ... except ArityMismatchError as e:
        ...     print(f"Parameter: {e.name}")
        ...     print(f"Expected: {e.expected}, Received: {e.received}")
        Parameter: output
        Expected: 2, Received: 1
    """

    def __init__(self, name: str, expected: int, received: int) -> None:
        self.name: str = name
        self.expected: int = expected
        self.received: int = received
        message = (
            f"Arity mismatch for '{name}': expected {expected} argument(s), "
            f"but received {received}."
        )
        super().__init__(message)


class UnknownOptionError(ParseError):
    """Exception raised when an unknown option is encountered.

    This exception is raised when the user specifies an option that does
    not match any option defined in the command specification, taking into
    account configured abbreviation and case sensitivity settings.

    Attributes:
        name: The unknown option name as provided by the user.
        all_names: Tuple of all valid option names for the command (useful
            for generating suggestions or implementing error recovery).

    When Raised:
        - User provides an option not defined in the specification
        - Option name doesn't match when abbreviations are disabled
        - No valid abbreviation match when abbreviations are enabled

    Example:
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
        ...     print(f"Valid options: {', '.join(e.all_names)}")
        Unknown option: unknown
        Valid options: v, verbose, o, output
    """

    def __init__(self, name: str, possible_names: tuple[str, ...]) -> None:
        self.name: str = name
        self.all_names: tuple[str, ...] = possible_names
        message = f"Unknown option '{name}'."
        super().__init__(message)


class OptionCannotBeSpecifiedMultipleTimesError(ParseError):
    """Exception raised when option specified multiple times but not allowed.

    This enforces the accumulation mode setting for options.

    Attributes:
        name: The option name as provided by the user.
        option_spec: The option specification for reference.

    When Raised:
        - Option has AccumulationMode.ERROR (the default)
        - User specifies the same option multiple times
        - Multiple specifications include aliases and different forms (short/long)

    Example:
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
        ...     print(f"Option {e.name} was already specified")
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        self.name: str = name
        self.option_spec: OptionSpec = option_spec

        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
        message = (
            f"Option '{message_name}' ({canonical_name}) cannot be "
            "specified multiple times."
        )
        super().__init__(message)


class OptionCannotBeCombinedError(ParseError):
    """Exception raised when non-combinable option used in combined form.

    This occurs when an option with allow_combined=False is used in a
    short option cluster (e.g., -abc).

    Attributes:
        name: The option name as provided by the user.
        option_spec: The option specification for reference.

    When Raised:
        - Option has allow_combined=False (typically for options that consume values)
        - User attempts to combine it with other short options
        - The option appears in a short option cluster

    Example:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.types import EXACTLY_ONE_ARITY
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[
        ...         OptionSpec("all", short="a", is_flag=True),
        ...         OptionSpec(
        ...             "file", short="f", arity=EXACTLY_ONE_ARITY, allow_combined=False
        ...         ),
        ...     ],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["-af", "file.txt"])
        ... except OptionCannotBeCombinedError as e:
        ...     print(f"Use {e.name} separately")
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        self.name: str = name
        self.option_spec: OptionSpec = option_spec

        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
        message = (
            f"Option '{message_name}' ({canonical_name}) cannot be "
            "combined with other options."
        )
        super().__init__(message)


class OptionDoesNotAcceptValueError(ParseError):
    """Exception raised when option doesn't accept value but one is provided.

    This applies to options with zero arity (not flags, which have special handling).

    Attributes:
        name: The option name as provided by the user.
        option_spec: The option specification for reference.

    When Raised:
        - Option has arity (0, 0) but is not a flag
        - User provides a value using = syntax
        - The option is designed to have no associated value

    Example:
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
        self.name: str = name
        self.option_spec: OptionSpec = option_spec

        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
        message = f"Option '{message_name}' ({canonical_name}) does not accept a value."
        super().__init__(message)


class FlagWithValueError(ParseError):
    """Exception raised when flag provided with value but not allowed.

    This exception occurs when a boolean flag (arity 0) is specified using
    the '--flag=value' syntax but the parser configuration doesn't allow
    explicit flag values.

    Attributes:
        name: The flag option name as provided by the user.
        option_spec: The option specification for the flag.

    When Raised:
        - Option is defined as a flag (is_flag=True)
        - User provides value using --flag=value or -f value syntax
        - Parser has allow_equals_for_flags=False (the default)

    Example:
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
        self.name: str = name
        self.option_spec: OptionSpec = option_spec

        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
        message = (
            f"Flag option '{message_name}' ({canonical_name}) does not accept a value. "
            "Enable 'allow_equals_for_flags' to override this behavior "
            "and coerce boolean-like values."
        )
        super().__init__(message)


class MissingOptionValueError(ParseError):
    """Exception raised when an option that requires a value is missing one.

    Attributes:
        name: The option name as provided by the user.
        option_spec: The option specification for reference.

    When Raised:
        - Option has arity requiring at least one value
        - Option appears at the end of arguments with no following value
        - Next argument is another option (starts with -)
        - Next argument is a recognized subcommand

    Example:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.types import EXACTLY_ONE_ARITY
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[OptionSpec("output", long="output", arity=EXACTLY_ONE_ARITY)],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["--output"])  # Missing value
        ... except MissingOptionValueError as e:
        ...     print(f"Error: {e}")
    """

    def __init__(self, name: str, option_spec: "OptionSpec") -> None:
        self.name: str = name
        self.option_spec: OptionSpec = option_spec

        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
        message = (
            f"Option '{message_name}' ({canonical_name}) requires a value "
            "but none was provided."
        )
        super().__init__(message)


class InvalidFlagValueError(ParseError):
    """Exception raised when a flag option is provided with an invalid value.

    This occurs when allow_equals_for_flags=True but the provided value is
    not in the configured truthy or falsey value sets.

    Attributes:
        name: The flag option name as provided by the user.
        value: The invalid value that was provided.
        option_spec: The option specification for the flag.

    When Raised:
        - Option is a flag and allow_equals_for_flags=True
        - User provides a value using = syntax
        - Value is not in truthy_flag_values or falsey_flag_values
        - Empty string is provided as value

    Example:
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

        message_name = full_option_name(name)
        canonical_name = full_option_name(option_spec.name)
        message = (
            f"Invalid value '{value}' for option '{message_name}' ({canonical_name}). "
            f"Expected one of: {', '.join(sorted(true_values | false_values))}."
        )
        super().__init__(message)


class MultiValueOptionEqualsError(ParseError):
    """Exception raised when multi-value option uses '=' syntax.

    The equals syntax can only provide a single value, so it cannot satisfy
    multi-value requirements.

    Attributes:
        name: The option name as provided by the user.

    When Raised:
        - Option has arity with minimum > 1
        - User attempts to use --option=value syntax
        - The = syntax can only provide one value, not multiple

    Example:
        >>> from aclaf.parser import CommandSpec, OptionSpec, Parser
        >>> from aclaf.parser.types import Arity
        >>> spec = CommandSpec(
        ...     name="myapp",
        ...     options=[
        ...         OptionSpec(
        ...             "files", long="files", arity=Arity(min=2, max=5)
        ...         )  # Requires at least 2
        ...     ],
        ... )
        >>> parser = Parser(spec)
        >>> try:
        ...     parser.parse(["--files=file1.txt"])
        ... except MultiValueOptionEqualsError as e:
        ...     print(f"Error: {e}")
        >>> # Correct usage:
        >>> result = parser.parse(["--files", "file1.txt", "file2.txt"])
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        message = (
            f"Option '{name}' accepts multiple values and cannot be "
            "specified using '=' syntax."
        )
        super().__init__(message)


class InsufficientOptionValuesError(ParseError):
    """Exception raised when option doesn't receive enough values.

    Attributes:
        name: The option name as provided by the user.
        option_spec: The option specification for reference.

    When Raised:
        - Option has minimum arity > 0
        - Not enough values are available after the option
        - Values are consumed by other options or subcommands
        - Inline value provided but minimum arity > 1

    Example:
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
        self.name: str = name
        self.option_spec: OptionSpec = option_spec
        message = (
            f"Insufficient values provided for option '{name}'. "
            f"Expected at least {option_spec.arity}."
        )
        super().__init__(message)


class AmbiguousOptionError(ParseError):
    """Exception raised when an option name is ambiguous.

    This exception occurs when abbreviation matching is enabled and the
    provided option name prefix matches multiple valid option names.

    Attributes:
        name: The ambiguous option name/prefix provided by the user.
        candidates: Sorted list of all option names that match the prefix.

    When Raised:
        - Abbreviation matching is enabled (allow_abbreviated_options=True)
        - User provides a prefix that matches multiple option names
        - No single unique match can be determined

    Example:
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
        self.candidates: list[str] = sorted(candidates)
        message = (
            f"Ambiguous option '--{name}'. Possible matches: {', '.join(candidates)}."
        )
        super().__init__(message)


class AmbiguousSubcommandError(ParseError):
    """Exception raised when a subcommand name is ambiguous.

    This occurs when abbreviation matching is enabled and the provided
    subcommand name prefix matches multiple valid subcommands.

    Attributes:
        name: The ambiguous subcommand name/prefix provided by the user.
        candidates: Sorted list of all subcommand names that match the prefix.

    When Raised:
        - Abbreviation matching is enabled (allow_abbreviated_subcommands=True)
        - User provides a prefix that matches multiple subcommand names
        - No single unique match can be determined

    Example:
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
        self.candidates: list[str] = sorted(candidates)
        message = (
            f"Ambiguous subcommand '{name}'. Possible matches: {', '.join(candidates)}."
        )
        super().__init__(message)


class UnknownSubcommandError(ParseError):
    """Exception raised when an unknown subcommand is encountered during parsing.

    Attributes:
        name: The unknown subcommand name as provided by the user.
        all_names: Tuple of all valid subcommand names for the command.

    When Raised:
        - User provides a subcommand not defined in the specification
        - Subcommand name doesn't match any defined subcommands or aliases
        - No valid abbreviation match when abbreviations are enabled

    Example:
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
        ...     print(f"Available subcommands: {', '.join(e.all_names)}")
    """

    def __init__(self, name: str, possible_names: tuple[str, ...]) -> None:
        self.name: str = name
        self.all_names: tuple[str, ...] = possible_names

        # Build helpful error message with suggestions
        message_parts = [f"Unknown subcommand '{name}'."]

        # Add suggestions if we find similar names
        suggestions = get_close_matches(name, possible_names, n=3, cutoff=0.6)
        if suggestions:
            if len(suggestions) == 1:
                message_parts.append(f"Did you mean '{suggestions[0]}'?")
            else:
                suggestion_list = "', '".join(suggestions)
                message_parts.append(f"Did you mean one of: '{suggestion_list}'?")

        # Always list available subcommands
        if possible_names:
            subcommand_list = "', '".join(sorted(possible_names))
            message_parts.append(f"Available subcommands: '{subcommand_list}'.")

        message = " ".join(message_parts)
        super().__init__(message)


class InsufficientPositionalArgumentsError(ParseError):
    """Exception raised when insufficient positional arguments provided.

    Attributes:
        spec_name: The name of the positional parameter specification.
        expected_min: The minimum number of values expected.
        received: The actual number of values received.

    When Raised:
        - Positional parameter has minimum arity > 0
        - Not enough arguments remain after parsing options
        - Arguments are consumed by other positional parameters
        - User provides fewer arguments than required

    Example:
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

    When Raised:
        - Command specification defines no positional parameters
        - User provides arguments that aren't options or subcommands
        - Arguments appear after all options have been parsed

    Note:
        When a command has no explicit positional specifications, the parser
        creates an implicit positional spec named "args" with unbounded arity
        (0, -1), so this exception is typically only raised when the
        specification explicitly defines an empty positionals set.

    Example:
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
