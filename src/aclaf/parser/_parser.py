import re
from dataclasses import replace
from itertools import chain
from typing import TYPE_CHECKING, cast, final
from typing_extensions import override

from ._base import BaseParser, ParsedOption, ParsedPositional, ParseResult
from ._parameters import PositionalSpec
from .constants import (
    DEFAULT_FALSEY_VALUES,
    DEFAULT_NEGATIVE_NUMBER_PATTERN,
    DEFAULT_TRUTHY_VALUES,
)
from .exceptions import (
    DuplicateOptionError,
    FlagWithValueError,
    InsufficientOptionValuesError,
    InsufficientPositionalArgumentsError,
    InvalidFlagValueError,
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
class Parser(BaseParser):
    """Concrete implementation of the command-line argument parser.

    The Parser class implements the complete parsing algorithm, processing
    command-line arguments according to a [`CommandSpec`][aclaf.parser.CommandSpec]
    and parser configuration. It performs single-pass, left-to-right parsing
    with support for:

    - Long options (`--option`) and short options (`-o`)
    - Combined short options (`-abc`)
    - Option values with various arities
    - Positional arguments with flexible grouping
    - Nested subcommands
    - Inline values (`--option=value`)
    - Negation words (`--no-flag`)
    - Trailing arguments after `--`

    The parser is immutable and thread-safe. All configuration is provided
    during initialization through the BaseParser constructor.
    """

    @override
    def parse(self, args: "Sequence[str]") -> "ParseResult":
        return self._parse_argument_list(
            args, self.spec, command_path=(self.spec.name,)
        )

    def _parse_argument_list(  # noqa: PLR0912, PLR0915 - Monolithic function by design
        self,
        args: "Sequence[str]",
        root_spec: "CommandSpec",
        command_path: "Sequence[str]",
    ) -> "ParseResult":
        """Parse a list of command-line arguments.

        This monolithic function contains all parsing logic including dispatch,
        option parsing, subcommand handling, and result building.

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
        # region State initialization
        current_spec = root_spec
        position = 0
        options: dict[str, ParsedOption] = {}
        positionals: tuple[str, ...] = ()
        positionals_started = False
        trailing_mode = False
        trailing_args: list[str] = []
        # endregion

        try:
            # region Main parsing loop
            while position < len(args):
                arg = args[position]

                # region Trailing arguments
                if trailing_mode:
                    trailing_args.append(arg)
                    position += 1
                # endregion

                # region Double-dash separator
                elif arg == "--":
                    trailing_mode = True
                    position += 1
                # endregion

                # region Long options
                elif arg.startswith("--"):
                    # Check if should treat as positional (strict mode or no options)
                    should_treat_as_positional = (
                        self._should_treat_option_as_positional(
                            positionals_started, current_spec
                        )
                    )

                    if should_treat_as_positional:
                        positionals += (arg,)
                        position += 1
                    else:
                        # Parse as long option (inlined from _parse_long_option)
                        arg_without_dashes = arg[2:]
                        next_args = args[position + 1 :]
                        parts = arg_without_dashes.split("=", 1)
                        option_name, option_spec = self._resolve_long_option(
                            parts[0], current_spec
                        )
                        inline_value = parts[1] if len(parts) == 2 else None  # noqa: PLR2004
                        parsed_option: ParsedOption
                        consumed: int = 0

                        match (
                            option_spec.is_flag,
                            option_spec.arity,
                            inline_value,
                            bool(next_args),
                        ):
                            # Flag with value and flag values not allowed
                            case (True, _, str(), _) if (
                                not self.config.allow_equals_for_flags
                            ):
                                raise FlagWithValueError(option_spec.name, option_spec)

                            # Flag with inline value and flag values allowed
                            case (True, _, str(), _) if (
                                self.config.allow_equals_for_flags
                            ):
                                parsed_option, consumed = self._parse_flag_with_value(
                                    option_spec, option_name, inline_value, next_args
                                )

                            # Flag with value from next_args and flag values allowed
                            case (True, _, None, True) if (
                                self.config.allow_equals_for_flags
                            ):
                                parsed_option, consumed = self._parse_flag_with_value(
                                    option_spec, option_name, inline_value, next_args
                                )

                            # Flag without value and const value defined
                            case (True, _, None, _) if (
                                option_spec.const_value is not None
                            ):
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
                                    parsed_option, consumed = (
                                        ParsedOption(
                                            name=option_spec.name,
                                            alias=option_name,
                                            value=True,
                                        ),
                                        0,
                                    )

                            # Flag without value and no const value or negation words
                            case (True, _, None, _):
                                parsed_option, consumed = (
                                    ParsedOption(
                                        name=option_spec.name,
                                        alias=option_name,
                                        value=True,
                                    ),
                                    0,
                                )

                            # Arity requires multiple values but only has inline value
                            case (False, arity, str(), _) if arity and arity.min > 1:
                                raise InsufficientOptionValuesError(
                                    option_spec.name, option_spec
                                )

                            # Arity allows multiple values
                            case (False, arity, str() as val, _) if (
                                arity and self._arity_accepts_values(arity)
                            ):
                                parsed_option, consumed = (
                                    self._parse_option_from_inline_value(
                                        option_spec, option_name, val
                                    ),
                                    0,
                                )

                            # Consume values from next_args
                            case (False, arity, None, _) if (
                                arity and self._arity_accepts_values(arity)
                            ):
                                parsed_option, consumed = (
                                    self._parse_option_values_from_args(
                                        option_spec,
                                        option_name,
                                        next_args,
                                        current_spec,
                                    )
                                )

                            # Zero arity with inline value
                            case (False, arity, str() as val, _) if _is_zero_arity(
                                arity
                            ):
                                # Zero-arity non-flag options with values
                                # Treat as flag value if allow_equals_for_flags enabled
                                if self.config.allow_equals_for_flags and val:
                                    parsed_option, consumed = (
                                        self._parse_flag_with_value(
                                            option_spec, option_name, val, next_args
                                        )
                                    )
                                # Empty value raises OptionDoesNotAcceptValueError
                                elif val == "":
                                    raise OptionDoesNotAcceptValueError(
                                        option_name, option_spec
                                    )
                                # Non-empty value raises FlagWithValueError
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
                                    "Unreachable: all valid combinations of "
                                    "(is_flag, arity, inline_value, next_args) "
                                    "should be handled"
                                )
                                raise AssertionError(msg)

                        accumulated_option = self._accumulate_option(
                            options.get(parsed_option.name), parsed_option, current_spec
                        )
                        options[accumulated_option.name] = accumulated_option
                        position += 1 + consumed
                # endregion

                # region Short options
                elif arg.startswith("-") and arg != "-":
                    # Check if should treat as positional (strict mode)
                    should_treat_as_positional = (
                        self._should_treat_option_as_positional(
                            positionals_started, current_spec
                        )
                    )

                    if should_treat_as_positional:
                        positionals += (arg,)
                        position += 1
                    else:
                        # Try to parse as short option(s) first.
                        # If fails and looks like negative number, treat as positional.
                        arg_without_dash = arg[1:]
                        next_args = args[position + 1 :]

                        # Check if first character can be resolved as an option
                        can_resolve_as_option = False
                        if arg_without_dash:
                            try:
                                _ = current_spec.resolve_option(
                                    arg_without_dash[0],
                                    allow_abbreviations=self.config.allow_abbreviated_options,
                                    case_insensitive=self.config.case_insensitive_flags,
                                )
                                can_resolve_as_option = True
                            except UnknownOptionError:
                                can_resolve_as_option = False

                        # Check if this looks like a negative number
                        is_negative_number = (
                            self.config.allow_negative_numbers
                            and self._is_negative_number(arg)
                        )

                        # Treat as positional if looks like negative number
                        # and can't be resolved as option
                        if is_negative_number and not can_resolve_as_option:
                            positionals += (arg,)
                            position += 1
                            positionals_started = True
                        else:
                            # Parse as short option(s) - inlined

                            # === CHARACTER-BY-CHARACTER PARSING ===
                            # Extract option specs and inline value
                            char_position = 0
                            option_specs: list[tuple[str, OptionSpec]] = []
                            inline_value: str | None = None
                            inline_value_from_equals = False
                            last_option_spec: OptionSpec | None = None

                            while (
                                char_position < len(arg_without_dash)
                                and inline_value is None
                            ):
                                char = arg_without_dash[char_position]

                                # Check for equals sign
                                if char == "=":
                                    char_position += 1
                                    inline_value = arg_without_dash[char_position:]
                                    inline_value_from_equals = True
                                    continue

                                # Try to resolve as an option
                                try:
                                    option_name, option_spec = (
                                        current_spec.resolve_option(
                                            char,
                                            allow_abbreviations=self.config.allow_abbreviated_options,
                                            case_insensitive=self.config.case_insensitive_flags,
                                        )
                                    )
                                except UnknownOptionError:
                                    # Handle unknown option character
                                    # If first character, it's unknown
                                    if char_position == 0:
                                        raise UnknownOptionError(
                                            char,
                                            tuple(current_spec.options.keys()),
                                        ) from None

                                    # Check if previous option needs a value
                                    if (
                                        last_option_spec
                                        and last_option_spec.arity
                                        and last_option_spec.arity.min > 0
                                    ):
                                        inline_value = arg_without_dash[char_position:]
                                        continue

                                    # Check if this looks like an inline value attempt
                                    if (
                                        last_option_spec
                                        and last_option_spec.arity == ZERO_ARITY
                                        and (len(arg_without_dash) - char_position) > 2  # noqa: PLR2004
                                    ):
                                        # ZERO_ARITY option but value provided
                                        raise OptionDoesNotAcceptValueError(
                                            option_specs[-1][0],
                                            last_option_spec,
                                        ) from None

                                    # Unknown option character
                                    raise UnknownOptionError(
                                        char,
                                        tuple(current_spec.options.keys()),
                                    ) from None

                                # Successfully resolved option
                                option_specs.append((option_name, option_spec))
                                last_option_spec = option_spec
                                char_position += 1

                                # Check for zero-arity option followed by =
                                if (
                                    option_spec.arity == ZERO_ARITY
                                    and char_position < len(arg_without_dash)
                                    and arg_without_dash[char_position] == "="
                                ):
                                    # Found zero-arity followed by =
                                    # Check if this is allowed by configuration
                                    if not self.config.allow_equals_for_flags:
                                        raise OptionDoesNotAcceptValueError(
                                            option_name, option_spec
                                        )
                                    # Start inline value
                                    inline_value = arg_without_dash[char_position + 1 :]
                                    inline_value_from_equals = True
                                    continue

                                # Check if this option requires values
                                if (
                                    not option_spec.is_flag
                                    and option_spec.arity.min > 0
                                    and char_position < len(arg_without_dash)
                                ):
                                    # Handle value-required option
                                    next_char = arg_without_dash[char_position]

                                    # Explicit = means inline value
                                    if next_char == "=":
                                        inline_value = arg_without_dash[
                                            char_position + 1 :
                                        ]
                                        inline_value_from_equals = True
                                        continue

                                    # Check if next char is a known option
                                    try:
                                        _ = current_spec.resolve_option(
                                            next_char,
                                            allow_abbreviations=self.config.allow_abbreviated_options,
                                            case_insensitive=self.config.case_insensitive_flags,
                                        )
                                        is_known_option = True
                                    except UnknownOptionError:
                                        is_known_option = False

                                    # If known option + not first + one char
                                    # remaining -> insufficient values error
                                    remaining_chars = (
                                        len(arg_without_dash) - char_position
                                    )
                                    has_previous_options = len(option_specs) > 1
                                    if (
                                        is_known_option
                                        and has_previous_options
                                        and remaining_chars == 1
                                    ):
                                        raise InsufficientOptionValuesError(
                                            option_name, option_spec
                                        )

                                    # Remaining characters are the inline value
                                    inline_value = arg_without_dash[char_position:]

                            # === END CHARACTER PARSING ===

                            # === PARSE EXTRACTED SHORT OPTIONS ===
                            # Inlined from _parse_extracted_short_options
                            parsed_options_list: list[ParsedOption] = []
                            next_args_consumed = 0

                            for spec_index, (option_name, option_spec) in enumerate(
                                option_specs
                            ):
                                is_last = spec_index == len(option_specs) - 1

                                if not is_last:
                                    # Inner option - inlined
                                    # Flag with const_value
                                    if (
                                        option_spec.is_flag
                                        and option_spec.const_value is not None
                                    ):
                                        parsed_option_inner = ParsedOption(
                                            name=option_spec.name,
                                            alias=option_name,
                                            value=option_spec.const_value,
                                        )
                                    # Flag without const_value
                                    elif option_spec.is_flag:
                                        parsed_option_inner = ParsedOption(
                                            name=option_spec.name,
                                            alias=option_name,
                                            value=True,
                                        )
                                    else:
                                        arity = option_spec.arity or ZERO_OR_MORE_ARITY

                                        # Zero arity with const_value
                                        if (
                                            _is_zero_arity(arity)
                                            and option_spec.const_value is not None
                                        ):
                                            parsed_option_inner = ParsedOption(
                                                name=option_spec.name,
                                                alias=option_name,
                                                value=option_spec.const_value,
                                            )
                                        # Zero arity without const_value
                                        elif _is_zero_arity(arity):
                                            parsed_option_inner = ParsedOption(
                                                name=option_spec.name,
                                                alias=option_name,
                                                value=True,
                                            )
                                        # Requires values (error case)
                                        elif arity.min > 0:
                                            raise InsufficientOptionValuesError(
                                                option_spec.name, option_spec
                                            )
                                        else:
                                            # Unreachable
                                            msg = (
                                                f"Unreachable: option "
                                                f"{option_spec.name!r} has unexpected "
                                                f"configuration (arity.min={arity.min})"
                                            )
                                            raise AssertionError(msg)

                                    parsed_options_list.append(parsed_option_inner)
                                else:
                                    # Last option - inlined
                                    # Flag options
                                    if option_spec.is_flag:
                                        # Inlined from _parse_last_short_option_flag
                                        # Flag with inline value when allowed
                                        if (
                                            inline_value is not None
                                            and self.config.allow_equals_for_flags
                                        ):
                                            last_parsed_option, last_consumed = (
                                                self._parse_flag_with_value(
                                                    option_spec,
                                                    option_name,
                                                    inline_value,
                                                    next_args,
                                                )
                                            )
                                        # Flag from next_args when allowed
                                        elif (
                                            inline_value is None
                                            and next_args
                                            and self.config.allow_equals_for_flags
                                        ):
                                            last_parsed_option, last_consumed = (
                                                self._parse_flag_with_value(
                                                    option_spec,
                                                    option_name,
                                                    None,
                                                    next_args,
                                                )
                                            )
                                        # Flag with inline value when not allowed
                                        elif (
                                            inline_value is not None
                                            and not self.config.allow_equals_for_flags
                                        ):
                                            raise FlagWithValueError(
                                                option_spec.name, option_spec
                                            )
                                        # Flag with const_value
                                        elif option_spec.const_value is not None:
                                            last_parsed_option, last_consumed = (
                                                ParsedOption(
                                                    name=option_spec.name,
                                                    alias=option_name,
                                                    value=option_spec.const_value,
                                                ),
                                                0,
                                            )
                                        # Simple flag
                                        else:
                                            last_parsed_option, last_consumed = (
                                                ParsedOption(
                                                    name=option_spec.name,
                                                    alias=option_name,
                                                    value=True,
                                                ),
                                                0,
                                            )
                                    else:
                                        # Zero-arity non-flag options
                                        arity = option_spec.arity or ZERO_OR_MORE_ARITY
                                        if _is_zero_arity(arity):
                                            # Inlined zero-arity handler
                                            # With inline value + flag values allowed
                                            if (
                                                inline_value is not None
                                                and self.config.allow_equals_for_flags
                                            ):
                                                last_parsed_option, last_consumed = (
                                                    self._parse_flag_with_value(
                                                        option_spec,
                                                        option_name,
                                                        inline_value,
                                                        next_args,
                                                    )
                                                )
                                            # Inline value without flag values
                                            elif inline_value is not None:
                                                raise OptionDoesNotAcceptValueError(
                                                    option_spec.name, option_spec
                                                )
                                            # Without inline value and with const_value
                                            elif option_spec.const_value is not None:
                                                last_parsed_option, last_consumed = (
                                                    ParsedOption(
                                                        name=option_spec.name,
                                                        alias=option_name,
                                                        value=option_spec.const_value,
                                                    ),
                                                    0,
                                                )
                                            # No inline value, no const_value
                                            else:
                                                last_parsed_option, last_consumed = (
                                                    ParsedOption(
                                                        name=option_spec.name,
                                                        alias=option_name,
                                                        value=True,
                                                    ),
                                                    0,
                                                )
                                        # Value-consuming options
                                        # Inline value from = syntax
                                        elif (
                                            inline_value is not None
                                            and inline_value_from_equals
                                        ):
                                            if arity.min > 1:
                                                raise InsufficientOptionValuesError(
                                                    option_spec.name, option_spec
                                                )
                                            last_parsed_option = (
                                                self._parse_option_from_inline_value(
                                                    option_spec,
                                                    option_name,
                                                    inline_value,
                                                )
                                            )
                                            last_consumed = 0
                                        # Inline value (not =) + unbounded arity
                                        elif (
                                            inline_value is not None
                                            and not inline_value_from_equals
                                            and arity.max is None
                                        ):
                                            last_parsed_option, last_consumed = (
                                                self._parse_option_values_from_args(
                                                    option_spec,
                                                    option_name,
                                                    next_args,
                                                    current_spec,
                                                    inline_start_value=inline_value,
                                                )
                                            )
                                        # Inline value (not from =) without next_args
                                        elif (
                                            inline_value is not None
                                            and not inline_value_from_equals
                                        ):
                                            if arity.min > 1:
                                                raise InsufficientOptionValuesError(
                                                    option_spec.name, option_spec
                                                )
                                            last_parsed_option = (
                                                self._parse_option_from_inline_value(
                                                    option_spec,
                                                    option_name,
                                                    inline_value,
                                                )
                                            )
                                            last_consumed = 0
                                        # No inline value - consume next_args
                                        else:
                                            last_parsed_option, last_consumed = (
                                                self._parse_option_values_from_args(
                                                    option_spec,
                                                    option_name,
                                                    next_args,
                                                    current_spec,
                                                )
                                            )

                                    parsed_options_list.append(last_parsed_option)
                                    next_args_consumed += last_consumed

                            # === ACCUMULATE SHORT OPTIONS ===
                            # Inlined from _accumulate_short_options
                            accumulated_dict: dict[str, ParsedOption] = {}
                            for parsed_option in parsed_options_list:
                                # Get the old value: check local accumulation first,
                                # then original dict
                                old = accumulated_dict.get(
                                    parsed_option.name
                                ) or options.get(parsed_option.name)
                                accumulated = self._accumulate_option(
                                    old, parsed_option, current_spec
                                )
                                accumulated_dict[accumulated.name] = accumulated
                                options[accumulated.name] = accumulated
                            position += 1 + next_args_consumed
                # endregion

                # region Subcommands and positionals
                else:
                    # Try to resolve as subcommand
                    subcommand_resolution = current_spec.resolve_subcommand(
                        arg,
                        allow_aliases=self.config.allow_aliases,
                        allow_abbreviations=self.config.allow_abbreviated_subcommands,
                        case_insensitive=self.config.case_insensitive_subcommands,
                        minimum_abbreviation_length=self.config.minimum_abbreviation_length,
                    )

                    if subcommand_resolution:
                        # Handle resolved subcommand
                        matched_name, subcommand_spec = subcommand_resolution

                        # Parse subcommand recursively
                        subcommand_result = self._parse_argument_list(
                            args[position + 1 :],
                            subcommand_spec,
                            command_path=(*command_path, subcommand_spec.name),
                        )

                        # Set alias if one was used
                        if matched_name != subcommand_spec.name:
                            subcommand_result = replace(
                                subcommand_result, alias=matched_name
                            )

                        # Build and return result (raises to exit parsing)
                        grouped_positionals = self._group_positionals(
                            positionals, current_spec
                        )

                        result = ParseResult(
                            command=current_spec.name,
                            options=options,
                            positionals=grouped_positionals,
                            extra_args=tuple(trailing_args),
                            subcommand=subcommand_result,
                        )

                        # Raise special exception to exit parsing early
                        raise _SubcommandParsedError(result)  # noqa: TRY301

                    # Check if unknown subcommand error should be raised
                    should_raise_unknown_subcommand = (
                        bool(current_spec.subcommands)
                        and not positionals_started
                        and not current_spec.positionals
                    )

                    if should_raise_unknown_subcommand:
                        all_names = tuple(current_spec.subcommands.keys())
                        raise UnknownSubcommandError(arg, all_names)

                    # Treat as positional
                    positionals += (arg,)
                    position += 1
                    positionals_started = True
                # endregion
            # endregion

            # region Build final result
            flattened_options: dict[str, ParsedOption] = {}
            for option_name, parsed_option in options.items():
                option_spec = current_spec.options[option_name]
                if _should_flatten_option(option_spec, current_spec, self):
                    flattened_options[option_name] = _flatten_option_value(
                        parsed_option
                    )
                else:
                    flattened_options[option_name] = parsed_option

            # Group positional arguments
            grouped_positionals_final = self._group_positionals(
                positionals, current_spec
            )

            return ParseResult(
                command=current_spec.name,
                options=flattened_options,
                positionals=grouped_positionals_final,
                extra_args=tuple(trailing_args),
            )
            # endregion

        except _SubcommandParsedError as e:
            return e.result

    # region Positional argument handling

    def _group_positionals(
        self,
        positionals: "tuple[str, ...]",
        current_spec: "CommandSpec",
    ) -> "dict[str, ParsedPositional]":
        """Group positional arguments according to positional specifications.

        This method distributes positional argument values to their corresponding
        positional parameter specifications based on arity constraints.

        Args:
            positionals: The tuple of positional argument values to group.
            current_spec: The current command specification.

        Returns:
            Dictionary mapping positional parameter names to ParsedPositional objects.

        Raises:
            InsufficientPositionalArgumentsError: If not enough arguments provided.
            UnexpectedPositionalArgumentError: If too many arguments in strict mode.
        """
        grouped_positionals: dict[str, ParsedPositional]
        if not current_spec.positionals:
            # Implicit spec with unbounded arity (0, -1)
            implicit_spec = PositionalSpec(name="args", arity=ZERO_OR_MORE_ARITY)
            grouped_positionals = {
                implicit_spec.name: ParsedPositional(
                    name=implicit_spec.name, value=positionals
                )
            }
        else:
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

            grouped_positionals = {}
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

                # Return scalar for single-value arities (max=1), tuple otherwise
                # This handles both EXACTLY_ONE (1,1) and optional single (0,1)
                if current_positional_spec.arity.max == 1:
                    parsed_value: str | tuple[str, ...] = (
                        consumed_values[0] if consumed_values else ""
                    )
                else:
                    parsed_value = tuple(consumed_values)

                grouped_positionals[current_positional_spec.name] = ParsedPositional(
                    name=current_positional_spec.name,
                    value=parsed_value,
                )

            # Check for unexpected leftover positionals (strict mode)
            if remaining_positionals and self.config.strict_options_before_positionals:
                raise UnexpectedPositionalArgumentError(
                    remaining_positionals[0], current_spec.name
                )

        return grouped_positionals

    # endregion

    # region Option resolution

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
            allow_abbreviations=self.config.allow_abbreviated_options,
            case_insensitive=self.config.case_insensitive_options,
            convert_underscores=self.config.convert_underscores_to_dashes,
            minimum_abbreviation_length=self.config.minimum_abbreviation_length,
        )

    # endregion

    # region Option value parsing

    def _parse_flag_with_value(
        self,
        option_spec: "OptionSpec",
        option_name: str,
        inline_value: str | None,
        next_args: "Sequence[str]",
    ) -> tuple[ParsedOption, int]:
        truthy = frozenset(
            option_spec.truthy_flag_values
            or self.config.truthy_flag_values
            or DEFAULT_TRUTHY_VALUES
        )
        falsey = frozenset(
            option_spec.falsey_flag_values
            or self.config.falsey_flag_values
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
                # Unreachable: value is either None or str
                msg = (
                    f"Unreachable: flag value must be None or str, "
                    f"got {type(value).__name__}"
                )
                raise AssertionError(msg)

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
                if self.config.allow_negative_numbers and self._is_negative_number(
                    current_value
                ):
                    # Continue to consume as value
                    pass
                else:
                    # Stop consuming (potential option)
                    break

            # Check if this is a subcommand (stop consuming values)
            if current_spec.resolve_subcommand(
                current_value,
                allow_aliases=self.config.allow_aliases,
                allow_abbreviations=self.config.allow_abbreviated_subcommands,
                case_insensitive=self.config.case_insensitive_subcommands,
                minimum_abbreviation_length=self.config.minimum_abbreviation_length,
            ):
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
                        self.config.allow_negative_numbers
                        and self._is_negative_number(arg)
                    )
                ):
                    break
                # Check if this is a subcommand (stop counting)
                if current_spec.resolve_subcommand(
                    arg,
                    allow_aliases=self.config.allow_aliases,
                    allow_abbreviations=self.config.allow_abbreviated_subcommands,
                    case_insensitive=self.config.case_insensitive_subcommands,
                    minimum_abbreviation_length=self.config.minimum_abbreviation_length,
                ):
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

    # endregion

    # region Option accumulation

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
                raise DuplicateOptionError(option_spec.name, option_spec)

            case _:
                # Unreachable: all AccumulationMode values should be handled
                msg = (
                    f"Unreachable: unexpected accumulation mode "
                    f"{option_spec.accumulation_mode!r}"
                )
                raise AssertionError(msg)
        return accumulated_option

    # endregion

    # region Utility methods

    @staticmethod
    def _arity_accepts_values(arity: "Arity") -> bool:
        return (
            arity.min > 0
            or (arity.min == 0 and arity.max is None)
            or (arity.min == 0 and arity.max is not None and arity.max > 0)
        )

    def _should_treat_option_as_positional(
        self,
        positionals_started: bool,  # noqa: FBT001 - Local helper uses bool for clarity
        current_spec: "CommandSpec",
    ) -> bool:
        """Check if an option-like argument should be treated as a positional.

        This occurs in two cases:
        1. Strict mode: positionals have started and
           strict_options_before_positionals is enabled
        2. No options defined: positionals have started and spec has no options

        Args:
            positionals_started: Whether any positional arguments have been parsed.
            current_spec: The current command specification.

        Returns:
            True if the option should be treated as a positional argument.
        """
        return (
            positionals_started and self.config.strict_options_before_positionals
        ) or (positionals_started and not current_spec.options)

    def _is_negative_number(self, arg: str) -> bool:
        """Check if argument matches negative number pattern.

        Args:
            arg: The argument to check.

        Returns:
            True if argument matches the negative number pattern.
        """
        pattern = self.config.negative_number_pattern or DEFAULT_NEGATIVE_NUMBER_PATTERN
        return bool(re.match(pattern, arg))

    # endregion


# region Module-level helper functions


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


def _resolve_flatten_setting(
    option_spec: "OptionSpec",
    command_spec: "CommandSpec",
    parser: BaseParser,
) -> bool:
    """Resolve the effective flatten_values setting for an option.

    Applies precedence: OptionSpec > CommandSpec > BaseParser.

    Args:
        option_spec: The option specification.
        command_spec: The command specification containing the option.
        parser: The parser instance with global settings.

    Returns:
        The effective flatten_values setting (True or False).
    """
    # Option-level setting takes precedence
    if option_spec.flatten_values is not None:
        return option_spec.flatten_values

    # Command-level setting is next
    if command_spec.flatten_option_values is not None:
        return command_spec.flatten_option_values

    # Fall back to parser-level default
    return parser.config.flatten_option_values


def _should_flatten_option(
    option_spec: "OptionSpec",
    command_spec: "CommandSpec",
    parser: BaseParser,
) -> bool:
    """Determine if an option's values should be flattened.

    Flattening applies only when ALL conditions are met:
    1. Option has COLLECT accumulation mode
    2. Option allows multiple values per occurrence (arity.max > 1 or None)
    3. Effective flatten_values setting is True

    Args:
        option_spec: The option specification.
        command_spec: The command specification containing the option.
        parser: The parser instance with global settings.

    Returns:
        True if the option's values should be flattened, False otherwise.
    """
    # Only COLLECT mode produces nested structures
    if option_spec.accumulation_mode != AccumulationMode.COLLECT:
        return False

    # Only multi-value options can produce nested tuples
    arity = option_spec.arity or ZERO_OR_MORE_ARITY
    if not _is_multi_value_arity(arity):
        return False

    # Check if flattening is enabled
    return _resolve_flatten_setting(option_spec, command_spec, parser)


def _flatten_option_value(
    parsed_option: ParsedOption,
) -> ParsedOption:
    """Flatten a ParsedOption's nested tuple value into a single flat tuple.

    Uses itertools.chain.from_iterable for O(n) performance.

    Args:
        parsed_option: The option with potentially nested tuple values.

    Returns:
        A new ParsedOption with flattened values, or the original if value
        is not a nested tuple structure.
    """
    # Only process tuple of tuples (nested structure from COLLECT mode)
    if not isinstance(parsed_option.value, tuple):
        return parsed_option

    # Check if this is a nested tuple structure
    # In COLLECT mode with multi-value options, we get tuple[tuple[str, ...], ...]
    if not parsed_option.value or not isinstance(parsed_option.value[0], tuple):
        return parsed_option

    # At this point, we know value is tuple[tuple[...], ...]
    # Cast to help type checker understand the structure after runtime checks
    nested_value = cast("tuple[tuple[str, ...], ...]", parsed_option.value)

    # Flatten using chain.from_iterable for O(n) performance
    flattened = tuple(chain.from_iterable(nested_value))

    return ParsedOption(
        name=parsed_option.name,
        value=flattened,
        alias=parsed_option.alias,
    )


# endregion
