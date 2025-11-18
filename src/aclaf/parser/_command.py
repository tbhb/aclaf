import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict
from typing_extensions import override

from ._constants import COMMAND_NAME_REGEX
from ._exceptions import (
    AmbiguousOptionError,
    AmbiguousSubcommandError,
    UnknownOptionError,
)

if TYPE_CHECKING:
    from ._parameters import OptionSpec, PositionalSpec


class CommandSpecInput(TypedDict, total=False):
    name: str
    aliases: frozenset[str]
    options: dict[str, "OptionSpec"]
    positionals: dict[str, "PositionalSpec"]
    subcommands: dict[str, "CommandSpec"]
    case_insensitive_aliases: bool
    case_insensitive_options: bool
    flatten_option_values: bool


@dataclass(slots=True, frozen=True)
class CommandSpec:
    """Specification for a command or subcommand.

    A CommandSpec defines the complete structure of a command, including its
    name, aliases, parameters, and subcommands. It is immutable after construction
    and serves as the blueprint for parsing command-line arguments.

    The spec uses caching for resolution operations to ensure fast lookups during
    parsing. All validation is performed during construction to catch errors early.

    Attributes:
        name: The canonical command name. Must start with an alphabetic
            character and may contain alphanumeric characters, dashes, and
            underscores.
        aliases: Frozenset of alternative names for this command. Each alias
            must follow the same naming rules as the command name. Default:
            empty frozenset.
        options: Dictionary mapping option names to their specifications.
            Default: empty dict.
        positionals: Dictionary mapping positional parameter names to their
            specifications. Default: empty dict.
        subcommands: Dictionary mapping subcommand names to their specifications.
            Default: empty dict.
        case_insensitive_aliases: Whether command and subcommand name
            matching should be case-insensitive.
        case_insensitive_options: Whether option name matching should be
            case-insensitive.
        flatten_option_values: Default `flatten_values` setting for all
            options in this command. Options can override with their own
            `flatten_values`. If `None`, inherits from
            [`BaseParser.flatten_option_values`][aclaf.parser.BaseParser.flatten_option_values].
            Default: `None`.
    """

    name: str
    aliases: frozenset[str] = field(default_factory=frozenset)
    options: dict[str, "OptionSpec"] = field(default_factory=dict)
    positionals: dict[str, "PositionalSpec"] = field(default_factory=dict)
    subcommands: dict[str, "CommandSpec"] = field(default_factory=dict)
    case_insensitive_aliases: bool = False
    case_insensitive_options: bool = False
    flatten_option_values: bool | None = None

    _option_names_cache: dict[tuple[bool, bool], dict[str, tuple[str, str]]] | None = (
        None
    )
    _subcommand_names_cache: dict[bool, dict[str, tuple[str, str]]] | None = None
    _subcommand_names_and_aliases_cache: (
        dict[bool, dict[str, tuple[str, str]]] | None
    ) = None

    def __post_init__(self) -> None:
        self._validate_name()
        self._validate_aliases()
        self._validate_options()
        self._validate_positionals()
        self._validate_subcommands()

    def resolve_option(
        self,
        name: str,
        *,
        allow_abbreviations: bool = False,
        case_insensitive: bool = False,
        convert_underscores: bool = False,
        minimum_abbreviation_length: int = 3,
    ) -> tuple[str, "OptionSpec"]:
        """Resolve an option name to its matched name and specification.

        Args:
            name: The option name to resolve (without leading dashes).
            allow_abbreviations: Whether to allow prefix matching for option names.
            case_insensitive: Whether to match case-insensitively. If `None`,
                uses the spec's configured `case_insensitive_options` setting.
            convert_underscores: Whether to convert underscores to dashes in the
                input name before matching.
            minimum_abbreviation_length: Minimum length required for abbreviation
                matching. Only enforced when `allow_abbreviations` is `True`.

        Returns:
            A tuple of `(matched_name, option_spec)` where `matched_name` is the
            exact option name that was matched (which may be an alias or
            abbreviation).

        Raises:
            [`UnknownOptionError`][aclaf.parser.UnknownOptionError]: If the
                option name doesn't match any option.
            [`AmbiguousOptionError`][aclaf.parser.AmbiguousOptionError]: If
                abbreviation matching is enabled and the name matches multiple
                options.
        """
        names = self._all_option_names(
            case_insensitive=case_insensitive, convert_underscores=convert_underscores
        )
        # Apply normalization: underscores to dashes, then case
        search_name = name.replace("_", "-") if convert_underscores else name
        search_name = search_name.lower() if case_insensitive else search_name

        # Check for exact match first
        # (works for both abbreviated and non-abbreviated modes)
        if search_name in names:
            return names[search_name][0], self.options[names[search_name][1]]

        # If abbreviations allowed, try prefix matching
        if allow_abbreviations:
            possible_names = names.keys()
            candidates = [n for n in possible_names if n.startswith(search_name)]

            # Check minimum abbreviation length
            if len(search_name) < minimum_abbreviation_length:
                # Only allow short abbreviations if there are multiple candidates
                # that all refer to the same option (i.e., multiple aliases)
                if len(candidates) == 0:
                    raise UnknownOptionError(name, tuple(names.keys()))

                if len(candidates) == 1:
                    # Single candidate but too short - enforce minimum length
                    raise UnknownOptionError(name, tuple(names.keys()))

                option_specs = {names[c][1] for c in candidates}
                if len(option_specs) > 1:
                    # Multiple different options - ambiguous and too short
                    raise UnknownOptionError(name, tuple(names.keys()))
                # Multiple candidates for same option (aliases) - allow even if short

            if len(candidates) == 0:
                raise UnknownOptionError(name, tuple(possible_names))
            if len(candidates) == 1:
                # Return the canonical name from the mapping
                canonical_key = candidates[0]
                return names[canonical_key][0], self.options[names[canonical_key][1]]

            # Multiple candidates - check if they all refer to the same option spec
            option_specs = {names[c][1] for c in candidates}
            if len(option_specs) == 1:
                # All candidates refer to the same option - not ambiguous
                canonical_key = candidates[0]
                return names[canonical_key][0], self.options[names[canonical_key][1]]

            raise AmbiguousOptionError(name, [names[c][0] for c in candidates])

        raise UnknownOptionError(name, tuple(n[0] for n in names.values()))

    def resolve_subcommand(  # noqa: PLR0911
        self,
        name: str,
        *,
        allow_aliases: bool = False,
        allow_abbreviations: bool = False,
        case_insensitive: bool = False,
        minimum_abbreviation_length: int = 3,
    ) -> tuple[str, "CommandSpec"] | None:
        """Resolve a subcommand name to the matched name and specification.

        Args:
            name: The subcommand name to resolve.
            allow_aliases: Whether to match against subcommand aliases.
            allow_abbreviations: Whether to allow prefix matching for subcommand names.
            case_insensitive: Whether to match case-insensitively. If `None`,
                uses the spec's configured `case_insensitive_aliases` setting.
            minimum_abbreviation_length: Minimum length required for abbreviation
                matching. Only enforced when `allow_abbreviations` is `True`.

        Returns:
            A tuple of `(matched_name, subcommand_spec)` where `matched_name` is the
            name that was actually used (could be an alias or abbreviation), or `None`
            if no subcommand matches.

        Raises:
            [`AmbiguousSubcommandError`][aclaf.parser.AmbiguousSubcommandError]:
                If abbreviation matching is enabled and the name matches
                multiple subcommands.
        """
        search_name = name.lower() if case_insensitive else name

        # Get the appropriate name mapping
        names = (
            self._all_subcommand_names_and_aliases(case_insensitive=case_insensitive)
            if allow_aliases
            else self._all_subcommand_names(case_insensitive=case_insensitive)
        )

        # Check for exact match first
        # (works for both abbreviated and non-abbreviated modes)
        if search_name in names:
            canonical_name, subcommand_name = names[search_name]
            return canonical_name, self.subcommands[subcommand_name]

        # If abbreviations allowed, try prefix matching
        if allow_abbreviations:
            candidates = [n for n in names if n.startswith(search_name)]

            # Check minimum abbreviation length
            if len(search_name) < minimum_abbreviation_length:
                # Only allow short abbreviations if there are multiple candidates
                # that all refer to the same subcommand (i.e., name + aliases)
                if len(candidates) == 0:
                    return None

                if len(candidates) == 1:
                    # Single candidate but too short - enforce minimum length
                    return None

                subcommand_specs = {names[c][1] for c in candidates}
                if len(subcommand_specs) > 1:
                    # Multiple different subcommands - ambiguous and too short
                    raise AmbiguousSubcommandError(
                        name, [names[c][0] for c in candidates]
                    )
                # Multiple candidates for same subcommand (name + aliases) - allow
                # even if short

            if len(candidates) == 0:
                return None
            if len(candidates) == 1:
                canonical_key = candidates[0]
                canonical_name, subcommand_name = names[canonical_key]
                return canonical_name, self.subcommands[subcommand_name]

            # Multiple candidates - check if they all refer to the same subcommand spec
            subcommand_specs = {names[c][1] for c in candidates}
            if len(subcommand_specs) == 1:
                # All candidates refer to the same subcommand - not ambiguous
                canonical_key = candidates[0]
                canonical_name, subcommand_name = names[canonical_key]
                return canonical_name, self.subcommands[subcommand_name]

            raise AmbiguousSubcommandError(name, [names[c][0] for c in candidates])

        return None

    def _all_option_names(  # noqa: PLR0912
        self, *, case_insensitive: bool = False, convert_underscores: bool = False
    ) -> dict[str, tuple[str, str]]:
        """Build a mapping of option names to `(canonical_name, option_spec_name)`.

        Args:
            spec: The command specification
            case_insensitive: Whether to normalize names to lowercase for matching
            convert_underscores: Whether to convert underscores to dashes in option
                names during matching. When enabled, both spec names and user input
                are normalized to use dashes for bidirectional equivalence.

        Returns:
            A dictionary mapping search keys to tuples of `(canonical_name,
            option_spec_name)`. The search key is normalized according to the flags:
            first underscore-to-dash conversion (if enabled), then case normalization
            (if enabled). The `canonical_name` is the original option name (e.g.,
            `verbose`, `no-verbose`). The `option_spec_name` is the name of the
            [`OptionSpec`][aclaf.parser.OptionSpec] (e.g., `verbose`).
        """
        cache_key = (case_insensitive, convert_underscores)
        if (
            self._option_names_cache is not None
            and cache_key in self._option_names_cache
        ):
            return self._option_names_cache[cache_key]
        names: dict[str, tuple[str, str]] = {}
        for option in self.options.values():
            if option.long:
                if isinstance(option.long, str):
                    # Apply normalization: underscores to dashes first, then case
                    normalized = (
                        option.long.replace("_", "-")
                        if convert_underscores
                        else option.long
                    )
                    search_key = normalized.lower() if case_insensitive else normalized
                    names[search_key] = (option.long, option.name)
                else:
                    for long_name in option.long:
                        # Apply normalization: underscores to dashes first, then case
                        normalized = (
                            long_name.replace("_", "-")
                            if convert_underscores
                            else long_name
                        )
                        search_key = (
                            normalized.lower() if case_insensitive else normalized
                        )
                        names[search_key] = (long_name, option.name)
                        if option.negation_words:
                            for negation_word in option.negation_words:
                                # Build negated name from normalized base name
                                negated_name = f"{negation_word}-{normalized}"
                                search_key = (
                                    negated_name.lower()
                                    if case_insensitive
                                    else negated_name
                                )
                                names[search_key] = (negated_name, option.name)
            if option.short:
                if isinstance(option.short, str):
                    search_key = (
                        option.short.lower() if case_insensitive else option.short
                    )
                    names[search_key] = (option.short, option.name)
                else:
                    for short_name in option.short:
                        search_key = (
                            short_name.lower() if case_insensitive else short_name
                        )
                        names[search_key] = (short_name, option.name)
        if not self._option_names_cache:
            object.__setattr__(self, "_option_names_cache", {})
        self._option_names_cache[cache_key] = names  # pyright: ignore[reportOptionalSubscript]
        return names

    def _all_subcommand_names(
        self, *, case_insensitive: bool = False
    ) -> dict[str, tuple[str, str]]:
        """Build a mapping of subcommand names to tuples.

        Args:
            spec: The command specification
            case_insensitive: Whether to normalize names to lowercase for matching

        Returns:
            A dictionary mapping search keys to tuples of `(canonical_name,
            subcommand_spec_name)`. The search key is lowercase if
            `case_insensitive=True`, otherwise original case. Both `canonical_name`
            and `subcommand_spec_name` are the same (the subcommand's name).
        """
        if (
            self._subcommand_names_cache
            and case_insensitive in self._subcommand_names_cache
        ):
            return self._subcommand_names_cache[case_insensitive]
        names: dict[str, tuple[str, str]] = {}
        for subcommand in self.subcommands.values():
            search_key = (
                subcommand.name.lower() if case_insensitive else subcommand.name
            )
            names[search_key] = (subcommand.name, subcommand.name)
        if not self._subcommand_names_cache:
            object.__setattr__(self, "_subcommand_names_cache", {})
        self._subcommand_names_cache[case_insensitive] = names  # pyright: ignore[reportOptionalSubscript]
        return names

    def _all_subcommand_names_and_aliases(
        self, *, case_insensitive: bool = False
    ) -> dict[str, tuple[str, str]]:
        """Build a mapping of subcommand names and aliases to tuples.

        Args:
            spec: The command specification
            case_insensitive: Whether to normalize names to lowercase for matching

        Returns:
            A dictionary mapping search keys to tuples of `(canonical_name,
            subcommand_spec_name)`. The search key is lowercase if
            `case_insensitive=True`, otherwise original case. The `canonical_name`
            is the original name/alias used (e.g., `rm`). The `subcommand_spec_name`
            is the name of the [`CommandSpec`][aclaf.parser.CommandSpec] (e.g.,
            `remove`).
        """
        if (
            self._subcommand_names_and_aliases_cache
            and case_insensitive in self._subcommand_names_and_aliases_cache
        ):
            return self._subcommand_names_and_aliases_cache[case_insensitive]
        names: dict[str, tuple[str, str]] = {}
        for subcommand in self.subcommands.values():
            search_key = (
                subcommand.name.lower() if case_insensitive else subcommand.name
            )
            names[search_key] = (subcommand.name, subcommand.name)
            for alias in subcommand.aliases:
                search_key = alias.lower() if self.case_insensitive_aliases else alias
                names[search_key] = (alias, subcommand.name)

        if not self._subcommand_names_and_aliases_cache:
            object.__setattr__(self, "_subcommand_names_and_aliases_cache", {})
        self._subcommand_names_and_aliases_cache[case_insensitive] = names  # pyright: ignore[reportOptionalSubscript]
        return names

    @override
    def __repr__(self) -> str:
        return (
            f"CommandSpec(name={self.name!r}, aliases={sorted(self.aliases)!r},"
            f" options={list(self.options.keys())!r},"
            f" positionals={list(self.positionals.keys())!r},"
            f" subcommands={list(self.subcommands.keys())!r})"
        )

    def _validate_name(self) -> None:
        if len(self.name) < 1:
            msg = "Command name must not be empty."
            raise ValueError(msg)
        if not re.match(COMMAND_NAME_REGEX, self.name):
            msg = (
                f"Command name {self.name} must start with an alphabetic character and"
                " may contain alphanumeric characters, dashes, and underscores."
            )
            raise ValueError(msg)

    def _validate_aliases(self) -> None:
        for name in self.aliases:
            if not re.match(COMMAND_NAME_REGEX, name):
                msg = (
                    f"Command alias {name} must start with an alphabetic "
                    "character and may contain alphanumeric characters, "
                    "dashes, and underscores."
                )
                raise ValueError(msg)

    def _validate_options(self) -> None:
        name_occurrences: dict[str, tuple[OptionSpec, ...]] = {}
        for option in self.options.values():
            for long_name in option.long:
                _ = name_occurrences.setdefault(long_name, ())
                name_occurrences[long_name] += (option,)
            for short_name in option.short:
                _ = name_occurrences.setdefault(short_name, ())
                name_occurrences[short_name] += (option,)
        name_duplicates = {
            name: (o.name for o in opts)
            for name, opts in name_occurrences.items()
            if len(opts) > 1
        }
        if name_duplicates:
            msg = "Duplicate option names found: " + ", ".join(
                f"{name} (options: {', '.join(duplicates)})"
                for name, duplicates in name_duplicates.items()
            )
            raise ValueError(msg)

    def _validate_positionals(self) -> None:
        # No specific validation needed for positionals at this time
        pass

    def _validate_subcommands(self) -> None:
        name_occurrences: dict[str, list[str]] = {}
        for subcommand in self.subcommands.values():
            name_occurrences.setdefault(subcommand.name, []).append(subcommand.name)
            for alias in subcommand.aliases:
                name_occurrences.setdefault(alias, []).append(subcommand.name)
        duplicates = {
            name: sources
            for name, sources in name_occurrences.items()
            if len(sources) > 1
        }
        if duplicates:
            msg = "Duplicate subcommand names or aliases found: " + ", ".join(
                f"{name} (subcommands: {', '.join(sorted(set(sources)))})"
                for name, sources in duplicates.items()
            )
            raise ValueError(msg)
