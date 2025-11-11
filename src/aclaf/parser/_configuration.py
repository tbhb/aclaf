import re
from dataclasses import dataclass
from typing import Final, TypedDict

from .exceptions import ParserConfigurationError


class ParserConfigurationInput(TypedDict, total=False):
    """Input dictionary for parser configuration settings.

    This TypedDict defines the optional keys that can be provided to
    configure the behavior of a command-line argument parser. Each key
    corresponds to a specific configuration option that controls how
    the parser interprets and processes command-line arguments.

    All keys are optional, allowing users to specify only the settings
    they wish to customize while relying on default values for others.
    """

    allow_abbreviated_subcommands: bool
    allow_abbreviated_options: bool
    allow_equals_for_flags: bool
    allow_aliases: bool
    allow_negative_numbers: bool
    case_insensitive_flags: bool
    case_insensitive_options: bool
    case_insensitive_subcommands: bool
    convert_underscores_to_dashes: bool
    flatten_option_values: bool
    minimum_abbreviation_length: int
    negative_number_pattern: str | None
    strict_options_before_positionals: bool
    truthy_flag_values: tuple[str, ...] | None
    falsey_flag_values: tuple[str, ...] | None


@dataclass(slots=True, frozen=True, unsafe_hash=True)
class ParserConfiguration:
    """Configuration settings for the parser.

    This class encapsulates all configuration options that control the behavior
    of a command-line argument parser. It is used to initialize parser instances
    with specific settings for abbreviation handling, case sensitivity, option
    ordering, and more.

    Attributes:
        allow_abbreviated_subcommands: Enable prefix matching for subcommand
            names (e.g., `sta` matches `start`). Default: `False`.
        allow_abbreviated_options: Enable prefix matching for option names
            (e.g., `--verb` matches `--verbose`). Default: `False`.
        allow_equals_for_flags: Allow `--flag=value` syntax for flag options
            that accept explicit true/false values. Default: `False`.
        allow_aliases: Enable command and option aliases. Default: `True`.
        allow_negative_numbers: Enable parsing of negative numbers (e.g., `-1`,
            `-3.14`, `-1e5`). When enabled, arguments starting with `-` followed by
            a digit are treated as negative numbers if no matching short option
            exists. Options take precedence over negative number interpretation.
            Default: `False`.
        case_insensitive_flags: Ignore case when matching boolean flags.
            Default: `False`.
        case_insensitive_options: Ignore case when matching option names.
            Default: `False`.
        case_insensitive_subcommands: Ignore case when matching subcommand
            names. Default: `False`.
        convert_underscores_to_dashes: Convert underscores to dashes in
            option names during matching (`--foo_bar` matches `--foo-bar`).
            Default: `True`.
        flatten_option_values: Global default for value flattening in
            [AccumulationMode.COLLECT][aclaf.parser.AccumulationMode] mode. When
            `True`, values from multiple option occurrences are flattened
            into a single tuple instead of nested tuples. Can be overridden by
            [`CommandSpec.flatten_option_values`][aclaf.parser.CommandSpec.flatten_option_values]
            or
            [`OptionSpec.flatten_values`][aclaf.parser.OptionSpec.flatten_values].
            Default: `False`.
        minimum_abbreviation_length: Minimum characters required for
            abbreviation matching. Default: `3`.
        negative_number_pattern: Custom regex pattern for negative number
            detection. If `None`, uses `DEFAULT_NEGATIVE_NUMBER_PATTERN`. Only
            used when `allow_negative_numbers` is `True`. The pattern is validated
            for safety (no ReDoS vulnerabilities). Default: `None`.
        strict_options_before_positionals: POSIX-style mode where options
            must appear before positionals. After the first positional,
            all remaining arguments are treated as positionals. Default: `False`
            (GNU-style, options can appear anywhere).
        truthy_flag_values: Custom values that set flags to `True` when using
            `--flag=value` syntax. Default: `None` (uses builtin defaults).
        falsey_flag_values: Custom values that set flags to `False` when using
            `--flag=value` syntax. Default: `None` (uses builtin defaults).
    """

    allow_abbreviated_subcommands: bool = False
    allow_abbreviated_options: bool = False
    allow_aliases: bool = True
    allow_equals_for_flags: bool = False
    allow_negative_numbers: bool = False
    case_insensitive_flags: bool = False
    case_insensitive_options: bool = False
    case_insensitive_subcommands: bool = False
    convert_underscores_to_dashes: bool = True
    flatten_option_values: bool = False
    minimum_abbreviation_length: int = 3
    negative_number_pattern: str | None = None
    strict_options_before_positionals: bool = False
    truthy_flag_values: tuple[str, ...] | None = None
    falsey_flag_values: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.minimum_abbreviation_length < 1:
            msg = (
                f"minimum_abbreviation_length must be at least 1, "
                f"got {self.minimum_abbreviation_length}."
            )
            raise ParserConfigurationError(msg)

        if self.negative_number_pattern is not None:
            self._validate_negative_number_pattern(self.negative_number_pattern)

        self._validate_truthy_flag_values(self.truthy_flag_values)
        self._validate_falsey_flag_values(self.falsey_flag_values)
        self._validate_flag_values_no_overlap(
            self.truthy_flag_values,
            self.falsey_flag_values,
        )

    @staticmethod
    def _validate_negative_number_pattern(pattern: str) -> None:
        try:
            compiled = re.compile(pattern)
        except re.error as e:
            msg = f"Invalid regex pattern: {e}."
            raise ParserConfigurationError(msg) from e

        if compiled.match(""):
            msg = "Pattern must not match empty string."
            raise ParserConfigurationError(msg)

        # Basic ReDoS check (not exhaustive, but catches common cases)
        # Flag nested quantifiers like (a+)+ or (a*)*
        nested_quantifiers = re.compile(r"\([^)]*[+*][^)]*\)[+*]")
        if nested_quantifiers.search(pattern):
            msg = "Pattern contains nested quantifiers which may cause ReDoS."
            raise ParserConfigurationError(msg)

    @staticmethod
    def _validate_truthy_flag_values(values: tuple[str, ...] | None) -> None:
        """Validate truthy flag values.

        Args:
            values: Tuple of truthy flag values, or None to use defaults.

        Raises:
            ParserConfigurationError: If values are invalid (empty tuple or
                contain empty strings).
        """
        if values is None:
            return

        if len(values) == 0:
            msg = (
                "truthy_flag_values must not be empty. "
                "Provide at least one truthy value or use None for defaults."
            )
            raise ParserConfigurationError(msg)

        for idx, value in enumerate(values):
            if len(value) == 0:
                msg = (
                    f"truthy_flag_values must contain only non-empty strings. "
                    f"Found empty string at index {idx}."
                )
                raise ParserConfigurationError(msg)

    @staticmethod
    def _validate_falsey_flag_values(values: tuple[str, ...] | None) -> None:
        """Validate falsey flag values.

        Args:
            values: Tuple of falsey flag values, or None to use defaults.

        Raises:
            ParserConfigurationError: If values are invalid (empty tuple or
                contain empty strings).
        """
        if values is None:
            return

        if len(values) == 0:
            msg = (
                "falsey_flag_values must not be empty. "
                "Provide at least one falsey value or use None for defaults."
            )
            raise ParserConfigurationError(msg)

        for idx, value in enumerate(values):
            if len(value) == 0:
                msg = (
                    f"falsey_flag_values must contain only non-empty strings. "
                    f"Found empty string at index {idx}."
                )
                raise ParserConfigurationError(msg)

    @staticmethod
    def _validate_flag_values_no_overlap(
        truthy: tuple[str, ...] | None,
        falsey: tuple[str, ...] | None,
    ) -> None:
        """Validate truthy and falsey flag values do not overlap.

        Args:
            truthy: Tuple of truthy flag values, or None.
            falsey: Tuple of falsey flag values, or None.

        Raises:
            ParserConfigurationError: If values overlap (same string appears
                in both truthy and falsey).
        """
        # Only check if both are specified
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
            raise ParserConfigurationError(msg)


DEFAULT_PARSER_CONFIGURATION: Final[ParserConfiguration] = ParserConfiguration()
