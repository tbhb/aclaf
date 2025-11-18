import re
import warnings
from dataclasses import dataclass, field
from typing import TypedDict

from ._types import AccumulationMode, Arity

LONG_NAME_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z-_]*[a-zA-Z0-9]$")
SHORT_NAME_REGEX = re.compile(r"^[a-zA-Z0-9]$")

_DEFAULT_ARITY = Arity(1, 1)


def _validate_arity(value: Arity) -> None:
    if value.min < 0:
        msg = "Minimum arity must not be negative."
        raise ValueError(msg)
    if value.max is not None and value.max < 0:
        msg = "Maximum arity must not be negative."
        raise ValueError(msg)
    if value.max is not None and value.min > value.max:
        msg = "Minimum arity must be less than maximum arity."
        raise ValueError(msg)


class OptionSpecInput(TypedDict, total=False):
    name: str
    long: frozenset[str]
    short: frozenset[str]
    arity: Arity
    accumulation_mode: AccumulationMode
    is_flag: bool
    falsey_flag_values: frozenset[str] | None
    truthy_flag_values: frozenset[str] | None
    negation_words: frozenset[str] | None
    const_value: str | None
    flatten_values: bool | None


@dataclass(slots=True, frozen=True, unsafe_hash=True)
class OptionSpec:
    """Specification for a command-line option.

    An option is a named parameter that typically appears with `--` (long form)
    or `-` (short form) prefixes. Options can accept zero or more values and
    can be configured with various behaviors for accumulation, negation, and
    flag value coercion.

    The `OptionSpec` is immutable after construction and defines all the metadata
    needed for the parser to recognize and process an option.

    Attributes:
        name: The canonical option name (without dashes). Must be alphanumeric
            with optional dashes/underscores (not at start/end).
        long: Frozenset of long-form option names. If empty and name has >1
            character, uses name as the long form. Default: empty frozenset.
        short: Frozenset of short-form option names. If empty and name has 1
            character, uses name as the short form. Must be single alphanumeric
            characters. Default: empty frozenset.
        arity: Number of values the option accepts as an Arity object.
            Default: `Arity(1, 1)`. Flags typically use `Arity(0, 0)`.
        accumulation_mode: How to handle repeated option occurrences.
            Default is [`LAST_WINS`][aclaf.parser.AccumulationMode.LAST_WINS].
        is_flag: Whether this is a boolean flag option. Flags have special
            behavior for value coercion and default arity of `0`.
        falsey_flag_values: Frozenset of values that set the flag to `False`
            when using `--flag=value` syntax (requires `allow_equals_for_flags`).
        truthy_flag_values: Frozenset of values that set the flag to `True`
            when using `--flag=value` syntax (requires `allow_equals_for_flags`).
        negation_words: Frozenset of prefix words for negation (e.g., `no`
            allows `--no-verbose`). Only applies to flags. Default: empty frozenset.
        const_value: Constant value to use when the option is specified
            without an explicit value.
        flatten_values: When `True` and `accumulation_mode` is
            [`COLLECT`][aclaf.parser.AccumulationMode.COLLECT], flatten
            nested tuples from multiple occurrences into a single flat tuple.
            Only applies when arity allows multiple values per occurrence
            (`arity.max > 1` or `arity.max is None`). If `None`, inherits from
            [`CommandSpec.flatten_option_values`][aclaf.parser.CommandSpec.flatten_option_values]
            or
            [`BaseParser.flatten_option_values`][aclaf.parser.BaseParser.flatten_option_values].
            Default: `None`.
    """

    name: str
    long: frozenset[str] = field(default_factory=frozenset)
    short: frozenset[str] = field(default_factory=frozenset)
    arity: Arity = _DEFAULT_ARITY
    accumulation_mode: AccumulationMode = AccumulationMode.LAST_WINS
    is_flag: bool = False
    falsey_flag_values: frozenset[str] | None = None
    truthy_flag_values: frozenset[str] | None = None
    negation_words: frozenset[str] | None = None
    const_value: str | None = None
    flatten_values: bool | None = None

    def __post_init__(self) -> None:
        self._validate_name(self.name)

        if not self.long and len(self.name) > 1:
            object.__setattr__(self, "long", frozenset((self.name,)))
        if not self.short and len(self.name) == 1:
            object.__setattr__(self, "short", frozenset((self.name,)))

        self._validate_long_names(self.long)
        self._validate_short_names(self.short)
        _validate_arity(self.arity)
        self._validate_falsey_flag_values(self.falsey_flag_values)
        self._validate_truthy_flag_values(self.truthy_flag_values)
        self._validate_flag_values_no_overlap(
            self.truthy_flag_values, self.falsey_flag_values
        )
        self._validate_negation_words(self.negation_words)
        self._validate_flatten_values(
            self.flatten_values,
            self.accumulation_mode,
            self.name,
        )

    @staticmethod
    def _validate_name(
        value: str,
    ) -> None:
        if len(value) < 1:
            msg = "Option name must not be empty."
            raise ValueError(msg)
        if not re.match(LONG_NAME_REGEX, value) and not re.match(
            SHORT_NAME_REGEX, value
        ):
            msg = (
                f"Option name {value} must be at least one alphanumeric character"
                " with no whitespace and may contain dashes and underscores except"
                " for the first and last characters."
            )
            raise ValueError(msg)

    @staticmethod
    def _validate_long_names(value: frozenset[str]) -> None:
        for name in value:
            if len(name) < 2:  # noqa: PLR2004
                msg = f"Long option name '{name}' must have at least two characters."
                raise ValueError(msg)
            if not re.match(LONG_NAME_REGEX, name):
                msg = (
                    f"Option long name {name} must be at least two alphanumeric"
                    " characters with no whitespace and may contain dashes and"
                    " underscores except for the first and last characters."
                )
                raise ValueError(msg)

    @staticmethod
    def _validate_short_names(value: frozenset[str]) -> None:
        for name in value:
            if len(name) != 1:
                msg = f"Short option name '{name}' must be exactly one character."
                raise ValueError(msg)
            if not re.match(SHORT_NAME_REGEX, name):
                msg = (
                    f"Short option name '{name}' must be exactly one alphanumeric"
                    " character."
                )
                raise ValueError(msg)

    @staticmethod
    def _validate_negation_words(
        values: frozenset[str] | None,
    ) -> None:
        if values is None:
            return

        for name in values:
            if len(name) < 1:
                msg = "Negation word must have at least one character."
                raise ValueError(msg)
            if re.search(r"\s", name):
                msg = f"Negation word '{name}' must not contain whitespace."
                raise ValueError(msg)

    @staticmethod
    def _validate_flatten_values(
        flatten_values: bool | None,  # noqa: FBT001
        accumulation_mode: AccumulationMode,
        name: str,
    ) -> None:
        if flatten_values is True and accumulation_mode != AccumulationMode.COLLECT:
            msg = (
                f"Option '{name}': flatten_values=True has no effect with "
                f"accumulation_mode={accumulation_mode}. Flattening only applies "
                f"to COLLECT mode."
            )
            warnings.warn(msg, stacklevel=2)

    @staticmethod
    def _validate_truthy_flag_values(
        values: frozenset[str] | None,
    ) -> None:
        if values is None:
            return

        if len(values) == 0:
            msg = (
                "truthy_flag_values must not be empty. "
                "Provide at least one truthy value or use None for defaults."
            )
            raise ValueError(msg)

        for idx, value in enumerate(values):
            if len(value) == 0:
                msg = (
                    f"truthy_flag_values must contain only non-empty strings. "
                    f"Found empty string at index {idx}."
                )
                raise ValueError(msg)

    @staticmethod
    def _validate_falsey_flag_values(
        values: frozenset[str] | None,
    ) -> None:
        if values is None:
            return

        if len(values) == 0:
            msg = (
                "falsey_flag_values must not be empty. "
                "Provide at least one falsey value or use None for defaults."
            )
            raise ValueError(msg)

        for idx, value in enumerate(values):
            if len(value) == 0:
                msg = (
                    f"falsey_flag_values must contain only non-empty strings. "
                    f"Found empty string at index {idx}."
                )
                raise ValueError(msg)

    @staticmethod
    def _validate_flag_values_no_overlap(
        truthy: frozenset[str] | None,
        falsey: frozenset[str] | None,
    ) -> None:
        if truthy is None or falsey is None:
            return

        truthy_set = set(truthy)
        falsey_set = set(falsey)
        overlap = truthy_set & falsey_set

        if overlap:
            overlap_list = ", ".join(f"'{v}'" for v in sorted(overlap))
            msg = (
                f"truthy_flag_values and falsey_flag_values must not overlap. "
                f"Found overlapping values: {overlap_list}."
            )
            raise ValueError(msg)


class PositionalSpecInput(TypedDict, total=False):
    name: str
    arity: Arity


@dataclass(slots=True, frozen=True, unsafe_hash=True)
class PositionalSpec:
    """Specification for a positional argument.

    A positional argument is a command-line argument identified by its
    position rather than by a name/flag. Positionals are matched to their
    specifications in order after all options have been consumed.

    The `PositionalSpec` is immutable after construction and defines the
    name and arity for a positional parameter.

    Attributes:
        name: The parameter name for this positional. Used to identify
            the positional in the parse result.
        arity: Number of values this positional accepts as an Arity object.
            Default: `Arity(1, 1)`.
    """

    name: str
    arity: Arity = _DEFAULT_ARITY

    def __post_init__(self) -> None:
        _validate_arity(self.arity)
