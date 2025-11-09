import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._command import CommandSpec


@dataclass(slots=True, frozen=True, unsafe_hash=True)
class ParsedOption:
    """Represents a parsed command-line option.

    This immutable dataclass stores the result of parsing a single option,
    including its canonical name, resolved value(s), and the alias that was
    used to specify it (if any).

    Attributes:
        name: The canonical option name (without leading dashes).
        value: The parsed value(s) for this option. The type depends on the
            option's arity and accumulation mode:
            - bool: Flag option (arity 0)
            - int: Count accumulation mode
            - str: Single value (arity 1)
            - tuple[str, ...]: Multiple values or COLLECT mode
            - tuple[bool, ...]: Multiple flags with COLLECT mode
            - tuple[tuple[str, ...], ...]: Nested collection (rare)
        alias: The option alias/abbreviation used by the user, or None if
            the canonical name was used directly.
    """

    name: str
    value: (
        bool
        | int
        | str
        | tuple[bool, ...]
        | tuple[str, ...]
        | tuple[tuple[str, ...], ...]
    )
    alias: str | None = None

    @override
    def __repr__(self) -> str:
        return (
            f"ParsedOption(name={self.name!r},"
            f" value={self.value!r}, alias={self.alias!r})"
        )


@dataclass(slots=True, frozen=True, unsafe_hash=True)
class ParsedPositional:
    """Represents a parsed positional argument.

    This immutable dataclass stores the result of parsing positional arguments
    that were assigned to a named positional parameter specification.

    Attributes:
        name: The positional parameter name from the specification.
        value: The parsed value(s). Either a single string (for arity 1) or
            a tuple of strings (for any other arity including 0 or unbounded).
    """

    name: str
    value: str | tuple[str, ...]

    @override
    def __repr__(self) -> str:
        return f"ParsedPositional(name={self.name!r}, value={self.value!r})"


@dataclass(slots=True, frozen=True, unsafe_hash=True)
class ParseResult:
    """The complete result of parsing command-line arguments.

    This immutable dataclass represents the parsed structure of a command
    invocation, including all options, positionals, and any nested subcommand.
    The structure is recursive to support arbitrary subcommand nesting.

    Attributes:
        command: The canonical command name that was invoked.
        alias: The command alias used by the user, or None if the canonical
            name was used directly.
        options: Dictionary mapping option names to their parsed values.
            Keys are canonical option names (without leading dashes).
        positionals: Dictionary mapping positional parameter names to their
            parsed values. Keys are the names from the positional specifications.
        extra_args: Tuple of arguments that appeared after a standalone '--'
            delimiter. These are preserved as-is for custom handling.
        subcommand: Nested ParseResult for a subcommand invocation, or None
            if no subcommand was specified.
    """

    command: str
    alias: str | None = None
    options: dict[str, ParsedOption] = field(default_factory=dict)
    positionals: dict[str, ParsedPositional] = field(default_factory=dict)
    extra_args: tuple[str, ...] = field(default_factory=tuple)
    subcommand: "ParseResult | None" = None

    @override
    def __repr__(self) -> str:
        return (
            f"ParseResult(command={self.command!r}, alias={self.alias!r},"
            f" options={self.options!r}, positionals={self.positionals!r},"
            f" extra_args={self.extra_args!r}, subcommand={self.subcommand!r})"
        )


class BaseParser(ABC):
    """Abstract base class for command-line argument parsers.

    This class defines the configuration interface for parsers and provides
    property accessors for all parser settings. Concrete implementations must
    provide the `parse()` method.

    The parser supports extensive configuration through boolean flags and
    parameters that control parsing behavior such as abbreviation handling,
    case sensitivity, and option/positional ordering.
    """

    def __init__(  # noqa: PLR0913
        self,
        spec: "CommandSpec",
        *,
        allow_abbreviated_subcommands: bool = False,
        allow_abbreviated_options: bool = False,
        allow_equals_for_flags: bool = False,
        allow_aliases: bool = True,
        allow_negative_numbers: bool = False,
        case_insensitive_flags: bool = False,
        case_insensitive_options: bool = False,
        case_insensitive_subcommands: bool = False,
        convert_underscores_to_dashes: bool = True,
        flatten_option_values: bool = False,
        minimum_abbreviation_length: int = 3,
        negative_number_pattern: str | None = None,
        strict_options_before_positionals: bool = False,
        truthy_flag_values: tuple[str, ...] | None = None,
        falsey_flag_values: tuple[str, ...] | None = None,
    ) -> None:
        """Initialize a parser with a command specification and configuration.

        Args:
            spec: The CommandSpec defining the command structure, options,
                positionals, and subcommands.
            allow_abbreviated_subcommands: Enable prefix matching for subcommand
                names (e.g., 'sta' matches 'start'). Default: False.
            allow_abbreviated_options: Enable prefix matching for option names
                (e.g., '--verb' matches '--verbose'). Default: False.
            allow_equals_for_flags: Allow '--flag=value' syntax for flag options
                that accept explicit true/false values. Default: False.
            allow_aliases: Enable command and option aliases. Default: True.
            allow_negative_numbers: Enable parsing of negative numbers (e.g., -1,
                -3.14, -1e5). When enabled, arguments starting with '-' followed by
                a digit are treated as negative numbers if no matching short option
                exists. Options take precedence over negative number interpretation.
                Default: False.
            case_insensitive_flags: Ignore case when matching boolean flags.
                Default: False.
            case_insensitive_options: Ignore case when matching option names.
                Default: False.
            case_insensitive_subcommands: Ignore case when matching subcommand
                names. Default: False.
            convert_underscores_to_dashes: Convert underscores to dashes in
                option names during matching ('--foo_bar' matches '--foo-bar').
                Default: True.
            flatten_option_values: Global default for value flattening in COLLECT
                mode. When True, values from multiple option occurrences are
                flattened into a single tuple instead of nested tuples. Can be
                overridden by CommandSpec.flatten_option_values or
                OptionSpec.flatten_values. Default: False.
            minimum_abbreviation_length: Minimum characters required for
                abbreviation matching. Default: 3.
            negative_number_pattern: Custom regex pattern for negative number
                detection. If None, uses DEFAULT_NEGATIVE_NUMBER_PATTERN. Only
                used when allow_negative_numbers is True. The pattern is validated
                for safety (no ReDoS vulnerabilities). Default: None.
            strict_options_before_positionals: POSIX-style mode where options
                must appear before positionals. After the first positional,
                all remaining arguments are treated as positionals. Default: False
                (GNU-style, options can appear anywhere).
            truthy_flag_values: Custom values that set flags to True when using
                '--flag=value' syntax. Default: None (uses builtin defaults).
            falsey_flag_values: Custom values that set flags to False when using
                '--flag=value' syntax. Default: None (uses builtin defaults).
        """
        self._spec: CommandSpec = spec

        self._allow_abbreviated_subcommands: bool = allow_abbreviated_subcommands
        self._allow_abbreviated_options: bool = allow_abbreviated_options
        self._allow_aliases: bool = allow_aliases
        self._allow_equals_for_flags: bool = allow_equals_for_flags
        self._allow_negative_numbers: bool = allow_negative_numbers
        self._case_insensitive_flags: bool = case_insensitive_flags
        self._case_insensitive_options: bool = case_insensitive_options
        self._case_insensitive_subcommands: bool = case_insensitive_subcommands
        self._convert_underscores_to_dashes: bool = convert_underscores_to_dashes
        self._flatten_option_values: bool = flatten_option_values
        self._minimum_abbreviation_length: int = minimum_abbreviation_length
        self._strict_options_before_positionals: bool = (
            strict_options_before_positionals
        )
        self._truthy_flag_values: tuple[str, ...] | None = truthy_flag_values
        self._falsey_flag_values: tuple[str, ...] | None = falsey_flag_values

        # Validate and store negative number pattern
        if negative_number_pattern is not None:
            self._validate_negative_number_pattern(negative_number_pattern)
        self._negative_number_pattern: str | None = negative_number_pattern

    @property
    def spec(self) -> "CommandSpec":
        """The command specification for this parser."""
        return self._spec

    @property
    def allow_abbreviated_subcommands(self) -> bool:
        """Whether subcommand abbreviation is enabled."""
        return self._allow_abbreviated_subcommands

    @property
    def allow_abbreviated_options(self) -> bool:
        """Whether option abbreviation is enabled."""
        return self._allow_abbreviated_options

    @property
    def allow_aliases(self) -> bool:
        """Whether command and option aliases are enabled."""
        return self._allow_aliases

    @property
    def allow_equals_for_flags(self) -> bool:
        """Whether '--flag=value' syntax is allowed for boolean flags."""
        return self._allow_equals_for_flags

    @property
    def case_insensitive_flags(self) -> bool:
        """Whether flag matching is case-insensitive."""
        return self._case_insensitive_flags

    @property
    def case_insensitive_options(self) -> bool:
        """Whether option matching is case-insensitive."""
        return self._case_insensitive_options

    @property
    def case_insensitive_subcommands(self) -> bool:
        """Whether subcommand matching is case-insensitive."""
        return self._case_insensitive_subcommands

    @property
    def convert_underscores_to_dashes(self) -> bool:
        """Whether underscores are converted to dashes during matching."""
        return self._convert_underscores_to_dashes

    @property
    def flatten_option_values(self) -> bool:
        """Global default for value flattening in COLLECT mode.

        When True, values from multiple option occurrences are flattened into
        a single tuple instead of nested tuples. Can be overridden per-command
        or per-option.
        """
        return self._flatten_option_values

    @property
    def minimum_abbreviation_length(self) -> int:
        """Minimum character length required for abbreviation matching."""
        return self._minimum_abbreviation_length

    @property
    def strict_options_before_positionals(self) -> bool:
        """Whether POSIX-style strict option ordering is enforced."""
        return self._strict_options_before_positionals

    @property
    def truthy_flag_values(self) -> tuple[str, ...] | None:
        """Custom values treated as True for flag options."""
        return self._truthy_flag_values

    @property
    def falsey_flag_values(self) -> tuple[str, ...] | None:
        """Custom values treated as False for flag options."""
        return self._falsey_flag_values

    @property
    def allow_negative_numbers(self) -> bool:
        """Whether negative number parsing is enabled."""
        return self._allow_negative_numbers

    @property
    def negative_number_pattern(self) -> str | None:
        """Custom regex pattern for negative number detection."""
        return self._negative_number_pattern

    @staticmethod
    def _validate_negative_number_pattern(pattern: str) -> None:
        """Validate negative number pattern for safety.

        Checks:
            - Pattern compiles successfully
            - Pattern doesn't match empty string
            - No catastrophic backtracking patterns (basic ReDoS check)

        Args:
            pattern: The regex pattern to validate.

        Raises:
            ValueError: If pattern is unsafe or invalid.
        """
        # Compile check
        try:
            compiled = re.compile(pattern)
        except re.error as e:
            msg = f"Invalid regex pattern: {e}"
            raise ValueError(msg) from e

        # Empty string check
        if compiled.match(""):
            msg = "Pattern must not match empty string"
            raise ValueError(msg)

        # Basic ReDoS check (not exhaustive, but catches common cases)
        # Flag nested quantifiers like (a+)+ or (a*)*
        nested_quantifiers = re.compile(r"\([^)]*[+*][^)]*\)[+*]")
        if nested_quantifiers.search(pattern):
            msg = "Pattern contains nested quantifiers which may cause ReDoS"
            raise ValueError(msg)

    @abstractmethod
    def parse(self, args: "Sequence[str]") -> "ParseResult":
        """Parse a sequence of command-line arguments.

        Args:
            args: The arguments to parse, typically from sys.argv[1:].

        Returns:
            A ParseResult containing the parsed command, options, positionals,
            and any nested subcommand.

        Raises:
            ParseError: If the arguments cannot be parsed according to the
                command specification and parser configuration.
        """
        ...
