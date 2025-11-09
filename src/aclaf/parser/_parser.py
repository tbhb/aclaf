from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING, final, override

from ._base import BaseParser, ParsedOption, ParsedPositional, ParseResult
from ._parameters import PositionalSpec
from .constants import DEFAULT_FALSEY_VALUES, DEFAULT_TRUTHY_VALUES
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

    def _parse_argument_list(  # noqa: PLR0912 - Complex argument parsing logic
        self,
        args: "Sequence[str]",
        root_spec: "CommandSpec",
        command_path: "Sequence[str]",
    ) -> "ParseResult":
        current_spec = root_spec
        position = 0
        options: dict[str, ParsedOption] = {}
        positionals: tuple[str, ...] = ()
        positionals_started = False
        trailing_mode = False
        trailing_args: list[str] = []

        while position < len(args):
            arg = args[position]

            match (arg, trailing_mode, positionals_started):
                case (_, True, _):
                    trailing_args.append(arg)
                    position += 1
                case ("--", False, _):
                    trailing_mode = True
                    position += 1
                case (str() as opt, False, _) if opt.startswith("--"):
                    # Treat as positional if:
                    # - strict mode is enabled and positionals have started, OR
                    # - positionals have started and no options are defined
                    if (
                        positionals_started and self._strict_options_before_positionals
                    ) or (positionals_started and not current_spec.options):
                        positionals += (arg,)
                        position += 1
                    else:
                        parsed_option, consumed = self._parse_long_option(
                            opt[2:],
                            args[position + 1 :],
                            current_spec,
                            MappingProxyType(options),
                        )
                        options[parsed_option.name] = parsed_option
                        position += 1 + consumed
                case (str() as opt, False, _) if opt.startswith("-") and opt != "-":
                    # Short option(s)
                    # Treat as positional if:
                    # - strict mode is enabled and positionals have started, OR
                    # - positionals have started and no options are defined
                    if (
                        positionals_started and self._strict_options_before_positionals
                    ) or (positionals_started and not current_spec.options):
                        positionals += (arg,)
                        position += 1
                    else:
                        parsed_options, consumed = self._parse_short_options(
                            opt[1:],
                            args[position + 1 :],
                            current_spec,
                            MappingProxyType(options),
                        )
                        for parsed_option in parsed_options:
                            options[parsed_option.name] = parsed_option
                        position += 1 + consumed
                case _:
                    if subcommand_resolution := current_spec.resolve_subcommand(
                        arg,
                        allow_aliases=self.allow_aliases,
                        allow_abbreviations=self.allow_abbreviated_subcommands,
                        case_insensitive=self.case_insensitive_subcommands,
                        minimum_abbreviation_length=self.minimum_abbreviation_length,
                    ):
                        matched_name, subcommand_spec = subcommand_resolution
                        subcommand_result = self._parse_argument_list(
                            args[position + 1 :],
                            subcommand_spec,
                            command_path=(*command_path, subcommand_spec.name),
                        )
                        # Determine if an alias was used
                        alias_used = (
                            matched_name
                            if matched_name != subcommand_spec.name
                            else None
                        )
                        # Set the alias on the subcommand result if one was used
                        if alias_used:
                            subcommand_result = replace(
                                subcommand_result, alias=alias_used
                            )
                        return ParseResult(
                            command=current_spec.name,
                            options=options,
                            positionals=self._group_positionals(
                                positionals, current_spec
                            ),
                            extra_args=tuple(trailing_args),
                            subcommand=subcommand_result,
                        )
                    # Check if this could be an unknown subcommand
                    # Only raise error if:
                    # 1. We have subcommands defined
                    # 2. No positionals are defined (or all are optional)
                    # 3. No positionals have been started yet
                    if (
                        current_spec.subcommands
                        and not positionals_started
                        and not current_spec.positionals
                    ):
                        # We have subcommands and no positionals defined,
                        # so this must be an unknown subcommand
                        all_subcommand_names = tuple(current_spec.subcommands.keys())
                        raise UnknownSubcommandError(arg, all_subcommand_names)
                    positionals += (arg,)
                    position += 1
                    positionals_started = True

        return ParseResult(
            command=current_spec.name,
            options=options,
            positionals=self._group_positionals(positionals, current_spec),
            extra_args=tuple(trailing_args),
        )

    def _parse_long_option(  # noqa: PLR0912 - Complex long option parsing logic
        self,
        arg_without_dashes: str,
        next_args: "Sequence[str]",
        current_spec: "CommandSpec",
        options: MappingProxyType[str, ParsedOption],
    ) -> tuple[ParsedOption, int]:
        parts = arg_without_dashes.split("=", 1)
        option_name, option_spec = current_spec.resolve_option(
            parts[0],
            allow_abbreviations=self.allow_abbreviated_options,
            case_insensitive=self.case_insensitive_options,
            convert_underscores=self.convert_underscores_to_dashes,
            minimum_abbreviation_length=self.minimum_abbreviation_length,
        )
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
            case (False, arity, str() as val, _) if (
                arity and arity.min == 0 and arity.max == 0
            ):
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
            case (False, arity, None, _) if arity and arity.min == 0 and arity.max == 0:
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
                raise NotImplementedError()

        accumulated_option = self._accumulate_option(
            options.get(parsed_option.name), parsed_option, current_spec
        )
        return accumulated_option, consumed

    def _parse_short_options(  # noqa: PLR0912, PLR0915 - Complex short option parsing
        self,
        arg_without_dash: str,
        next_args: "Sequence[str]",
        current_spec: "CommandSpec",
        options: MappingProxyType[str, ParsedOption],
    ) -> tuple[tuple[ParsedOption, ...], int]:
        option_specs, inline_value, inline_value_from_equals = (
            self._extract_short_option_specs(arg_without_dash, current_spec)
        )

        parsed_options: list[ParsedOption] = []
        next_args_consumed = 0

        for index, (option_name, option_spec) in enumerate(option_specs):
            is_last = index == len(option_specs) - 1

            match (
                is_last,
                option_spec.is_flag,
                option_spec.arity,
                inline_value,
                bool(next_args),
            ):
                # Inner option: flag with const_value
                case (False, True, _, _, _) if option_spec.const_value is not None:
                    parsed_options.append(
                        ParsedOption(
                            name=option_spec.name,
                            alias=option_name,
                            value=option_spec.const_value,
                        )
                    )

                # Inner option: flag without const_value
                case (False, True, _, _, _):
                    parsed_options.append(
                        ParsedOption(
                            name=option_spec.name, alias=option_name, value=True
                        )
                    )

                # Inner option: zero arity (non-flag) with const_value
                case (False, False, arity, _, _) if (
                    arity
                    and arity.min == 0
                    and arity.max == 0
                    and option_spec.const_value is not None
                ):
                    parsed_options.append(
                        ParsedOption(
                            name=option_spec.name,
                            alias=option_name,
                            value=option_spec.const_value,
                        )
                    )

                # Inner option: zero arity (non-flag) without const_value
                case (False, False, arity, _, _) if (
                    arity and arity.min == 0 and arity.max == 0
                ):
                    parsed_options.append(
                        ParsedOption(
                            name=option_spec.name, alias=option_name, value=True
                        )
                    )

                # Inner option: requires values
                case (False, False, arity, _, _) if arity and arity.min > 0:
                    raise InsufficientOptionValuesError(option_spec.name, option_spec)

                # Last option: flag from inline value when flag values are allowed
                case (True, True, _, str(), _) if self.allow_equals_for_flags:
                    parsed_option, extra_consumed = self._parse_flag_with_value(
                        option_spec, option_name, inline_value, next_args
                    )
                    parsed_options.append(parsed_option)
                    next_args_consumed += extra_consumed

                # Last option: flag from next_args when flag values are allowed
                case (True, True, _, None, True) if self.allow_equals_for_flags:
                    parsed_option, extra_consumed = self._parse_flag_with_value(
                        option_spec, option_name, inline_value, next_args
                    )
                    parsed_options.append(parsed_option)
                    next_args_consumed += extra_consumed

                # Last option: flag from inline value when flag values not allowed
                case (True, True, _, str(), _) if not self.allow_equals_for_flags:
                    raise FlagWithValueError(option_spec.name, option_spec)

                # Last option: flag without value and const value defined
                case (True, True, _, None, _) if option_spec.const_value is not None:
                    parsed_options.append(
                        ParsedOption(
                            name=option_spec.name,
                            alias=option_name,
                            value=option_spec.const_value,
                        )
                    )

                # Last option: flag without value and no const value
                case (True, True, _, None, _):
                    parsed_options.append(
                        ParsedOption(
                            name=option_spec.name,
                            alias=option_name,
                            value=True,
                        )
                    )

                # Last option: has inline value from = syntax
                # (only use inline, don't consume next_args)
                case (True, False, arity, str() as val, _) if (
                    inline_value_from_equals
                    and arity
                    and self._arity_accepts_values(arity)
                ):
                    # When using =value syntax, only the inline value is consumed
                    if arity.min > 1:
                        # Need more values than inline value provides
                        raise InsufficientOptionValuesError(
                            option_spec.name, option_spec
                        )
                    parsed_option = self._parse_option_from_inline_value(
                        option_spec, option_name, val
                    )
                    parsed_options.append(parsed_option)

                # Last option: has inline value (not from =)
                # and needs more values from next_args
                case (True, False, arity, str() as val, True) if (
                    not inline_value_from_equals and arity and arity.max is None
                ):
                    # Inline value without = means continue consuming from next_args
                    parsed_option, extra_consumed = self._parse_option_values_from_args(
                        option_spec,
                        option_name,
                        next_args,
                        current_spec,
                        inline_start_value=val,
                    )
                    parsed_options.append(parsed_option)
                    next_args_consumed += extra_consumed

                # Last option: has inline value (not from =) but no next_args
                case (True, False, arity, str() as val, False) if (
                    not inline_value_from_equals
                    and arity
                    and self._arity_accepts_values(arity)
                ):
                    if arity.min > 1:
                        raise InsufficientOptionValuesError(
                            option_spec.name, option_spec
                        )
                    parsed_option = self._parse_option_from_inline_value(
                        option_spec, option_name, val
                    )
                    parsed_options.append(parsed_option)

                # Last option: needs to consume values from next_args
                case (True, False, arity, _, _) if arity and self._arity_accepts_values(
                    arity
                ):
                    parsed_option, extra_consumed = self._parse_option_values_from_args(
                        option_spec, option_name, next_args, current_spec
                    )
                    parsed_options.append(parsed_option)
                    next_args_consumed += extra_consumed

                # Last option: zero arity with inline value when flag values allowed
                case (True, False, arity, str(), _) if (
                    arity
                    and arity.min == 0
                    and arity.max == 0
                    and self.allow_equals_for_flags
                ):
                    # Treat as flag value
                    parsed_option, extra_consumed = self._parse_flag_with_value(
                        option_spec, option_name, inline_value, next_args
                    )
                    parsed_options.append(parsed_option)
                    next_args_consumed += extra_consumed

                # Last option: zero arity with inline value when flag values not allowed
                case (True, False, arity, str(), _) if (
                    arity and arity.min == 0 and arity.max == 0
                ):
                    raise OptionDoesNotAcceptValueError(option_spec.name, option_spec)

                # Last option: zero arity without value and const value defined
                case (True, False, arity, None, _) if (
                    arity
                    and arity.min == 0
                    and arity.max == 0
                    and option_spec.const_value is not None
                ):
                    parsed_options.append(
                        ParsedOption(
                            name=option_spec.name,
                            alias=option_name,
                            value=option_spec.const_value,
                        )
                    )

                # Last option: zero arity without value and no const value
                case (True, False, arity, None, _) if (
                    arity and arity.min == 0 and arity.max == 0
                ):
                    parsed_options.append(
                        ParsedOption(
                            name=option_spec.name, alias=option_name, value=True
                        )
                    )

                case _:
                    raise NotImplementedError()

        # Accumulate options, threading the accumulated value through
        # This is important for combined flags like -vvv with COUNT mode
        accumulated_dict: dict[str, ParsedOption] = {}
        accumulated_options: list[ParsedOption] = []

        for parsed_option in parsed_options:
            # Get the old value: first check our local accumulation dict,
            # then fall back to the original options dict
            old = accumulated_dict.get(parsed_option.name) or options.get(
                parsed_option.name
            )
            accumulated = self._accumulate_option(old, parsed_option, current_spec)
            accumulated_dict[accumulated.name] = accumulated
            accumulated_options.append(accumulated)

        return tuple(accumulated_options), next_args_consumed

    def _extract_short_option_specs(  # noqa: PLR0912, PLR0915 - Complex short option extraction
        self, arg_without_dash: str, current_spec: "CommandSpec"
    ) -> tuple[list[tuple[str, "OptionSpec"]], str | None, bool]:
        option_specs: list[tuple[str, OptionSpec]] = []
        position = 0
        inline_value_started = False
        inline_value_from_equals = False
        last_option_spec: OptionSpec | None = None

        while position < len(arg_without_dash) and not inline_value_started:
            char = arg_without_dash[position]

            if char == "=":
                position += 1
                inline_value_started = True
                inline_value_from_equals = True
                break

            try:
                _, option_spec = current_spec.resolve_option(
                    char,
                    allow_abbreviations=self.allow_abbreviated_options,
                    case_insensitive=self.case_insensitive_flags,
                )
            except UnknownOptionError:
                if position == 0:
                    raise
                # Only treat as inline value if previous option needs a value
                if (
                    last_option_spec
                    and last_option_spec.arity
                    and last_option_spec.arity.min > 0
                ):
                    inline_value_started = True
                else:
                    # If previous option was ZERO_ARITY and there are MORE than
                    # one character remaining, this looks like an inline value attempt
                    # (e.g., -vfoo where foo is a value)
                    # Raise OptionDoesNotAcceptValueError for better clarity
                    # But if there's only 1-2 chars remaining, it looks like flags
                    # (e.g., -vxf), so raise UnknownOptionError
                    remaining = len(arg_without_dash) - position
                    _min_chars_for_value = 2  # Minimum chars to treat as value not flag
                    if (
                        last_option_spec
                        and last_option_spec.arity == ZERO_ARITY
                        and remaining > _min_chars_for_value
                    ):
                        raise OptionDoesNotAcceptValueError(
                            option_specs[-1][0], last_option_spec
                        ) from None
                    # Unknown option - raise UnknownOptionError
                    raise
            else:
                option_specs.append((char, option_spec))
                last_option_spec = option_spec
                position += 1

                # Check for ZERO_ARITY with = (error case when flag values not allowed)
                # ZERO_ARITY options can be followed by more short options,
                # but not by =value unless allow_equals_for_flags is enabled
                if (
                    option_spec.arity == ZERO_ARITY
                    and position < len(arg_without_dash)
                    and arg_without_dash[position] == "="
                    and not self.allow_equals_for_flags
                ):
                    # ZERO_ARITY option cannot have inline values via =
                    # (unless flag values allowed)
                    raise OptionDoesNotAcceptValueError(char, option_spec)

                # If ZERO_ARITY with = and flag values allowed,
                # treat rest as inline value
                if (
                    option_spec.arity == ZERO_ARITY
                    and position < len(arg_without_dash)
                    and arg_without_dash[position] == "="
                    and self.allow_equals_for_flags
                ):
                    inline_value_started = True
                    inline_value_from_equals = True

                # If this option requires values and there are more chars,
                # treat the rest as inline value (but not for flags)
                if (
                    not option_spec.is_flag
                    and option_spec.arity
                    and option_spec.arity.min > 0
                    and position < len(arg_without_dash)
                ):
                    # Check next character
                    next_char = arg_without_dash[position]

                    # If next char is '=', it's an explicit value separator - always OK
                    if next_char == "=":
                        inline_value_started = True
                        inline_value_from_equals = True
                    # Otherwise, check if next char is a known option
                    else:
                        is_known_option = False
                        try:
                            _ = current_spec.resolve_option(
                                next_char,
                                allow_abbreviations=self.allow_abbreviated_options,
                                case_insensitive=self.case_insensitive_flags,
                            )
                            is_known_option = True
                        except UnknownOptionError:
                            pass

                        # If next char is a known option AND this value option is not
                        # at position 0 AND there's only one char remaining
                        # (looks like a flag, not a value), error
                        # Note: option_specs already includes the current option,
                        # so > 1 means there were others before
                        remaining_chars = len(arg_without_dash) - position
                        if (
                            is_known_option
                            and len(option_specs) > 1
                            and remaining_chars == 1
                        ):
                            raise InsufficientOptionValuesError(char, option_spec)

                        # The remaining characters are treated as the inline value
                        inline_value_started = True

        inline_value: str | None = None
        if inline_value_started:
            # Skip leading = if present
            if arg_without_dash[position : position + 1] == "=":
                position += 1
            inline_value = arg_without_dash[position:]

        return option_specs, inline_value, inline_value_from_equals

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
                raise NotImplementedError()

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

    def _parse_option_values_from_args(
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
                break

            if current_spec.resolve_subcommand(
                current_value,
                allow_aliases=self.allow_aliases,
                allow_abbreviations=self.allow_abbreviated_subcommands,
                case_insensitive=self.case_insensitive_subcommands,
                minimum_abbreviation_length=self.minimum_abbreviation_length,
            ):
                break

            # Check if consuming this value would violate positional requirements
            # Count remaining non-option, non-subcommand args after this consumption
            remaining_after_consume = 0
            for arg in next_args[consumed + 1 :]:
                if arg.startswith("-") and arg != "-":
                    break
                if current_spec.resolve_subcommand(
                    arg,
                    allow_aliases=self.allow_aliases,
                    allow_abbreviations=self.allow_abbreviated_subcommands,
                    case_insensitive=self.case_insensitive_subcommands,
                    minimum_abbreviation_length=self.minimum_abbreviation_length,
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
            parsed_value = values[0]
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
                if not isinstance(new.value, tuple):
                    # Scalar value (flag, const_value, etc.): wrap in tuple
                    # Type checker can't handle dynamic tuple construction
                    # for COLLECT mode
                    accumulated_option = ParsedOption(
                        name=new.name,
                        alias=new.alias,
                        value=(new.value,),  # pyright: ignore[reportArgumentType]
                    )
                elif arity.max is None or arity.max > 1:
                    # Multi-value option (unbounded or max > 1):
                    # wrap tuple in outer tuple
                    # to preserve grouping across multiple occurrences
                    # Type checker can't handle dynamic tuple construction
                    # for COLLECT mode
                    accumulated_option = ParsedOption(
                        name=new.name,
                        alias=new.alias,
                        value=(new.value,),  # pyright: ignore[reportArgumentType]
                    )
                else:
                    # Single-value option (max=1) with COLLECT:
                    # the value is already a tuple
                    accumulated_option = new
            case (AccumulationMode.COLLECT, ParsedOption()):
                # Subsequent occurrences: append to the collection
                # Check if this is a multi-value option to preserve grouping
                # Type checker can't handle dynamic tuple construction for COLLECT mode
                arity = option_spec.arity or ZERO_OR_MORE_ARITY
                if not isinstance(new.value, tuple):
                    # Scalar value: append directly
                    value = (*old.value, new.value)  # pyright: ignore[reportGeneralTypeIssues,reportUnknownVariableType]
                elif arity.max is None or arity.max > 1:
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
                raise NotImplementedError()
        return accumulated_option

    @staticmethod
    def _arity_accepts_values(arity: "Arity") -> bool:
        return (
            arity.min > 0
            or (arity.min == 0 and arity.max is None)
            or (arity.min == 0 and arity.max is not None and arity.max > 0)
        )
