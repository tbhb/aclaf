import re
import warnings
from typing import TYPE_CHECKING, override

from ._utils import normalize_frozen_str_set
from .types import AccumulationMode, Arity

if TYPE_CHECKING:
    from collections.abc import Sequence

LONG_NAME_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z-_]*[a-zA-Z0-9]$")
SHORT_NAME_REGEX = re.compile(r"^[a-zA-Z0-9]$")


def _validate_arity(value: int | Arity | tuple[int, int] | None) -> Arity:
    if value is None:
        return Arity(1, 1)
    if isinstance(value, Arity):
        normalized = value
    elif isinstance(value, tuple):
        normalized = Arity(value[0], value[1])
    else:
        normalized = Arity(value, value)
    if normalized.min < 0:
        msg = "Minimum arity must not be negative."
        raise ValueError(msg)
    if normalized.max is not None and normalized.max < 0:
        msg = "Maximum arity must not be negative."
        raise ValueError(msg)
    if normalized.max is not None and normalized.min > normalized.max:
        msg = "Minimum arity must be less than maximum arity."
        raise ValueError(msg)
    return normalized


class OptionSpec:
    """Specification for a command-line option.

    An option is a named parameter that typically appears with `--` (long form)
    or `-` (short form) prefixes. Options can accept zero or more values and
    can be configured with various behaviors for accumulation, negation, and
    flag value coercion.

    The `OptionSpec` is immutable after construction and defines all the metadata
    needed for the parser to recognize and process an option.
    """

    __slots__: tuple[str, ...] = (
        "_accumulation_mode",
        "_arity",
        "_const_value",
        "_falsey_flag_values",
        "_flatten_values",
        "_is_flag",
        "_long",
        "_name",
        "_negation_words",
        "_short",
        "_truthy_flag_values",
    )

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        *,
        long: "str | Sequence[str] | None" = None,
        short: "str | Sequence[str] | None" = None,
        arity: int | Arity | tuple[int, int] | None = None,
        accumulation_mode: AccumulationMode = AccumulationMode.LAST_WINS,
        is_flag: bool = False,
        falsey_flag_values: "str | Sequence[str] | None" = None,
        truthy_flag_values: "str | Sequence[str] | None" = None,
        negation_words: "str | Sequence[str] | None" = None,
        const_value: str | None = None,
        flatten_values: bool | None = None,
    ) -> None:
        """Initialize an option specification.

        Args:
            name: The canonical option name (without dashes). Must be alphanumeric
                with optional dashes/underscores (not at start/end).
            long: Long form option name(s). If `None` and name has `>1` character,
                uses name as the long form. Can be a single string or sequence.
            short: Short form option name(s). If `None` and name has `1` character,
                uses name as the short form. Must be single alphanumeric characters.
            arity: Number of values the option accepts. Can be an int,
                [`Arity`][aclaf.parser.Arity] tuple, or `(min, max)` tuple.
                Default is `Arity(1, 1)`. Flags typically use `Arity(0, 0)`.
            accumulation_mode: How to handle repeated option occurrences.
                Default is [`LAST_WINS`][aclaf.parser.AccumulationMode.LAST_WINS].
            is_flag: Whether this is a boolean flag option. Flags have special
                behavior for value coercion and default arity of `0`.
            falsey_flag_values: Values that set the flag to `False` when using
                `--flag=value` syntax (requires `allow_equals_for_flags`).
            truthy_flag_values: Values that set the flag to `True` when using
                `--flag=value` syntax (requires `allow_equals_for_flags`).
            negation_words: Prefix words for negation (e.g., `no` allows
                `--no-verbose`). Only applies to flags.
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

        Raises:
            ValueError: If the option configuration is invalid (e.g., invalid
                name format, overlapping flag values, etc.).
        """
        self._name: str = self._validate_option_name(name)
        self._long: frozenset[str] = self._validate_long_names(self._name, long)
        self._short: frozenset[str] = self._validate_short_names(self._name, short)
        self._arity: Arity = _validate_arity(arity)
        self._accumulation_mode: AccumulationMode = accumulation_mode
        self._is_flag: bool = is_flag
        self._falsey_flag_values: frozenset[str] | None
        self._truthy_flag_values: frozenset[str] | None
        self._falsey_flag_values, self._truthy_flag_values = self._validate_flag_values(
            falsey_flag_values, truthy_flag_values
        )
        self._negation_words: frozenset[str] | None = self._validate_negation_words(
            negation_words
        )
        self._const_value: str | None = const_value
        self._flatten_values: bool | None = flatten_values

        # Validate flatten_values is only explicitly set with COLLECT mode
        if flatten_values is True and accumulation_mode != AccumulationMode.COLLECT:
            msg = (
                f"Option '{name}': flatten_values=True has no effect with "
                f"accumulation_mode={accumulation_mode}. Flattening only applies "
                f"to COLLECT mode."
            )
            warnings.warn(msg, stacklevel=2)

    @property
    def name(self) -> str:
        """The canonical option name."""
        return self._name

    @property
    def long(self) -> frozenset[str]:
        """Frozenset of long-form option names (without `--` prefix)."""
        return self._long

    @property
    def short(self) -> frozenset[str]:
        """Frozenset of short-form option names (without `-` prefix)."""
        return self._short

    @property
    def arity(self) -> Arity | None:
        """The arity specification defining how many values this option accepts."""
        return self._arity

    @property
    def negation_words(self) -> frozenset[str] | None:
        """Frozenset of negation prefix words (e.g., `no` for `--no-flag`)."""
        return self._negation_words

    @property
    def accumulation_mode(self) -> AccumulationMode:
        """How repeated occurrences of this option are handled."""
        return self._accumulation_mode

    @property
    def is_flag(self) -> bool:
        """Whether this option is a boolean flag."""
        return self._is_flag

    @property
    def truthy_flag_values(self) -> frozenset[str] | None:
        """Frozenset of values that set this flag to `True`.

        For `--flag=value` syntax.
        """
        return self._truthy_flag_values

    @property
    def falsey_flag_values(self) -> frozenset[str] | None:
        """Frozenset of values that set this flag to `False`.

        For `--flag=value` syntax.
        """
        return self._falsey_flag_values

    @property
    def const_value(self) -> str | None:
        """Constant value to use when the option is specified without a value."""
        return self._const_value

    @property
    def flatten_values(self) -> bool | None:
        """Whether to flatten nested tuples in COLLECT mode.

        When `True` and `accumulation_mode` is
        [`COLLECT`][aclaf.parser.AccumulationMode.COLLECT], values from
        multiple occurrences are flattened into a single tuple instead of
        nested tuples. Only applies when arity allows multiple values
        (`arity.max > 1` or `None`). If `None`, inherits from
        [`CommandSpec`][aclaf.parser.CommandSpec] or
        [`BaseParser`][aclaf.parser.BaseParser] setting.
        """
        return self._flatten_values

    @override
    def __repr__(self) -> str:
        return (
            f"OptionSpec(name={self._name!r}, long={sorted(self._long)!r},"
            f" short={sorted(self._short)!r}, arity={self._arity!r},"
            f" accumulation_mode={self._accumulation_mode!r},"
            f" is_flag={self._is_flag!r},"
            f" truthy_flag_values={sorted(self._truthy_flag_values or [])!r},"
            f" falsey_flag_values={sorted(self._falsey_flag_values or [])!r},"
            f" negation_words={sorted(self._negation_words or [])!r})"
            f" const_value={self._const_value!r}"
        )

    @staticmethod
    def _validate_option_name(
        value: str,
    ) -> str:
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
        return value

    @staticmethod
    def _validate_long_names(
        option_name: str, value: "str | Sequence[str] | None"
    ) -> frozenset[str]:
        if value is None and len(option_name) > 1:
            return frozenset((option_name,))
        if value is None:
            return frozenset()
        normalized = normalize_frozen_str_set(value)
        for name in normalized:
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
        return normalized

    @staticmethod
    def _validate_short_names(
        option_name: str, value: "str | Sequence[str] | None"
    ) -> frozenset[str]:
        if value is None and len(option_name) == 1:
            return frozenset((option_name,))
        if value is None:
            return frozenset()
        normalized = normalize_frozen_str_set(value)
        for name in normalized:
            if len(name) != 1:
                msg = f"Short option name '{name}' must be exactly one character."
                raise ValueError(msg)
            if not re.match(SHORT_NAME_REGEX, name):
                msg = (
                    f"Short option name '{name}' must be exactly one alphanumeric"
                    " character."
                )
                raise ValueError(msg)
        return normalized

    @staticmethod
    def _validate_flag_values(
        falsey_values: "str | Sequence[str] | None",
        truthy_values: "str | Sequence[str] | None",
    ) -> tuple[frozenset[str] | None, frozenset[str] | None]:
        truthy = (
            normalize_frozen_str_set(truthy_values)
            if truthy_values is not None
            else None
        )
        falsey = (
            normalize_frozen_str_set(falsey_values)
            if falsey_values is not None
            else None
        )
        if truthy is not None and falsey is not None:
            intersection = truthy.intersection(falsey)
            if intersection:
                msg = (
                    f"Flag option truthy and falsey values must not overlap: "
                    f"{', '.join(intersection)}"
                )
                raise ValueError(msg)
        return falsey, truthy

    @staticmethod
    def _validate_negation_words(
        value: "str | Sequence[str] | None",
    ) -> frozenset[str]:
        if value is None:
            return frozenset()
        normalized = normalize_frozen_str_set(value)
        for name in normalized:
            if len(name) < 1:
                msg = "Negation word must have at least one character."
                raise ValueError(msg)
            if re.search(r"\s", name):
                msg = f"Negation word '{name}' must not contain whitespace."
                raise ValueError(msg)
        return normalized


class PositionalSpec:
    """Specification for a positional argument.

    A positional argument is a command-line argument identified by its
    position rather than by a name/flag. Positionals are matched to their
    specifications in order after all options have been consumed.

    The `PositionalSpec` is immutable after construction and defines the
    name and arity for a positional parameter.
    """

    __slots__: tuple[str, ...] = ("_arity", "_name")

    def __init__(
        self, name: str, *, arity: int | Arity | tuple[int, int] | None
    ) -> None:
        """Initialize a positional argument specification.

        Args:
            name: The parameter name for this positional. Used to identify
                the positional in the parse result.
            arity: Number of values this positional accepts. Can be an int,
                [`Arity`][aclaf.parser.Arity] tuple, or `(min, max)` tuple.
                Default is `Arity(1, 1)`.

        Raises:
            ValueError: If the arity is invalid (e.g., negative values).
        """
        self._name: str = name
        self._arity: Arity = _validate_arity(arity)

    @property
    def name(self) -> str:
        """The positional parameter name."""
        return self._name

    @property
    def arity(self) -> Arity:
        """The arity specification defining how many values this positional accepts."""
        return self._arity

    @override
    def __repr__(self) -> str:
        return f"PositionalSpec(name={self._name!r}, arity={self._arity!r})"
