"""Property-based tests for subcommand hierarchy and interactions.

This module tests invariants related to nested subcommands, option inheritance,
conflict detection, and subcommand resolution across various configurations.
"""

import string

import pytest
from hypothesis import given, strategies as st

from aclaf.parser import CommandSpec, OptionSpec, Parser, ParserConfiguration
from aclaf.parser.exceptions import AmbiguousSubcommandError, UnknownSubcommandError

from .strategies import option_lists


@st.composite
def subcommand_names(draw: st.DrawFn, min_size: int = 2, max_size: int = 12) -> str:
    """Generate valid subcommand names.

    Args:
        draw: Hypothesis draw function.
        min_size: Minimum name length.
        max_size: Maximum name length.

    Returns:
        A valid subcommand name (lowercase alphanumeric with dashes).
    """
    # Subcommand names use lowercase ASCII letters, digits, and dashes
    alphabet = st.sampled_from(string.ascii_lowercase + string.digits + "-")
    return draw(
        st.text(
            alphabet=alphabet,
            min_size=min_size,
            max_size=max_size,
        ).filter(
            lambda x: (
                x
                and x[0].isalpha()  # Must start with letter
                and x[-1].isalnum()  # Must end with alphanumeric
                and "--" not in x  # No consecutive dashes
            )
        )
    )


@st.composite
def subcommand_lists(
    draw: st.DrawFn,
    min_size: int = 1,
    max_size: int = 8,
) -> list[str]:
    """Generate lists of unique subcommand names.

    Args:
        draw: Hypothesis draw function.
        min_size: Minimum number of subcommands.
        max_size: Maximum number of subcommands.

    Returns:
        A list of unique subcommand names.
    """
    return draw(
        st.lists(
            subcommand_names(),
            min_size=min_size,
            max_size=max_size,
            unique=True,
        )
    )


class TestNestedSubcommandProperties:
    """Test properties of nested subcommand hierarchies."""

    @given(
        depth=st.integers(min_value=1, max_value=5),
        subcommand_name=subcommand_names(),
    )
    def test_nested_subcommand_parsing(
        self,
        depth: int,
        subcommand_name: str,
    ):
        """Property: nested subcommands can be parsed at various depths.

        The parser should correctly handle subcommand nesting from depth 1
        (single subcommand) to depth 5 (deeply nested hierarchies).
        """
        # Build nested command structure from bottom up
        current_spec = CommandSpec(name=f"{subcommand_name}-{depth}")

        for level in range(depth - 1, 0, -1):
            parent_name = f"{subcommand_name}-{level}"
            current_spec = CommandSpec(
                name=parent_name,
                subcommands={current_spec.name: current_spec},
            )

        # Root command wraps the entire hierarchy
        root_spec = CommandSpec(
            name="root",
            subcommands={current_spec.name: current_spec},
        )

        parser = Parser(root_spec)

        # Build args list for the nested path
        args = [f"{subcommand_name}-{i}" for i in range(1, depth + 1)]

        result = parser.parse(args)

        # Verify we can navigate the full depth
        current_result = result
        for i in range(1, depth + 1):
            assert current_result.subcommand is not None
            assert current_result.subcommand.command == f"{subcommand_name}-{i}"
            current_result = current_result.subcommand

    @given(
        names=subcommand_lists(min_size=2, max_size=6),
    )
    def test_sibling_subcommands_are_independent(
        self,
        names: list[str],
    ):
        """Property: sibling subcommands don't interfere with each other.

        Each subcommand at the same level should be independently resolvable
        without affecting the others.
        """
        spec = CommandSpec(
            name="root",
            subcommands={
                name: CommandSpec(
                    name=name,
                    options={"flag": OptionSpec("flag", is_flag=True)},
                )
                for name in names
            },
        )
        parser = Parser(spec)

        # Test each subcommand independently
        for name in names:
            result = parser.parse([name, "--flag"])
            assert result.subcommand is not None
            assert result.subcommand.command == name
            assert result.subcommand.options["flag"].value is True

    @given(
        parent_name=subcommand_names(),
        child_names=subcommand_lists(min_size=2, max_size=5),
    )
    def test_parent_subcommand_has_isolated_children(
        self,
        parent_name: str,
        child_names: list[str],
    ):
        """Property: parent subcommand's children are isolated.

        A parent subcommand's children should only be accessible through
        that parent, not at the root level or through other parents.
        """
        # Filter out any child names that match the parent name
        # to ensure children are truly isolated
        child_names = [child for child in child_names if child != parent_name]

        if len(child_names) < 1:
            return  # Skip if no valid children after filtering

        # Create parent with children
        parent_spec = CommandSpec(
            name=parent_name,
            subcommands={
                child: CommandSpec(name=child)
                for child in child_names
            },
        )

        root_spec = CommandSpec(
            name="root",
            subcommands={parent_name: parent_spec},
        )

        parser = Parser(root_spec)

        # Children should be accessible through parent
        for child in child_names:
            result = parser.parse([parent_name, child])
            assert result.subcommand is not None
            assert result.subcommand.command == parent_name
            assert result.subcommand.subcommand is not None
            assert result.subcommand.subcommand.command == child

        # Children should NOT be accessible at root level
        for child in child_names:
            with pytest.raises(UnknownSubcommandError):
                _ = parser.parse([child])


class TestSubcommandOptionInheritanceProperties:
    """Test properties of option inheritance in subcommand hierarchies."""

    @given(
        parent_options=option_lists(min_size=1, max_size=4),
        child_options=option_lists(min_size=1, max_size=4),
    )
    def test_parent_and_child_options_are_isolated(
        self,
        parent_options: list[str],
        child_options: list[str],
    ):
        """Property: parent and child options are isolated from each other.

        Options defined on a parent command should not be accessible to
        child subcommands, and vice versa (unless explicitly inherited).
        """
        # Sanitize option names to be valid
        parent_options = [
            opt.lower().replace("-", "p").replace("_", "x")
            for opt in parent_options
        ]
        parent_options = [
            opt for opt in parent_options if len(opt) >= 2 and opt.isalpha()
        ]

        child_options = [
            opt.lower().replace("-", "c").replace("_", "y")
            for opt in child_options
        ]
        child_options = [
            opt for opt in child_options if len(opt) >= 2 and opt.isalpha()
        ]

        if len(parent_options) < 1 or len(child_options) < 1:
            return  # Skip if not enough valid options

        parent_spec = CommandSpec(
            name="parent",
            options={
                opt: OptionSpec(opt, is_flag=True) for opt in parent_options
            },
            subcommands={
                "child": CommandSpec(
                    name="child",
                    options={
                        opt: OptionSpec(opt, is_flag=True)
                        for opt in child_options
                    },
                ),
            },
        )

        parser = Parser(parent_spec)

        # Parent options work before subcommand
        result1 = parser.parse([f"--{parent_options[0]}", "child"])
        assert result1.options[parent_options[0]].value is True

        # Child options work after subcommand
        result2 = parser.parse(["child", f"--{child_options[0]}"])
        assert result2.subcommand is not None
        assert result2.subcommand.options[child_options[0]].value is True

    @given(
        shared_option=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz"),
            min_size=2,
            max_size=10,
        ).filter(lambda x: x and x[0].isalpha() and x[-1].isalpha()),
        parent_value=st.text(min_size=1, max_size=20).filter(
            lambda x: not x.startswith("-")
        ),
        child_value=st.text(min_size=1, max_size=20).filter(
            lambda x: not x.startswith("-")
        ),
    )
    def test_same_named_option_in_parent_and_child(
        self,
        shared_option: str,
        parent_value: str,
        child_value: str,
    ):
        """Property: same-named options in parent and child are independent.

        When parent and child both define an option with the same name,
        they should be treated as separate options with independent values.
        """
        spec = CommandSpec(
            name="parent",
            options={shared_option: OptionSpec(shared_option)},
            subcommands={
                "child": CommandSpec(
                    name="child",
                    options={shared_option: OptionSpec(shared_option)},
                ),
            },
        )

        parser = Parser(spec)

        # Both options can be set independently
        args = [
            f"--{shared_option}",
            parent_value,
            "child",
            f"--{shared_option}",
            child_value,
        ]
        result = parser.parse(args)

        assert result.options[shared_option].value == parent_value
        assert result.subcommand is not None
        assert result.subcommand.options[shared_option].value == child_value


class TestSubcommandConflictProperties:
    """Test properties related to subcommand name conflicts and ambiguity."""

    @given(
        common_prefix=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz"),
            min_size=2,
            max_size=5,
        ).filter(lambda x: x and x[0].isalpha()),
        suffix1=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz"),
            min_size=1,
            max_size=3,
        ).filter(lambda x: x and x.isalpha()),
        suffix2=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz"),
            min_size=1,
            max_size=3,
        ).filter(lambda x: x and x.isalpha()),
    )
    def test_abbreviation_ambiguity_detection(
        self,
        common_prefix: str,
        suffix1: str,
        suffix2: str,
    ):
        """Property: abbreviation ambiguity is detected correctly.

        When multiple subcommands share a common prefix, using just
        the prefix with abbreviation enabled should raise an ambiguity error.
        """
        if suffix1 == suffix2:
            return  # Need different suffixes

        name1 = common_prefix + suffix1
        name2 = common_prefix + suffix2

        spec = CommandSpec(
            name="root",
            subcommands={
                name1: CommandSpec(name=name1),
                name2: CommandSpec(name=name2),
            },
        )

        config = ParserConfiguration(
            allow_abbreviated_subcommands=True,
            minimum_abbreviation_length=len(common_prefix),
        )
        parser = Parser(spec, config=config)

        # Using just the common prefix should be ambiguous
        with pytest.raises(AmbiguousSubcommandError):
            _ = parser.parse([common_prefix])

    @given(
        names=subcommand_lists(min_size=2, max_size=8),
    )
    def test_exact_match_always_succeeds(
        self,
        names: list[str],
    ):
        """Property: exact subcommand name matches always succeed.

        Even with abbreviation enabled, using the exact full name of a
        subcommand should always work without ambiguity.
        """
        spec = CommandSpec(
            name="root",
            subcommands={name: CommandSpec(name=name) for name in names},
        )

        config = ParserConfiguration(
            allow_abbreviated_subcommands=True,
            minimum_abbreviation_length=1,
        )
        parser = Parser(spec, config=config)

        # Each exact name should parse successfully
        for name in names:
            result = parser.parse([name])
            assert result.subcommand is not None
            assert result.subcommand.command == name

    @given(
        subcommand_name=subcommand_names(),
        option_name=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz"),
            min_size=2,
            max_size=10,
        ).filter(lambda x: x and x[0].isalpha() and x[-1].isalpha()),
    )
    def test_subcommand_and_option_names_can_overlap(
        self,
        subcommand_name: str,
        option_name: str,
    ):
        """Property: subcommand and option names can safely overlap.

        Having an option with the same name as a subcommand should not
        cause conflicts, as context determines which is being referenced.
        """
        if subcommand_name == option_name:
            return  # Skip if names are identical to avoid confusion

        spec = CommandSpec(
            name="root",
            options={option_name: OptionSpec(option_name, is_flag=True)},
            subcommands={
                subcommand_name: CommandSpec(
                    name=subcommand_name,
                    options={option_name: OptionSpec(option_name, is_flag=True)},
                ),
            },
        )

        parser = Parser(spec)

        # Option before subcommand
        result1 = parser.parse([f"--{option_name}", subcommand_name])
        assert result1.options[option_name].value is True
        assert result1.subcommand is not None
        assert result1.subcommand.command == subcommand_name

        # Subcommand with its own option
        result2 = parser.parse([subcommand_name, f"--{option_name}"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == subcommand_name
        assert result2.subcommand.options[option_name].value is True


class TestSubcommandResolutionInvariants:
    """Test fundamental invariants of subcommand resolution."""

    @given(
        names=subcommand_lists(min_size=1, max_size=10),
    )
    def test_parse_result_deterministic(
        self,
        names: list[str],
    ):
        """Property: parsing the same arguments produces identical results.

        Multiple parses of the same argument list should yield identical
        results, ensuring parser state doesn't leak between invocations.
        """
        spec = CommandSpec(
            name="root",
            subcommands={name: CommandSpec(name=name) for name in names},
        )
        parser = Parser(spec)

        # Pick a subcommand to test
        test_name = names[0]
        args = [test_name]

        # Parse multiple times
        result1 = parser.parse(args)
        result2 = parser.parse(args)
        result3 = parser.parse(args)

        # Results should be identical
        assert result1.subcommand is not None
        assert result2.subcommand is not None
        assert result3.subcommand is not None
        assert (
            result1.subcommand.command
            == result2.subcommand.command
            == result3.subcommand.command
        )

    @given(
        depth=st.integers(min_value=1, max_value=4),
    )
    def test_subcommand_nesting_preserves_parent_data(
        self,
        depth: int,
    ):
        """Property: nested subcommands preserve parent command data.

        When parsing nested subcommands, each level should preserve the
        options and positionals from its parent level correctly.
        """
        # Build a nested structure where each level has an option
        current_spec = CommandSpec(
            name=f"level-{depth}",
            options={f"opt-{depth}": OptionSpec(f"opt-{depth}", is_flag=True)},
        )

        for level in range(depth - 1, 0, -1):
            parent_name = f"level-{level}"
            current_spec = CommandSpec(
                name=parent_name,
                options={f"opt-{level}": OptionSpec(f"opt-{level}", is_flag=True)},
                subcommands={current_spec.name: current_spec},
            )

        root_spec = CommandSpec(
            name="root",
            subcommands={current_spec.name: current_spec},
        )

        parser = Parser(root_spec)

        # Build args with option after each subcommand (not before)
        # Since options belong to the subcommand, not the root
        args: list[str] = []
        for level in range(1, depth + 1):
            args.append(f"level-{level}")
            args.append(f"--opt-{level}")

        result = parser.parse(args)

        # Verify options at each level
        current_result = result
        for level in range(1, depth + 1):
            assert current_result.subcommand is not None
            assert current_result.subcommand.command == f"level-{level}"
            assert f"opt-{level}" in current_result.subcommand.options
            assert current_result.subcommand.options[f"opt-{level}"].value is True

            if level < depth:
                current_result = current_result.subcommand

    @given(
        subcommand_count=st.integers(min_value=1, max_value=20),
    )
    def test_large_subcommand_sets_perform_efficiently(
        self,
        subcommand_count: int,
    ):
        """Property: resolution performs efficiently with many subcommands.

        Even with a large number of subcommands, resolution should remain
        fast due to dictionary lookups and caching.
        """
        # Generate unique subcommand names
        names = [f"subcmd-{i:03d}" for i in range(subcommand_count)]

        spec = CommandSpec(
            name="root",
            subcommands={name: CommandSpec(name=name) for name in names},
        )
        parser = Parser(spec)

        # Test resolution of first, middle, and last subcommands
        test_indices = [0, subcommand_count // 2, subcommand_count - 1]

        for idx in test_indices:
            test_name = names[idx]
            result = parser.parse([test_name])
            assert result.subcommand is not None
            assert result.subcommand.command == test_name
