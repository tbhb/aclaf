from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Unpack, override

from aclaf.parser._configuration import (
    DEFAULT_PARSER_CONFIGURATION,
    ParserConfiguration,
    ParserConfigurationInput,
)

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
            - `bool`: Flag option (arity 0)
            - `int`: Count accumulation mode
            - `str`: Single value (arity 1)
            - `tuple[str, ...]`: Multiple values or COLLECT mode
            - `tuple[bool, ...]`: Multiple flags with COLLECT mode
            - `tuple[tuple[str, ...], ...]`: Nested collection (rare)
        alias: The option alias/abbreviation used by the user, or `None` if
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
        value: The parsed value(s). Either a single string (for `arity=1`) or
            a tuple of strings (for any other arity including `0` or unbounded).
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
        alias: The command alias used by the user, or `None` if the canonical
            name was used directly.
        options: Dictionary mapping option names to their parsed values.
            Keys are canonical option names (without leading dashes).
        positionals: Dictionary mapping positional parameter names to their
            parsed values. Keys are the names from the positional specifications.
        extra_args: Tuple of arguments that appeared after a standalone `--`
            delimiter. These are preserved as-is for custom handling.
        subcommand: Nested [`ParseResult`][aclaf.parser.ParseResult] for a
            subcommand invocation, or `None` if no subcommand was specified.
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

    def __init__(
        self,
        spec: "CommandSpec",
        config: ParserConfiguration | None = None,
        **overrides: Unpack[ParserConfigurationInput],
    ) -> None:
        """Initialize a parser with a command specification and configuration.

        Args:
            spec: The [`CommandSpec`][aclaf.parser.CommandSpec] defining the
                command structure, options, positionals, and subcommands.
            config: Configuration settings for the parser. If `None`, uses
                [`DEFAULT_PARSER_CONFIGURATION`][aclaf.parser.DEFAULT_PARSER_CONFIGURATION].
            **overrides: Individual configuration options to override the
                provided `config`. These correspond to the attributes of
                [`ParserConfiguration`][aclaf.parser.ParserConfiguration].
        """
        self._spec: CommandSpec = spec

        config = config or DEFAULT_PARSER_CONFIGURATION
        config = replace(config, **overrides) if overrides else config
        self._config: ParserConfiguration = config

    @property
    def spec(self) -> "CommandSpec":
        """The command specification for this parser."""
        return self._spec

    @property
    def config(self) -> ParserConfiguration:
        """The parser configuration for this parser."""
        return self._config

    @abstractmethod
    def parse(self, args: "Sequence[str]") -> "ParseResult":
        """Parse a sequence of command-line arguments.

        Args:
            args: The arguments to parse, typically from `sys.argv[1:]`.

        Returns:
            A [`ParseResult`][aclaf.parser.ParseResult] containing the parsed
            command, options, positionals, and any nested subcommand.

        Raises:
            [`ParseError`][aclaf.parser.ParseError]: If the arguments cannot
            be parsed according to the command specification and parser
            configuration.
        """
        ...
