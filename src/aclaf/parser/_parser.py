import re
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING, final, override

from ._base import BaseParser, ParsedOption, ParsedPositional, ParseResult
from ._parameters import PositionalSpec
from .constants import (
    DEFAULT_FALSEY_VALUES,
    DEFAULT_NEGATIVE_NUMBER_PATTERN,
    DEFAULT_TRUTHY_VALUES,
)
from .exceptions import (
    FlagWithValueError,
    InsufficientOptionValuesError,
    InsufficientPositionalArgumentsError,
    InvalidFlagValueError,
    OptionCannotBeSpecifiedMultipleTimesError,
    OptionDoesNotAcceptValueError,
    UnexpectedPositionalArgumentError,
    UnknownOptionError,
    UnknownSubcommandError,
)
from .types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    ZERO_OR_ONE_ARITY,
    AccumulationMode,
    Arity,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._command import CommandSpec
    from ._parameters import OptionSpec


@final
class _ShortOptionSpecParser:
    """State machine for parsing combined short options.

    This extracts the structure of a combined short option string like:
    - -abc (three flags)
    - -xvalue (option x with inline value)
    - -o=val (option o with equals-delimited value)

    The parser maintains parsing state and provides clean methods for each
    state transition, making the complex character-by-character parsing logic
    easier to understand and maintain.
    """

    def __init__(
        self,
        arg_without_dash: str,
        current_spec: "CommandSpec",
        allow_abbreviated_options: bool,  # noqa: FBT001 - Internal parser class
        case_insensitive_flags: bool,  # noqa: FBT001 - Internal parser class
        allow_equals_for_flags: bool,  # noqa: FBT001 - Internal parser class
    ):
        self.arg = arg_without_dash
        self.spec = current_spec
        self.allow_abbreviated = allow_abbreviated_options
        self.case_insensitive = case_insensitive_flags
        self.allow_equals = allow_equals_for_flags

        # State tracking
        self.position = 0
        self.option_specs: list[tuple[str, OptionSpec]] = []
        self.inline_value: str | None = None
        self.inline_value_from_equals = False
        self.last_option_spec: OptionSpec | None = None

    def parse(self) -> tuple[list[tuple[str, "OptionSpec"]], str | None, bool]:
        """Parse the short option string.

        Returns:
            Tuple of (option specs list, inline value if any, whether from =)
        """
        while self.position < len(self.arg) and self.inline_value is None:
            self._parse_next_character()

        return self.option_specs, self.inline_value, self.inline_value_from_equals

    def _parse_next_character(self) -> None:
        """Parse the next character in the option string."""
        char = self.arg[self.position]

        # Check for equals sign
        if char == "=":
            self._handle_equals_sign()
            return

        # Try to resolve as an option
        try:
            option_resolution = self._resolve_option(char)
        except UnknownOptionError:
            self._handle_unknown_option(char)
            return

        # Successfully resolved option
        self._handle_resolved_option(char, option_resolution)

    def _handle_equals_sign(self) -> None:
        """Handle = character indicating start of inline value."""
        self.position += 1
        self.inline_value = self.arg[self.position :]
        self.inline_value_from_equals = True

    def _resolve_option(self, char: str) -> tuple[str, "OptionSpec"]:
        """Resolve a character to an option spec.

        Args:
            char: Single character to resolve

        Returns:
            Tuple of (resolved option name, option spec)

        Raises:
            UnknownOptionError: If character doesn't resolve to known option
        """
        return self.spec.resolve_option(
            char,
            allow_abbreviations=self.allow_abbreviated,
            case_insensitive=self.case_insensitive,
        )

    def _handle_unknown_option(self, char: str) -> None:
        """Handle character that doesn't resolve to a known option.

        This may indicate the start of an inline value.

        Args:
            char: Unknown character

        Raises:
            UnknownOptionError: If truly unknown option
            OptionDoesNotAcceptValueError: If looks like value for zero-arity option
        """
        # If this is the first character, it's definitely unknown
        if self.position == 0:
            raise UnknownOptionError(
                char,
                tuple(self.spec.options.keys()),
            )

        # Check if previous option needs a value
        if self._previous_option_needs_value():
            self.inline_value = self.arg[self.position :]
            return

        # Check if this looks like an inline value attempt
        if self._looks_like_inline_value_attempt():
            # Previous option was ZERO_ARITY but user tried to provide value
            # last_option_spec is guaranteed to be non-None in this code path
            if self.last_option_spec is None:
                msg = "Unexpected state: last_option_spec is None"
                raise RuntimeError(msg)
            raise OptionDoesNotAcceptValueError(
                self.option_specs[-1][0],
                self.last_option_spec,
            ) from None

        # Unknown option character
        raise UnknownOptionError(
            char,
            tuple(self.spec.options.keys()),
        )

    def _previous_option_needs_value(self) -> bool:
        """Check if the previous option requires a value."""
        return bool(
            self.last_option_spec
            and self.last_option_spec.arity
            and self.last_option_spec.arity.min > 0
        )

    def _looks_like_inline_value_attempt(self) -> bool:
        """Check if remaining characters look like a value, not flags."""
        if not self.last_option_spec:
            return False

        if self.last_option_spec.arity != ZERO_ARITY:
            return False

        remaining = len(self.arg) - self.position
        min_chars_for_value = 2  # Need 2+ chars to look like value not flag

        return remaining > min_chars_for_value

    def _handle_resolved_option(
        self, char: str, option_resolution: tuple[str, "OptionSpec"]
    ) -> None:
        """Handle a successfully resolved option character.

        Args:
            char: The character that was resolved
            option_resolution: The (option_name, option_spec) tuple from resolution

        Raises:
            OptionDoesNotAcceptValueError: If zero-arity with = when not allowed
            InsufficientOptionValuesError: If value-required with ambiguous char
        """
        _, option_spec = option_resolution

        self.option_specs.append((char, option_spec))
        self.last_option_spec = option_spec
        self.position += 1

        # Check for zero-arity option followed by =
        if self._zero_arity_followed_by_equals(option_spec):
            # This would be handled in _zero_arity_followed_by_equals
            # Start inline value
            self.inline_value = self.arg[self.position + 1 :]
            self.inline_value_from_equals = True
            return

        # Check if this option requires values
        if self._option_requires_values_and_has_remaining(option_spec):
            self._handle_value_required_option()

    def _zero_arity_followed_by_equals(self, option_spec: "OptionSpec") -> bool:
        """Check if this is a zero-arity option followed by =.

        Args:
            option_spec: The option specification

        Returns:
            True if zero-arity followed by =

        Raises:
            OptionDoesNotAcceptValueError: If not allowed by configuration
        """
        if not (
            option_spec.arity == ZERO_ARITY
            and self.position < len(self.arg)
            and self.arg[self.position] == "="
        ):
            return False

        # Found zero-arity followed by =
        # Check if this is allowed by configuration
        if not self.allow_equals:
            raise OptionDoesNotAcceptValueError(self.option_specs[-1][0], option_spec)

        return True

    def _option_requires_values_and_has_remaining(
        self, option_spec: "OptionSpec"
    ) -> bool:
        """Check if option requires values and there are remaining characters."""
        return (
            not option_spec.is_flag
            and option_spec.arity is not None
            and option_spec.arity.min > 0
            and self.position < len(self.arg)
        )

    def _handle_value_required_option(self) -> None:
        """Handle an option that requires values with remaining characters.

        Raises:
            InsufficientOptionValuesError: If ambiguous single character remains
        """
        next_char = self.arg[self.position]

        # Explicit = means inline value
        if next_char == "=":
            self.inline_value = self.arg[self.position + 1 :]
            self.inline_value_from_equals = True
            return

        # Check if next char is a known option
        is_known_option = self._is_known_option(next_char)

        # If known option AND not first option AND only one char remaining
        # -> error (insufficient values)
        if self._is_ambiguous_single_char(is_known_option):
            current_option_name = self.option_specs[-1][0]
            current_option_spec = self.option_specs[-1][1]
            raise InsufficientOptionValuesError(
                current_option_name, current_option_spec
            )

        # Remaining characters are the inline value
        self.inline_value = self.arg[self.position :]

    def _is_known_option(self, char: str) -> bool:
        """Check if a character resolves to a known option."""
        try:
            _ = self.spec.resolve_option(
                char,
                allow_abbreviations=self.allow_abbreviated,
                case_insensitive=self.case_insensitive,
            )
        except UnknownOptionError:
            return False
        else:
            return True

    def _is_ambiguous_single_char(
        self,
        is_known_option: bool,  # noqa: FBT001 - Clear in context
    ) -> bool:
        """Check if remaining single char is ambiguous (flag vs value)."""
        remaining_chars = len(self.arg) - self.position
        has_previous_options = len(self.option_specs) > 1

        return is_known_option and has_previous_options and remaining_chars == 1


class _SubcommandParsedError(Exception):
    """Internal exception for early exit when subcommand is parsed.

    This exception is used for control flow within the parser when a subcommand
    is encountered. Since subcommand parsing is recursive and happens deep in
    the call stack, this exception allows us to unwind and return the result
    immediately without adding complex return value checking at each level.
    """

    result: "ParseResult"

    def __init__(self, result: "ParseResult") -> None:
        self.result = result
        super().__init__()


@final
class _ParsingContext:
    """Encapsulates state for parsing a single argument list.

    This class manages all mutable state during argument parsing, providing
    focused methods for each type of argument handling. By encapsulating the
    state machine, we achieve:

    - Clear separation of concerns (each method handles one argument type)
    - Flat control flow (no deep nesting)
    - Easier testing (can test classification logic independently)
    - Better maintainability (adding new argument types is straightforward)

    Note: This is an internal helper class that accesses Parser's protected
    methods. This is intentional and safe since it's tightly coupled to Parser.
    The reportPrivateUsage warnings are suppressed on individual method calls.
    """

    def __init__(
        self,
        args: "Sequence[str]",
        root_spec: "CommandSpec",
        command_path: "Sequence[str]",
        parser: "Parser",
    ) -> None:
        self.args = args
        self.root_spec = root_spec
        self.command_path = command_path
        self.parser = parser

        # Mutable parsing state
        self.current_spec = root_spec
        self.position = 0
        self.options: dict[str, ParsedOption] = {}
        self.positionals: tuple[str, ...] = ()
        self.positionals_started = False
        self.trailing_mode = False
        self.trailing_args: list[str] = []

    def parse(self) -> "ParseResult":
        """Parse all arguments and return result."""
        while self.position < len(self.args):
            self._parse_next_argument()

        return self._build_result()

    def _parse_next_argument(self) -> None:
        """Parse the next argument based on current state."""
        arg = self.args[self.position]

        if self.trailing_mode:
            self._handle_trailing_arg(arg)
        elif arg == "--":
            self._handle_double_dash()
        elif arg.startswith("--"):
            self._handle_long_option(arg)
        elif arg.startswith("-") and arg != "-":
            self._handle_short_option_or_negative(arg)
        else:
            self._handle_subcommand_or_positional(arg)

    def _handle_trailing_arg(self, arg: str) -> None:
        """Handle argument in trailing mode (after --)."""
        self.trailing_args.append(arg)
        self.position += 1

    def _handle_double_dash(self) -> None:
        """Handle -- separator (start trailing mode)."""
        self.trailing_mode = True
        self.position += 1

    def _handle_long_option(self, arg: str) -> None:
        """Handle long option like --option."""
        # Check if should treat as positional
        if self._should_treat_as_positional():
            self.positionals += (arg,)
            self.position += 1
            return

        # Parse as long option
        parsed_option, consumed = self.parser._parse_long_option(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            arg[2:],
            self.args[self.position + 1 :],
            self.current_spec,
            MappingProxyType(self.options),
        )
        self.options[parsed_option.name] = parsed_option
        self.position += 1 + consumed

    def _handle_short_option_or_negative(self, arg: str) -> None:
        """Handle short option or negative number like -o or -5."""
        # Check for negative number
        if self._is_negative_number(arg):
            self.positionals += (arg,)
            self.position += 1
            self.positionals_started = True
            return

        # Check if should treat as positional
        if self._should_treat_as_positional():
            self.positionals += (arg,)
            self.position += 1
            return

        # Parse as short option(s)
        parsed_options, consumed = self.parser._parse_short_options(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            arg[1:],
            self.args[self.position + 1 :],
            self.current_spec,
            MappingProxyType(self.options),
        )
        for parsed_option in parsed_options:
            self.options[parsed_option.name] = parsed_option
        self.position += 1 + consumed

    def _handle_subcommand_or_positional(self, arg: str) -> None:
        """Handle potential subcommand or positional argument."""
        # Try to resolve as subcommand
        if subcommand_resolution := self._try_resolve_subcommand(arg):
            self._handle_subcommand(subcommand_resolution)
            return

        # Check if unknown subcommand error should be raised
        if self._should_raise_unknown_subcommand():
            all_names = tuple(self.current_spec.subcommands.keys())
            raise UnknownSubcommandError(arg, all_names)

        # Treat as positional
        self.positionals += (arg,)
        self.position += 1
        self.positionals_started = True

    def _should_treat_as_positional(self) -> bool:
        """Check if option-like arg should be treated as positional."""
        # Strict mode: after positionals started, everything is positional
        if self.positionals_started and self.parser._strict_options_before_positionals:  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            return True

        # No options defined: everything is positional after first positional
        return self.positionals_started and not self.current_spec.options

    def _is_negative_number(self, arg: str) -> bool:
        """Check if arg is a negative number in value context."""
        return (
            self.parser._allow_negative_numbers  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            and self.parser._is_negative_number(arg)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            and self.parser._in_value_consuming_context(self.current_spec)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        )

    def _try_resolve_subcommand(self, arg: str) -> tuple[str, "CommandSpec"] | None:
        """Try to resolve arg as a subcommand."""
        return self.current_spec.resolve_subcommand(
            arg,
            allow_aliases=self.parser.allow_aliases,
            allow_abbreviations=self.parser.allow_abbreviated_subcommands,
            case_insensitive=self.parser.case_insensitive_subcommands,
            minimum_abbreviation_length=self.parser.minimum_abbreviation_length,
        )

    def _should_raise_unknown_subcommand(self) -> bool:
        """Check if unknown subcommand error should be raised."""
        return (
            bool(self.current_spec.subcommands)
            and not self.positionals_started
            and not self.current_spec.positionals
        )

    def _handle_subcommand(self, resolution: tuple[str, "CommandSpec"]) -> None:
        """Handle a resolved subcommand (raises _SubcommandParsed to exit parsing)."""
        matched_name, subcommand_spec = resolution

        # Parse subcommand recursively
        subcommand_result = self.parser._parse_argument_list(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            self.args[self.position + 1 :],
            subcommand_spec,
            command_path=(*self.command_path, subcommand_spec.name),
        )

        # Set alias if one was used
        if matched_name != subcommand_spec.name:
            subcommand_result = replace(subcommand_result, alias=matched_name)

        # Build and return result (raises to exit parsing)
        result = ParseResult(
            command=self.current_spec.name,
            options=self.options,
            positionals=self.parser._group_positionals(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
                self.positionals, self.current_spec
            ),
            extra_args=tuple(self.trailing_args),
            subcommand=subcommand_result,
        )

        # Raise special exception to exit parsing early
        raise _SubcommandParsedError(result)

    def _build_result(self) -> "ParseResult":
        """Build final parse result."""
        return ParseResult(
            command=self.current_spec.name,
            options=self.options,
            positionals=self.parser._group_positionals(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
                self.positionals, self.current_spec
            ),
            extra_args=tuple(self.trailing_args),
        )


@final
class Parser(BaseParser):
    """Concrete implementation of the command-line argument parser.

    The Parser class implements the complete parsing algorithm, processing
    command-line arguments according to a CommandSpec and parser configuration.
    It performs single-pass, left-to-right parsing with support for:

    - Long options (--option) and short options (-o)
    - Combined short options (-abc)
    - Option values with various arities
    - Positional arguments with flexible grouping
    - Nested subcommands
    - Inline values (--option=value)
    - Negation words (--no-flag)
    - Trailing arguments after '--'

    The parser is immutable and thread-safe. All configuration is provided
    during initialization through the BaseParser constructor.
    """

    @override
    def parse(self, args: "Sequence[str]") -> "ParseResult":
        return self._parse_argument_list(
            args, self.spec, command_path=(self.spec.name,)
        )

    def _parse_argument_list(
        self,
        args: "Sequence[str]",
        root_spec: "CommandSpec",
        command_path: "Sequence[str]",
    ) -> "ParseResult":
        """Parse a list of command-line arguments.

        This method creates a parsing context and delegates to it for the actual
        parsing work. The context encapsulates all mutable state and provides
        focused methods for each argument type.

        Args:
            args: The argument list to parse
            root_spec: The command specification to parse against
            command_path: The command path (for nested subcommands)

        Returns:
            The parse result containing options, positionals, and subcommand

        Raises:
            UnknownOptionError: If an unknown option is encountered
            UnknownSubcommandError: If an unknown subcommand is encountered
            Various validation errors: If argument validation fails
        """
        try:
            context = _ParsingContext(
                args=args,
                root_spec=root_spec,
                command_path=command_path,
                parser=self,
            )
            return context.parse()
        except _SubcommandParsedError as e:
            return e.result

    def _resolve_subcommand(
        self, arg: str, current_spec: "CommandSpec"
    ) -> tuple[str, "CommandSpec"] | None:
        """Resolve argument as a subcommand using parser configuration.

        Args:
            arg: The argument to resolve.
            current_spec: Current command specification.

        Returns:
            Tuple of (matched_name, subcommand_spec) or None if no match.
        """
        return current_spec.resolve_subcommand(
            arg,
            allow_aliases=self.allow_aliases,
            allow_abbreviations=self.allow_abbreviated_subcommands,
            case_insensitive=self.case_insensitive_subcommands,
            minimum_abbreviation_length=self.minimum_abbreviation_length,
        )

    def _resolve_long_option(
        self, option_name: str, current_spec: "CommandSpec"
    ) -> tuple[str, "OptionSpec"]:
        """Resolve long option name using parser configuration.

        Args:
            option_name: The option name to resolve (without -- prefix).
            current_spec: Current command specification.

        Returns:
            Tuple of (matched_name, option_spec).

        Raises:
            UnknownOptionError: If option cannot be resolved.
        """
        return current_spec.resolve_option(
            option_name,
            allow_abbreviations=self.allow_abbreviated_options,
            case_insensitive=self.case_insensitive_options,
            convert_underscores=self.convert_underscores_to_dashes,
            minimum_abbreviation_length=self.minimum_abbreviation_length,
        )

    def _parse_long_option(  # noqa: PLR0912 - Complex long option parsing logic
        self,
        arg_without_dashes: str,
        next_args: "Sequence[str]",
        current_spec: "CommandSpec",
        options: MappingProxyType[str, ParsedOption],
    ) -> tuple[ParsedOption, int]:
        parts = arg_without_dashes.split("=", 1)
        option_name, option_spec = self._resolve_long_option(parts[0], current_spec)
        inline_value = parts[1] if len(parts) == 2 else None  # noqa: PLR2004
        parsed_option: ParsedOption
        consumed: int = 0

        match (option_spec.is_flag, option_spec.arity, inline_value, bool(next_args)):
            # Flag with value and flag values not allowed
            case (True, _, str(), _) if not self.allow_equals_for_flags:
                raise FlagWithValueError(option_spec.name, option_spec)

            # Flag with inline value and flag values allowed
            case (True, _, str(), _) if self.allow_equals_for_flags:
                parsed_option, consumed = self._parse_flag_with_value(
                    option_spec, option_name, inline_value, next_args
                )

            # Flag with value from next_args and flag values allowed
            case (True, _, None, True) if self.allow_equals_for_flags:
                parsed_option, consumed = self._parse_flag_with_value(
                    option_spec, option_name, inline_value, next_args
                )

            # Flag without value and const value defined
            case (True, _, None, _) if option_spec.const_value is not None:
                parsed_option, consumed = (
                    ParsedOption(
                        name=option_spec.name,
                        alias=option_name,
                        value=option_spec.const_value,
                    ),
                    0,
                )

            # Flag without value and negation words defined
            case (True, _, None, _) if option_spec.negation_words:
                for negation_word in option_spec.negation_words:
                    negated_prefix = f"{negation_word}-"
                    if option_name.startswith(negated_prefix):
                        return ParsedOption(
                            name=option_spec.name, alias=option_name, value=False
                        ), 0
                parsed_option, consumed = (
                    ParsedOption(name=option_spec.name, alias=option_name, value=True),
                    0,
                )

            # Flag without value and no const value or negation words
            case (True, _, None, _):
                parsed_option, consumed = (
                    ParsedOption(name=option_spec.name, alias=option_name, value=True),
                    0,
                )

            # Arity requires multiple values but only has inline value
            case (False, arity, str(), _) if arity and arity.min > 1:
                raise InsufficientOptionValuesError(option_spec.name, option_spec)

            # Arity allows multiple values
            case (False, arity, str() as val, _) if (
                arity and self._arity_accepts_values(arity)
            ):
                parsed_option, consumed = (
                    self._parse_option_from_inline_value(option_spec, option_name, val),
                    0,
                )

            # Consume values from next_args
            case (False, arity, None, _) if arity and self._arity_accepts_values(arity):
                parsed_option, consumed = self._parse_option_values_from_args(
                    option_spec, option_name, next_args, current_spec
                )

            # Zero arity with inline value
            case (False, arity, str() as val, _) if _is_zero_arity(arity):
                # Zero-arity non-flag options with values
                # If allow_equals_for_flags is enabled, treat as flag value
                if self.allow_equals_for_flags and val:
                    parsed_option, consumed = self._parse_flag_with_value(
                        option_spec, option_name, val, next_args
                    )
                # Empty value raises OptionDoesNotAcceptValueError
                elif val == "":
                    raise OptionDoesNotAcceptValueError(option_name, option_spec)
                # Non-empty value raises FlagWithValueError (attempting to use as flag)
                else:
                    raise FlagWithValueError(option_name, option_spec)

            # Zero arity without value
            case (False, arity, None, _) if _is_zero_arity(arity):
                # Check for const value first
                if option_spec.const_value is not None:
                    parsed_option, consumed = (
                        ParsedOption(
                            name=option_spec.name,
                            alias=option_name,
                            value=option_spec.const_value,
                        ),
                        0,
                    )
                # Check for negation words
                elif option_spec.negation_words:
                    for negation_word in option_spec.negation_words:
                        negated_prefix = f"{negation_word}-"
                        if option_name.startswith(negated_prefix):
                            parsed_option, consumed = (
                                ParsedOption(
                                    name=option_spec.name,
                                    alias=option_name,
                                    value=False,
                                ),
                                0,
                            )
                            break
                    else:
                        # No negation prefix matched, default to True
                        parsed_option, consumed = (
                            ParsedOption(
                                name=option_spec.name,
                                alias=option_name,
                                value=True,
                            ),
                            0,
                        )
                else:
                    parsed_option, consumed = (
                        ParsedOption(
                            name=option_spec.name,
                            alias=option_name,
                            value=True,
                        ),
                        0,
                    )

            case _:
                msg = (
                    f"Unexpected long option parsing state: "
                    f"is_flag={option_spec.is_flag}, arity={option_spec.arity}, "
                    f"inline_value={inline_value!r}, has_next_args={bool(next_args)}"
                )
                raise RuntimeError(msg)

        accumulated_option = self._accumulate_option(
            options.get(parsed_option.name), parsed_option, current_spec
        )
        return accumulated_option, consumed

    def _parse_short_options(
        self,
        arg_without_dash: str,
        next_args: "Sequence[str]",
        current_spec: "CommandSpec",
        options: MappingProxyType[str, ParsedOption],
    ) -> tuple[tuple[ParsedOption, ...], int]:
        """Parse combined short options like -abc or -xvalue.

        Args:
            arg_without_dash: Short option string without leading dash
            next_args: Remaining arguments after this short option
            current_spec: Current command specification
            options: Previously parsed options for accumulation

        Returns:
            Tuple of (parsed and accumulated options, next_args consumed)
        """
        # Extract specs and inline value (delegation)
        option_specs, inline_value, inline_value_from_equals = (
            self._extract_short_option_specs(arg_without_dash, current_spec)
        )

        # Parse each option (delegation)
        parsed_options, next_args_consumed = self._parse_extracted_short_options(
            option_specs,
            inline_value,
            inline_value_from_equals,
            next_args,
            current_spec,
        )

        # Accumulate combined flags (delegation)
        accumulated_options = self._accumulate_short_options(
            parsed_options, options, current_spec
        )

        return accumulated_options, next_args_consumed

    def _parse_extracted_short_options(
        self,
        option_specs: list[tuple[str, "OptionSpec"]],
        inline_value: str | None,
        inline_value_from_equals: bool,  # noqa: FBT001 - Clear in context
        next_args: "Sequence[str]",
        current_spec: "CommandSpec",
    ) -> tuple[list[ParsedOption], int]:
        """Parse a list of extracted short option specs into ParsedOptions.

        Args:
            option_specs: List of (option_name, option_spec) tuples
            inline_value: Inline value from combined option (e.g., 'value' from -xvalue)
            inline_value_from_equals: Whether inline value came from = syntax
            next_args: Remaining arguments
            current_spec: Current command specification

        Returns:
            Tuple of (parsed options list, next_args consumed count)
        """
        parsed_options: list[ParsedOption] = []
        next_args_consumed = 0

        for index, (option_name, option_spec) in enumerate(option_specs):
            is_last = index == len(option_specs) - 1

            if not is_last:
                # Inner option (simpler logic)
                parsed_option = self._parse_inner_short_option(option_name, option_spec)
                parsed_options.append(parsed_option)
            else:
                # Last option (more complex - can consume values)
                parsed_option, consumed = self._parse_last_short_option(
                    option_name,
                    option_spec,
                    inline_value,
                    inline_value_from_equals,
                    next_args,
                    current_spec,
                )
                parsed_options.append(parsed_option)
                next_args_consumed += consumed

        return parsed_options, next_args_consumed

    def _parse_inner_short_option(
        self,
        option_name: str,
        option_spec: "OptionSpec",
    ) -> ParsedOption:
        """Parse a short option that is not the last in a combined string.

        Inner options can only be flags or zero-arity options since they
        cannot consume values.

        Args:
            option_name: The single-character option name
            option_spec: The option specification

        Returns:
            Parsed option with appropriate value

        Raises:
            InsufficientOptionValuesError: If option requires values
        """
        # Flag with const_value
        if option_spec.is_flag and option_spec.const_value is not None:
            return ParsedOption(
                name=option_spec.name,
                alias=option_name,
                value=option_spec.const_value,
            )

        # Flag without const_value
        if option_spec.is_flag:
            return ParsedOption(
                name=option_spec.name,
                alias=option_name,
                value=True,
            )

        arity = option_spec.arity or ZERO_OR_MORE_ARITY

        # Zero arity with const_value
        if _is_zero_arity(arity) and option_spec.const_value is not None:
            return ParsedOption(
                name=option_spec.name,
                alias=option_name,
                value=option_spec.const_value,
            )

        # Zero arity without const_value
        if _is_zero_arity(arity):
            return ParsedOption(
                name=option_spec.name,
                alias=option_name,
                value=True,
            )

        # Requires values (error case)
        if arity.min > 0:
            raise InsufficientOptionValuesError(option_spec.name, option_spec)

        # Should not reach here
        msg = f"Unexpected inner short option state: {option_spec.name}"
        raise RuntimeError(msg)

    def _parse_last_short_option(  # noqa: PLR0913 - Refactored helper
        self,
        option_name: str,
        option_spec: "OptionSpec",
        inline_value: str | None,
        inline_value_from_equals: bool,  # noqa: FBT001 - Clear in context
        next_args: "Sequence[str]",
        current_spec: "CommandSpec",
    ) -> tuple[ParsedOption, int]:
        """Parse the last short option in a combined string.

        The last option can consume values from inline or next_args.

        Args:
            option_name: The single-character option name
            option_spec: The option specification
            inline_value: Inline value if present
            inline_value_from_equals: Whether inline value came from =
            next_args: Remaining arguments
            current_spec: Current command specification

        Returns:
            Tuple of (parsed option, next_args consumed)
        """
        # Flag options
        if option_spec.is_flag:
            return self._parse_last_short_option_flag(
                option_name, option_spec, inline_value, next_args
            )

        # Zero-arity non-flag options
        arity = option_spec.arity or ZERO_OR_MORE_ARITY
        if _is_zero_arity(arity):
            return self._parse_last_short_option_zero_arity(
                option_name, option_spec, inline_value, next_args
            )

        # Value-consuming options
        return self._parse_last_short_option_with_values(
            option_name,
            option_spec,
            inline_value,
            inline_value_from_equals,
            next_args,
            current_spec,
        )

    def _parse_last_short_option_flag(
        self,
        option_name: str,
        option_spec: "OptionSpec",
        inline_value: str | None,
        next_args: "Sequence[str]",
    ) -> tuple[ParsedOption, int]:
        """Parse a flag as the last short option.

        Args:
            option_name: The single-character option name
            option_spec: The option specification (must be a flag)
            inline_value: Inline value if present
            next_args: Remaining arguments

        Returns:
            Tuple of (parsed option, next_args consumed)

        Raises:
            FlagWithValueError: If flag has inline value and flag values not allowed
        """
        # Flag with inline value when allowed
        if inline_value is not None and self.allow_equals_for_flags:
            return self._parse_flag_with_value(
                option_spec, option_name, inline_value, next_args
            )

        # Flag from next_args when allowed
        if inline_value is None and next_args and self.allow_equals_for_flags:
            return self._parse_flag_with_value(
                option_spec, option_name, None, next_args
            )

        # Flag with inline value when not allowed
        if inline_value is not None and not self.allow_equals_for_flags:
            raise FlagWithValueError(option_spec.name, option_spec)

        # Flag with const_value
        if option_spec.const_value is not None:
            return ParsedOption(
                name=option_spec.name,
                alias=option_name,
                value=option_spec.const_value,
            ), 0

        # Simple flag
        return ParsedOption(
            name=option_spec.name,
            alias=option_name,
            value=True,
        ), 0

    def _parse_last_short_option_zero_arity(
        self,
        option_name: str,
        option_spec: "OptionSpec",
        inline_value: str | None,
        next_args: "Sequence[str]",
    ) -> tuple[ParsedOption, int]:
        """Parse a zero-arity option as the last short option.

        Args:
            option_name: The single-character option name
            option_spec: The option specification (must have zero arity)
            inline_value: Inline value if present
            next_args: Remaining arguments

        Returns:
            Tuple of (parsed option, next_args consumed)

        Raises:
            OptionDoesNotAcceptValueError: If inline value provided when not allowed
        """
        # With inline value and flag values allowed
        if inline_value is not None and self.allow_equals_for_flags:
            return self._parse_flag_with_value(
                option_spec, option_name, inline_value, next_args
            )

        # With inline value and flag values not allowed
        if inline_value is not None:
            raise OptionDoesNotAcceptValueError(option_spec.name, option_spec)

        # Without inline value and with const_value
        if option_spec.const_value is not None:
            return ParsedOption(
                name=option_spec.name,
                alias=option_name,
                value=option_spec.const_value,
            ), 0

        # Without inline value and without const_value
        return ParsedOption(
            name=option_spec.name,
            alias=option_name,
            value=True,
        ), 0

    def _parse_last_short_option_with_values(  # noqa: PLR0913 - Refactored helper
        self,
        option_name: str,
        option_spec: "OptionSpec",
        inline_value: str | None,
        inline_value_from_equals: bool,  # noqa: FBT001 - Clear in context
        next_args: "Sequence[str]",
        current_spec: "CommandSpec",
    ) -> tuple[ParsedOption, int]:
        """Parse a value-consuming option as the last short option.

        Args:
            option_name: The single-character option name
            option_spec: The option specification
            inline_value: Inline value if present
            inline_value_from_equals: Whether inline value came from =
            next_args: Remaining arguments
            current_spec: Current command specification

        Returns:
            Tuple of (parsed option, next_args consumed)

        Raises:
            InsufficientOptionValuesError: If not enough values provided
        """
        arity = option_spec.arity or ZERO_OR_MORE_ARITY

        # Inline value from = syntax (only use inline, don't consume next_args)
        if inline_value is not None and inline_value_from_equals:
            if arity.min > 1:
                raise InsufficientOptionValuesError(option_spec.name, option_spec)
            parsed_option = self._parse_option_from_inline_value(
                option_spec, option_name, inline_value
            )
            return parsed_option, 0

        # Inline value (not from =) with unbounded arity - continue from next_args
        if (
            inline_value is not None
            and not inline_value_from_equals
            and arity.max is None
        ):
            parsed_option, consumed = self._parse_option_values_from_args(
                option_spec,
                option_name,
                next_args,
                current_spec,
                inline_start_value=inline_value,
            )
            return parsed_option, consumed

        # Inline value (not from =) without next_args
        if inline_value is not None and not inline_value_from_equals:
            if arity.min > 1:
                raise InsufficientOptionValuesError(option_spec.name, option_spec)
            parsed_option = self._parse_option_from_inline_value(
                option_spec, option_name, inline_value
            )
            return parsed_option, 0

        # No inline value - consume from next_args
        parsed_option, consumed = self._parse_option_values_from_args(
            option_spec, option_name, next_args, current_spec
        )
        return parsed_option, consumed

    def _accumulate_short_options(
        self,
        parsed_options: list[ParsedOption],
        options: MappingProxyType[str, ParsedOption],
        current_spec: "CommandSpec",
    ) -> tuple[ParsedOption, ...]:
        """Accumulate parsed short options, handling combined flags like -vvv.

        This threads accumulated values through for proper COUNT mode handling.

        Args:
            parsed_options: List of parsed options to accumulate
            options: Previously parsed options dict
            current_spec: Current command specification

        Returns:
            Tuple of accumulated options
        """
        accumulated_dict: dict[str, ParsedOption] = {}
        accumulated_options: list[ParsedOption] = []

        for parsed_option in parsed_options:
            # Get the old value: first check local accumulation, then original dict
            old = accumulated_dict.get(parsed_option.name) or options.get(
                parsed_option.name
            )
            accumulated = self._accumulate_option(old, parsed_option, current_spec)
            accumulated_dict[accumulated.name] = accumulated
            accumulated_options.append(accumulated)

        return tuple(accumulated_options)

    def _extract_short_option_specs(
        self, arg_without_dash: str, current_spec: "CommandSpec"
    ) -> tuple[list[tuple[str, "OptionSpec"]], str | None, bool]:
        """Extract short option specs from a combined short option string.

        Examples:
            -abc -> [a, b, c], None, False
            -xvalue -> [x], "value", False
            -o=val -> [o], "val", True

        Args:
            arg_without_dash: Short option string without leading dash
            current_spec: Current command specification

        Returns:
            Tuple of (option specs list, inline value if any, whether from =)
        """
        parser = _ShortOptionSpecParser(
            arg_without_dash=arg_without_dash,
            current_spec=current_spec,
            allow_abbreviated_options=self.allow_abbreviated_options,
            case_insensitive_flags=self.case_insensitive_flags,
            allow_equals_for_flags=self.allow_equals_for_flags,
        )
        return parser.parse()

    def _parse_flag_with_value(
        self,
        option_spec: "OptionSpec",
        option_name: str,
        inline_value: str | None,
        next_args: "Sequence[str]",
    ) -> tuple[ParsedOption, int]:
        truthy = frozenset(
            option_spec.truthy_flag_values
            or self.truthy_flag_values
            or DEFAULT_TRUTHY_VALUES
        )
        falsey = frozenset(
            option_spec.falsey_flag_values
            or self.falsey_flag_values
            or DEFAULT_FALSEY_VALUES
        )

        if inline_value == "":
            raise InvalidFlagValueError(
                option_spec.name, inline_value, option_spec, truthy, falsey
            )

        value = inline_value or (next_args[0] if next_args else None)

        match value:
            case v if v in truthy:
                return ParsedOption(
                    name=option_spec.name, alias=option_name, value=True
                ), (0 if inline_value else 1)
            case v if v in falsey:
                return ParsedOption(
                    name=option_spec.name, alias=option_name, value=False
                ), (0 if inline_value else 1)
            case str() if inline_value is not None:
                # Invalid inline value - must raise error
                raise InvalidFlagValueError(
                    option_spec.name, value, option_spec, truthy, falsey
                )
            case str():
                # Invalid value from next_args - don't consume, just return True
                return ParsedOption(
                    name=option_spec.name, alias=option_name, value=True
                ), 0
            case _:
                msg = (
                    f"Unexpected flag value state: value={value!r}, "
                    f"inline_value={inline_value!r}, next_args={bool(next_args)}"
                )
                raise RuntimeError(msg)

    def _parse_option_from_inline_value(
        self, option_spec: "OptionSpec", option_name: str, value: str
    ) -> ParsedOption:
        # For options with single-value arities and non-accumulating modes,
        # return scalars
        if option_spec.arity in (
            EXACTLY_ONE_ARITY,
            ZERO_OR_ONE_ARITY,
        ) and option_spec.accumulation_mode in (
            AccumulationMode.FIRST_WINS,
            AccumulationMode.LAST_WINS,
            AccumulationMode.ERROR,
        ):
            parsed_value = value
        else:
            parsed_value = (value,)

        return ParsedOption(
            name=option_spec.name, alias=option_name, value=parsed_value
        )

    def _parse_option_values_from_args(  # noqa: PLR0912 - Complex value parsing logic
        self,
        option_spec: "OptionSpec",
        option_name: str,
        next_args: "Sequence[str]",
        current_spec: "CommandSpec",
        inline_start_value: str | None = None,
    ) -> tuple[ParsedOption, int]:
        arity = option_spec.arity or ZERO_OR_MORE_ARITY

        # If we have an inline start value, we already have one value
        values_already_collected = 1 if inline_start_value is not None else 0
        remaining_min = max(0, arity.min - values_already_collected)

        if len(next_args) < remaining_min:
            raise InsufficientOptionValuesError(option_spec.name, option_spec)

        # Calculate minimum required positional arguments
        # This prevents options from consuming values needed by required positionals
        min_positionals_required = sum(
            spec.arity.min for spec in current_spec.positionals.values()
        )

        values: list[str] = (
            [inline_start_value] if inline_start_value is not None else []
        )
        consumed = 0

        while consumed < len(next_args):
            # Check if we've reached the maximum arity
            # (accounting for values already collected)
            if arity.max is not None and (len(values) >= arity.max):
                break

            current_value = next_args[consumed]
            if current_value.startswith("-") and current_value != "-":
                # If negative numbers enabled and matches pattern, consume as value
                if self._allow_negative_numbers and self._is_negative_number(
                    current_value
                ):
                    # Continue to consume as value
                    pass
                else:
                    # Stop consuming (potential option)
                    break

            if self._resolve_subcommand(current_value, current_spec):
                break

            # Check if consuming this value would violate positional requirements
            # Count remaining non-option, non-subcommand args after this consumption
            remaining_after_consume = 0
            for arg in next_args[consumed + 1 :]:
                # Check if this is an option (not a negative number or single dash)
                if (
                    arg.startswith("-")
                    and arg != "-"
                    and not (
                        self._allow_negative_numbers and self._is_negative_number(arg)
                    )
                ):
                    break
                if self._resolve_subcommand(arg, current_spec):
                    break
                remaining_after_consume += 1

            # If consuming this value would not leave enough for required positionals,
            # stop consuming (unless we haven't met the option's minimum yet)
            # We need to leave AT LEAST min_positionals_required args for positionals
            if (
                min_positionals_required > 0
                and remaining_after_consume < min_positionals_required
                and len(values) >= arity.min
            ):
                break

            values.append(current_value)
            consumed += 1

        if len(values) < arity.min:
            raise InsufficientOptionValuesError(option_spec.name, option_spec)

        # For options with single-value arities and non-accumulating modes,
        # return scalars
        if option_spec.arity in (
            EXACTLY_ONE_ARITY,
            ZERO_OR_ONE_ARITY,
        ) and option_spec.accumulation_mode in (
            AccumulationMode.FIRST_WINS,
            AccumulationMode.LAST_WINS,
            AccumulationMode.ERROR,
        ):
            # For ZERO_OR_ONE_ARITY with no values, return empty tuple
            parsed_value = values[0] if values else ()
        else:
            parsed_value = tuple(values)

        return ParsedOption(
            name=option_spec.name, alias=option_name, value=parsed_value
        ), consumed

    def _group_positionals(
        self, positionals: tuple[str, ...], current_spec: "CommandSpec"
    ) -> dict[str, ParsedPositional]:
        # Handle implicit positional spec (when no positionals defined)
        if not current_spec.positionals:
            # Implicit spec with unbounded arity (0, -1)
            implicit_spec = PositionalSpec(name="args", arity=ZERO_OR_MORE_ARITY)
            return {
                implicit_spec.name: ParsedPositional(
                    name=implicit_spec.name, value=positionals
                )
            }

        positional_specs = list(current_spec.positionals.values())
        total_min_required = sum(spec.arity.min for spec in positional_specs)

        # Check if we have enough arguments
        if len(positionals) < total_min_required:
            # Find the first unsatisfied spec for error reporting
            consumed = 0
            for spec in positional_specs:
                remaining = len(positionals) - consumed
                if remaining < spec.arity.min:
                    raise InsufficientPositionalArgumentsError(
                        spec.name, spec.arity.min, remaining
                    )
                consumed += spec.arity.min

        grouped: dict[str, ParsedPositional] = {}
        remaining_positionals = list(positionals)

        for spec_index, current_positional_spec in enumerate(positional_specs):
            max_allowed = current_positional_spec.arity.max

            subsequent_min = sum(
                s.arity.min for s in positional_specs[spec_index + 1 :]
            )

            if max_allowed is None:
                # Unbounded arity
                to_consume = max(0, len(remaining_positionals) - subsequent_min)
            else:
                # Bounded arity
                available = max(0, len(remaining_positionals) - subsequent_min)
                to_consume = min(max_allowed, available)

            consumed_values = remaining_positionals[:to_consume]
            remaining_positionals = remaining_positionals[to_consume:]

            # For EXACTLY_ONE arity, return scalar string; otherwise tuple
            if current_positional_spec.arity == EXACTLY_ONE_ARITY:
                parsed_value: str | tuple[str, ...] = (
                    consumed_values[0] if consumed_values else ""
                )
            else:
                parsed_value = tuple(consumed_values)

            grouped[current_positional_spec.name] = ParsedPositional(
                name=current_positional_spec.name, value=parsed_value
            )

        # Check for unexpected leftover positionals only in strict mode
        # In strict mode, options after positionals are treated as positionals
        # and should raise an error if they don't fit the spec
        if remaining_positionals and self._strict_options_before_positionals:
            raise UnexpectedPositionalArgumentError(
                remaining_positionals[0], current_spec.name
            )

        return grouped

    def _accumulate_option(  # noqa: PLR0912 - Complex accumulation logic for different modes
        self, old: ParsedOption | None, new: ParsedOption, current_spec: "CommandSpec"
    ):
        option_spec = current_spec.options[new.name]
        accumulated_option: ParsedOption
        match (option_spec.accumulation_mode, old):
            case (AccumulationMode.FIRST_WINS, ParsedOption()):
                accumulated_option = old
            case (AccumulationMode.FIRST_WINS, None):
                accumulated_option = new

            case (AccumulationMode.LAST_WINS, _):
                accumulated_option = new

            case (AccumulationMode.COLLECT, None):
                # First occurrence: wrap in tuple to establish collection structure
                # Different handling based on what type of value we have:
                # - Scalar (bool/str from flags or const_value): wrap in tuple
                # - Tuple from single-value option (max=1) with COLLECT: keep as-is
                # - Tuple from multi-value option (max>1 or unbounded):
                #   wrap in outer tuple
                arity = option_spec.arity or ZERO_OR_MORE_ARITY
                # For COLLECT mode first occurrence:
                # - Scalar values: wrap in tuple
                # - Multi-value tuples (max > 1): wrap in outer tuple for grouping
                # - Single-value tuples (max = 1): keep as-is (already a tuple)
                if not isinstance(new.value, tuple) or _is_multi_value_arity(arity):
                    # Wrap scalar or multi-value tuple
                    # Type checker can't handle dynamic tuple construction
                    accumulated_option = ParsedOption(
                        name=new.name,
                        alias=new.alias,
                        value=(new.value,),  # pyright: ignore[reportArgumentType]
                    )
                else:
                    # Single-value option (max=1): value is already a tuple
                    accumulated_option = new
            case (AccumulationMode.COLLECT, ParsedOption()):
                # Subsequent occurrences: append to the collection
                # Check if this is a multi-value option to preserve grouping
                # Type checker can't handle dynamic tuple construction for COLLECT mode
                arity = option_spec.arity or ZERO_OR_MORE_ARITY
                if not isinstance(new.value, tuple):
                    # Scalar value: append directly
                    value = (*old.value, new.value)  # pyright: ignore[reportGeneralTypeIssues,reportUnknownVariableType]
                elif _is_multi_value_arity(arity):
                    # Multi-value option: append the tuple as a single element
                    value = (*old.value, new.value)  # pyright: ignore[reportGeneralTypeIssues,reportUnknownVariableType]
                else:
                    # Single-value option (max=1): unwrap and merge
                    value = (*old.value, *new.value)  # pyright: ignore[reportGeneralTypeIssues,reportUnknownVariableType]
                accumulated_option = ParsedOption(
                    name=new.name,
                    alias=new.alias,
                    value=value,  # pyright: ignore[reportArgumentType]
                )

            case (AccumulationMode.COUNT, None):
                count = 1 if new.value else 0
                accumulated_option = ParsedOption(
                    name=new.name, alias=new.alias, value=count
                )
            case (AccumulationMode.COUNT, ParsedOption(value=int() as old_count)):
                count = old_count + (1 if new.value else 0)
                accumulated_option = ParsedOption(
                    name=new.name, alias=new.alias, value=count
                )

            case (AccumulationMode.ERROR, None):
                accumulated_option = new
            case (AccumulationMode.ERROR, ParsedOption()):
                raise OptionCannotBeSpecifiedMultipleTimesError(
                    option_spec.name, option_spec
                )

            case _:
                msg = (
                    f"Unexpected option accumulation state: "
                    f"mode={option_spec.accumulation_mode}, "
                    f"old={old}"
                )
                raise RuntimeError(msg)
        return accumulated_option

    @staticmethod
    def _arity_accepts_values(arity: "Arity") -> bool:
        return (
            arity.min > 0
            or (arity.min == 0 and arity.max is None)
            or (arity.min == 0 and arity.max is not None and arity.max > 0)
        )

    def _is_negative_number(self, arg: str) -> bool:
        """Check if argument matches negative number pattern.

        Args:
            arg: The argument to check.

        Returns:
            True if argument matches the negative number pattern.
        """
        pattern = self._negative_number_pattern or DEFAULT_NEGATIVE_NUMBER_PATTERN
        return bool(re.match(pattern, arg))

    def _in_value_consuming_context(
        self,
        current_spec: "CommandSpec",
    ) -> bool:
        """Check if parser is in a context where values are expected.

        This determines whether a negative-number-like argument should be
        treated as a value rather than as an option.

        Args:
            current_spec: The current command specification.

        Returns:
            True if in a context that expects values (positional arguments).
        """
        # Spec allows positionals (either already started or can start now)
        return bool(current_spec.positionals)


# Helper functions for arity checking


def _is_zero_arity(arity: "Arity | None") -> bool:
    """Check if arity represents zero arguments (0, 0).

    Args:
        arity: The arity specification to check, or None.

    Returns:
        True if arity is exactly (0, 0), False otherwise.
    """
    return arity is not None and arity.min == 0 and arity.max == 0


def _is_multi_value_arity(arity: "Arity | None") -> bool:
    """Check if arity allows multiple values (max > 1 or unbounded).

    Args:
        arity: The arity specification to check, or None.

    Returns:
        True if arity allows multiple values, False otherwise.
    """
    return arity is not None and (arity.max is None or arity.max > 1)
