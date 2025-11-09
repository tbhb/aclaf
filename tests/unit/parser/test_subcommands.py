"""Comprehensive tests for subcommand functionality.

This module tests subcommand parsing including basic resolution, nested subcommands,
subcommand options and positionals, aliases, abbreviations, and complex scenarios.
"""

import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.exceptions import (
    AmbiguousSubcommandError,
    UnknownSubcommandError,
)
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
)


class TestBasicSubcommands:
    """Test basic subcommand resolution and parsing."""

    def test_resolves_exact_match(self):
        """Basic subcommand resolution works."""
        args = ["foo"]
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec("foo"),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.subcommand is not None
        assert result.subcommand.command == "foo"

    def test_recognizes_multiple_subcommands(self):
        """Multiple subcommands are recognized."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(name="start"),
                CommandSpec(name="stop"),
                CommandSpec(name="status"),
            ],
        )
        parser = Parser(spec)

        result1 = parser.parse(["start"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "start"

        result2 = parser.parse(["stop"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "stop"

        result3 = parser.parse(["status"])
        assert result3.subcommand is not None
        assert result3.subcommand.command == "status"

    def test_none_when_not_provided(self):
        """Parser works when no subcommand is provided."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[CommandSpec(name="start")],
        )
        parser = Parser(spec)

        result = parser.parse([])
        assert result.subcommand is None

    def test_unknown_subcommand_raises_error(self):
        """Unknown subcommands raise UnknownSubcommandError."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[CommandSpec(name="start")],
        )
        parser = Parser(spec)

        with pytest.raises(UnknownSubcommandError):
            _ = parser.parse(["unknown"])

    def test_result_includes_name_and_alias_info(self):
        """Result includes subcommand name and alias info."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[CommandSpec(name="start")],
        )
        parser = Parser(spec)

        result = parser.parse(["start"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"
        assert result.subcommand.alias is None


class TestSubcommandOptions:
    """Test subcommand-specific options."""

    def test_option_with_multiple_arity_and_subcommand(self):
        """Options with multiple values work with subcommands."""
        args = ["--opt", "val1", "val2", "sub"]
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("opt", arity=(1, 3)),
            ],
            subcommands=[
                CommandSpec("sub"),
            ],
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["opt"].value == ("val1", "val2")
        assert result.subcommand is not None
        assert result.subcommand.command == "sub"

    def test_options_per_subcommand(self):
        """Each subcommand can have its own options."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("opt")],
            subcommands=[
                CommandSpec(
                    name="sub",
                    options=[OptionSpec("opt")],
                ),
            ],
        )
        args = ["--opt", "foo", "sub", "--opt", "bar"]
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["opt"].value == "foo"
        assert result.subcommand is not None
        assert result.subcommand.command == "sub"
        assert result.subcommand.options["opt"].value == "bar"

    def test_subcommand_only_option(self):
        """Subcommand can have options not in parent."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="build",
                    options=[
                        OptionSpec("threads", short=["t"], arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["build", "--threads", "4"])
        assert result.subcommand is not None
        assert result.subcommand.command == "build"
        assert result.subcommand.options["threads"].value == "4"

    def test_parent_options_before_subcommand(self):
        """Parent options can appear before subcommand."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("verbose", short=["v"], arity=ZERO_ARITY)],
            subcommands=[
                CommandSpec(
                    name="start",
                    options=[OptionSpec("force", short=["f"], arity=ZERO_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-v", "start", "-f"])
        assert result.options["verbose"].value is True
        assert result.subcommand is not None
        assert result.subcommand.command == "start"
        assert result.subcommand.options["force"].value is True

    def test_subcommand_option_isolation(self):
        """Subcommand options don't leak to parent."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("verbose", short=["v"], arity=ZERO_ARITY)],
            subcommands=[
                CommandSpec(
                    name="start",
                    options=[OptionSpec("force", short=["f"], arity=ZERO_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["start", "-f"])
        assert "verbose" not in result.options
        assert result.subcommand is not None
        assert result.subcommand.options["force"].value is True


class TestSubcommandPositionals:
    """Test subcommand-specific positional arguments."""

    def test_subcommand_with_positionals(self):
        """Subcommands can have positional arguments."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="add",
                    positionals=[PositionalSpec("files", arity=ONE_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["add", "file1.txt", "file2.txt"])
        assert result.subcommand is not None
        assert result.subcommand.command == "add"
        assert result.subcommand.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
        )

    def test_parent_and_subcommand_positionals(self):
        """Both parent and subcommand can have positionals."""
        spec = CommandSpec(
            name="cmd",
            positionals=[PositionalSpec("config", arity=EXACTLY_ONE_ARITY)],
            subcommands=[
                CommandSpec(
                    name="process",
                    positionals=[PositionalSpec("files", arity=ONE_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["config.yml", "process", "file1.txt", "file2.txt"])
        assert result.positionals["config"].value == "config.yml"
        assert result.subcommand is not None
        assert result.subcommand.command == "process"
        assert result.subcommand.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
        )

    def test_subcommand_optional_positionals(self):
        """Subcommands can have optional positionals."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="list",
                    positionals=[PositionalSpec("pattern", arity=ZERO_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result1 = parser.parse(["list"])
        assert result1.subcommand is not None
        assert result1.subcommand.positionals["pattern"].value == ()

        result2 = parser.parse(["list", "*.txt"])
        assert result2.subcommand is not None
        assert result2.subcommand.positionals["pattern"].value == ("*.txt",)


class TestNestedSubcommands:
    """Test nested subcommand hierarchies."""

    def test_two_level_nesting(self):
        """Two levels of subcommands work."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="remote",
                    subcommands=[
                        CommandSpec(name="add"),
                        CommandSpec(name="remove"),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["remote", "add"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remote"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "add"

    def test_three_level_nesting(self):
        """Three levels of subcommands work."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="level1",
                    subcommands=[
                        CommandSpec(
                            name="level2",
                            subcommands=[
                                CommandSpec(name="level3"),
                            ],
                        ),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["level1", "level2", "level3"])
        assert result.subcommand is not None
        assert result.subcommand.command == "level1"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "level2"
        assert result.subcommand.subcommand.subcommand is not None
        assert result.subcommand.subcommand.subcommand.command == "level3"

    def test_nested_subcommand_with_options(self):
        """Nested subcommands can have options at each level."""
        spec = CommandSpec(
            name="cmd",
            options=[OptionSpec("verbose", short=["v"], arity=ZERO_ARITY)],
            subcommands=[
                CommandSpec(
                    name="remote",
                    options=[OptionSpec("all", short=["a"], arity=ZERO_ARITY)],
                    subcommands=[
                        CommandSpec(
                            name="add",
                            options=[
                                OptionSpec("fetch", short=["f"], arity=ZERO_ARITY)
                            ],
                        ),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-v", "remote", "-a", "add", "-f"])
        assert result.options["verbose"].value is True
        assert result.subcommand is not None
        assert result.subcommand.command == "remote"
        assert result.subcommand.options["all"].value is True
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "add"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.options["fetch"].value is True

    def test_nested_subcommand_with_positionals(self):
        """Nested subcommands can have positionals at each level."""
        spec = CommandSpec(
            name="cmd",
            positionals=[PositionalSpec("repo", arity=EXACTLY_ONE_ARITY)],
            subcommands=[
                CommandSpec(
                    name="branch",
                    positionals=[PositionalSpec("name", arity=ZERO_OR_MORE_ARITY)],
                    subcommands=[
                        CommandSpec(
                            name="delete",
                            positionals=[
                                PositionalSpec("branches", arity=ONE_OR_MORE_ARITY)
                            ],
                        ),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["myrepo", "branch", "delete", "feature1", "feature2"])
        assert result.positionals["repo"].value == "myrepo"
        assert result.subcommand is not None
        assert result.subcommand.command == "branch"
        assert result.subcommand.positionals["name"].value == ()
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "delete"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.positionals["branches"].value == (
            "feature1",
            "feature2",
        )


class TestSubcommandAliases:
    """Test subcommand alias functionality."""

    def test_single_alias(self):
        """Single alias works."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[CommandSpec(name="remove", aliases=("rm",))],
        )
        parser = Parser(spec, allow_aliases=True)

        result = parser.parse(["rm"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remove"
        assert result.subcommand.alias == "rm"

    def test_multiple_aliases(self):
        """Multiple aliases work."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="remove",
                    aliases=(
                        "rm",
                        "del",
                        "delete",
                    ),
                )
            ],
        )
        parser = Parser(spec, allow_aliases=True)

        for alias in ["rm", "del", "delete"]:
            result = parser.parse([alias])
            assert result.subcommand is not None
            assert result.subcommand.command == "remove"
            assert result.subcommand.alias == alias

    def test_alias_vs_primary_name(self):
        """Both alias and primary name work."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[CommandSpec(name="remove", aliases=("rm",))],
        )
        parser = Parser(spec, allow_aliases=True)

        result1 = parser.parse(["remove"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "remove"
        assert result1.subcommand.alias is None

        result2 = parser.parse(["rm"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "remove"
        assert result2.subcommand.alias == "rm"

    def test_nested_subcommand_aliases(self):
        """Aliases work for nested subcommands."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="remote",
                    aliases=("r",),
                    subcommands=[
                        CommandSpec(name="add", aliases=("a",)),
                    ],
                ),
            ],
        )
        parser = Parser(spec, allow_aliases=True)

        result = parser.parse(["r", "a"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remote"
        assert result.subcommand.alias == "r"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "add"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.alias == "a"


class TestSubcommandAbbreviations:
    """Test subcommand abbreviation functionality."""

    def test_unambiguous_abbreviation(self):
        """Unambiguous abbreviations work."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(name="start"),
                CommandSpec(name="remove"),
            ],
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        result1 = parser.parse(["sta"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "start"

        result2 = parser.parse(["rem"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "remove"

    def test_ambiguous_abbreviation(self):
        """Ambiguous abbreviations raise error."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(name="start"),
                CommandSpec(name="stop"),
                CommandSpec(name="status"),
            ],
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        with pytest.raises(AmbiguousSubcommandError) as exc_info:
            _ = parser.parse(["sta"])

        message = str(exc_info.value).lower()
        assert "sta" in message

    def test_abbreviation_with_aliases(self):
        """Abbreviations work with aliases."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="remove",
                    aliases=(
                        "rm",
                        "delete",
                    ),
                )
            ],
        )
        parser = Parser(
            spec,
            allow_abbreviated_subcommands=True,
            allow_aliases=True,
        )

        # Can abbreviate primary name
        result1 = parser.parse(["rem"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "remove"

        # Can abbreviate alias
        result2 = parser.parse(["del"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "remove"

    def test_nested_subcommand_abbreviations(self):
        """Abbreviations work at all nesting levels."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[
                CommandSpec(
                    name="remote",
                    subcommands=[
                        CommandSpec(name="add"),
                        CommandSpec(name="remove"),
                    ],
                ),
            ],
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        result = parser.parse(["rem", "add"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remote"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "add"


class TestSubcommandCaseInsensitive:
    """Test case-insensitive subcommand matching."""

    def test_case_insensitive_matching(self):
        """Case-insensitive matching works."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[CommandSpec(name="start")],
        )
        parser = Parser(spec, case_insensitive_subcommands=True)

        result = parser.parse(["START"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_case_insensitive_with_aliases(self):
        """Case-insensitive matching works with aliases."""
        spec = CommandSpec(
            name="cmd",
            subcommands=[CommandSpec(name="remove", aliases=("rm",))],
        )
        parser = Parser(
            spec,
            allow_aliases=True,
            case_insensitive_subcommands=True,
        )

        result1 = parser.parse(["REMOVE"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "remove"

        result2 = parser.parse(["RM"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "remove"


class TestComplexSubcommandScenarios:
    """Test complex combinations of subcommand features."""

    def test_git_like_cli(self):
        """Git-like command structure works."""
        spec = CommandSpec(
            name="git",
            options=[OptionSpec("verbose", short=["v"], arity=ZERO_ARITY)],
            subcommands=[
                CommandSpec(
                    name="commit",
                    options=[
                        OptionSpec("message", short=["m"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("all", short=["a"], arity=ZERO_ARITY),
                    ],
                ),
                CommandSpec(
                    name="branch",
                    positionals=[PositionalSpec("name", arity=ZERO_OR_MORE_ARITY)],
                ),
                CommandSpec(
                    name="remote",
                    subcommands=[
                        CommandSpec(
                            name="add",
                            positionals=[
                                PositionalSpec("name", arity=EXACTLY_ONE_ARITY),
                                PositionalSpec("url", arity=EXACTLY_ONE_ARITY),
                            ],
                        ),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        # git commit -am "message"
        result1 = parser.parse(["commit", "-a", "-m", "Initial commit"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "commit"
        assert result1.subcommand.options["all"].value is True
        assert result1.subcommand.options["message"].value == "Initial commit"

        # git branch feature
        result2 = parser.parse(["branch", "feature"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "branch"
        assert result2.subcommand.positionals["name"].value == ("feature",)

        # git remote add origin url
        result3 = parser.parse(["remote", "add", "origin", "https://example.com"])
        assert result3.subcommand is not None
        assert result3.subcommand.command == "remote"
        assert result3.subcommand.subcommand is not None
        assert result3.subcommand.subcommand.command == "add"
        assert result3.subcommand.subcommand is not None
        assert result3.subcommand.subcommand.positionals["name"].value == "origin"
        assert (
            result3.subcommand.subcommand.positionals["url"].value
            == "https://example.com"
        )

    def test_docker_like_cli(self):
        """Docker-like command structure works."""
        spec = CommandSpec(
            name="docker",
            subcommands=[
                CommandSpec(
                    name="run",
                    options=[
                        OptionSpec("interactive", short=["i"], arity=ZERO_ARITY),
                        OptionSpec("tty", short=["t"], arity=ZERO_ARITY),
                        OptionSpec("rm", arity=ZERO_ARITY),
                    ],
                    positionals=[
                        PositionalSpec("image", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                    ],
                ),
                CommandSpec(
                    name="ps",
                    options=[OptionSpec("all", short=["a"], arity=ZERO_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        # docker run -it --rm ubuntu bash
        result = parser.parse(["run", "-i", "-t", "--rm", "ubuntu", "bash"])
        assert result.subcommand is not None
        assert result.subcommand.command == "run"
        assert result.subcommand.options["interactive"].value is True
        assert result.subcommand.options["tty"].value is True
        assert result.subcommand.options["rm"].value is True
        assert result.subcommand.positionals["image"].value == "ubuntu"
        assert result.subcommand.positionals["command"].value == ("bash",)
