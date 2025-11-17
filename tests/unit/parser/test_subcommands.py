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
    Arity,
)


class TestBasicSubcommands:
    def test_resolves_exact_match(self):
        args = ["foo"]
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "foo": CommandSpec("foo"),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.subcommand is not None
        assert result.subcommand.command == "foo"

    def test_recognizes_multiple_subcommands(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "stop": CommandSpec(name="stop"),
                "status": CommandSpec(name="status"),
            },
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
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec)

        result = parser.parse([])
        assert result.subcommand is None

    def test_unknown_subcommand_raises_error(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec)

        with pytest.raises(UnknownSubcommandError):
            _ = parser.parse(["unknown"])

    def test_result_includes_name_and_alias_info(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec)

        result = parser.parse(["start"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"
        assert result.subcommand.alias is None


class TestSubcommandOptions:
    def test_option_with_multiple_arity_and_subcommand(self):
        args = ["--opt", "val1", "val2", "sub"]
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec("opt", arity=Arity(1, 3)),
            },
            subcommands={
                "sub": CommandSpec("sub"),
            },
        )
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["opt"].value == ("val1", "val2")
        assert result.subcommand is not None
        assert result.subcommand.command == "sub"

    def test_options_per_subcommand(self):
        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt")},
            subcommands={
                "sub": CommandSpec(
                    name="sub",
                    options={"opt": OptionSpec("opt")},
                ),
            },
        )
        args = ["--opt", "foo", "sub", "--opt", "bar"]
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.options["opt"].value == "foo"
        assert result.subcommand is not None
        assert result.subcommand.command == "sub"
        assert result.subcommand.options["opt"].value == "bar"

    def test_subcommand_only_option(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "build": CommandSpec(
                    name="build",
                    options={
                        "threads": OptionSpec(
                            "threads", short=frozenset({"t"}), arity=EXACTLY_ONE_ARITY
                        )
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["build", "--threads", "4"])
        assert result.subcommand is not None
        assert result.subcommand.command == "build"
        assert result.subcommand.options["threads"].value == "4"

    def test_parent_options_before_subcommand(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            subcommands={
                "start": CommandSpec(
                    name="start",
                    options={
                        "force": OptionSpec(
                            "force", short=frozenset({"f"}), arity=ZERO_ARITY
                        )
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["-v", "start", "-f"])
        assert result.options["verbose"].value is True
        assert result.subcommand is not None
        assert result.subcommand.command == "start"
        assert result.subcommand.options["force"].value is True

    def test_subcommand_option_isolation(self):
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            subcommands={
                "start": CommandSpec(
                    name="start",
                    options={
                        "force": OptionSpec(
                            "force", short=frozenset({"f"}), arity=ZERO_ARITY
                        )
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["start", "-f"])
        assert "verbose" not in result.options
        assert result.subcommand is not None
        assert result.subcommand.options["force"].value is True


class TestSubcommandPositionals:
    def test_subcommand_with_positionals(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "add": CommandSpec(
                    name="add",
                    positionals={
                        "files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)
                    },
                ),
            },
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
        spec = CommandSpec(
            name="cmd",
            positionals={"config": PositionalSpec("config", arity=EXACTLY_ONE_ARITY)},
            subcommands={
                "process": CommandSpec(
                    name="process",
                    positionals={
                        "files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)
                    },
                ),
            },
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
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "list": CommandSpec(
                    name="list",
                    positionals={
                        "pattern": PositionalSpec("pattern", arity=ZERO_OR_MORE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result1 = parser.parse(["list"])
        assert result1.subcommand is not None
        assert result1.subcommand.positionals["pattern"].value == ()

        result2 = parser.parse(["list", "*.txt"])
        assert result2.subcommand is not None
        assert result2.subcommand.positionals["pattern"].value == ("*.txt",)


class TestNestedSubcommands:
    def test_two_level_nesting(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remote": CommandSpec(
                    name="remote",
                    subcommands={
                        "add": CommandSpec(name="add"),
                        "remove": CommandSpec(name="remove"),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["remote", "add"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remote"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "add"

    def test_three_level_nesting(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "level1": CommandSpec(
                    name="level1",
                    subcommands={
                        "level2": CommandSpec(
                            name="level2",
                            subcommands={
                                "level3": CommandSpec(name="level3"),
                            },
                        ),
                    },
                ),
            },
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
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            subcommands={
                "remote": CommandSpec(
                    name="remote",
                    options={
                        "all": OptionSpec(
                            "all", short=frozenset({"a"}), arity=ZERO_ARITY
                        )
                    },
                    subcommands={
                        "add": CommandSpec(
                            name="add",
                            options={
                                "fetch": OptionSpec(
                                    "fetch", short=frozenset({"f"}), arity=ZERO_ARITY
                                )
                            },
                        ),
                    },
                ),
            },
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
        spec = CommandSpec(
            name="cmd",
            positionals={"repo": PositionalSpec("repo", arity=EXACTLY_ONE_ARITY)},
            subcommands={
                "branch": CommandSpec(
                    name="branch",
                    positionals={
                        "name": PositionalSpec("name", arity=ZERO_OR_MORE_ARITY)
                    },
                    subcommands={
                        "delete": CommandSpec(
                            name="delete",
                            positionals={
                                "branches": PositionalSpec(
                                    "branches", arity=ONE_OR_MORE_ARITY
                                )
                            },
                        ),
                    },
                ),
            },
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
    def test_single_alias(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(spec, allow_aliases=True)

        result = parser.parse(["rm"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remove"
        assert result.subcommand.alias == "rm"

    def test_multiple_aliases(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(
                    name="remove",
                    aliases=frozenset({"rm", "del", "delete"}),
                )
            },
        )
        parser = Parser(spec, allow_aliases=True)

        for alias in ["rm", "del", "delete"]:
            result = parser.parse([alias])
            assert result.subcommand is not None
            assert result.subcommand.command == "remove"
            assert result.subcommand.alias == alias

    def test_alias_vs_primary_name(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
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
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remote": CommandSpec(
                    name="remote",
                    aliases=frozenset({"r"}),
                    subcommands={
                        "add": CommandSpec(name="add", aliases=frozenset({"a"})),
                    },
                ),
            },
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

    def test_alias_disabled(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(spec, allow_aliases=False)

        with pytest.raises(UnknownSubcommandError):
            _ = parser.parse(["rm"])

    def test_primary_name_always_works(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
        )
        parser = Parser(spec, allow_aliases=False)

        result = parser.parse(["remove"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remove"


class TestSubcommandAbbreviations:
    def test_unambiguous_abbreviation(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "remove": CommandSpec(name="remove"),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        result1 = parser.parse(["sta"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "start"

        result2 = parser.parse(["rem"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "remove"

    def test_ambiguous_abbreviation(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "start": CommandSpec(name="start"),
                "stop": CommandSpec(name="stop"),
                "status": CommandSpec(name="status"),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        with pytest.raises(AmbiguousSubcommandError) as exc_info:
            _ = parser.parse(["sta"])

        message = str(exc_info.value).lower()
        assert "sta" in message

    def test_abbreviation_with_aliases(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(
                    name="remove",
                    aliases=frozenset({"rm", "delete"}),
                )
            },
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
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remote": CommandSpec(
                    name="remote",
                    subcommands={
                        "add": CommandSpec(name="add"),
                        "remove": CommandSpec(name="remove"),
                    },
                ),
            },
        )
        parser = Parser(spec, allow_abbreviated_subcommands=True)

        result = parser.parse(["rem", "add"])
        assert result.subcommand is not None
        assert result.subcommand.command == "remote"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "add"

    def test_minimum_abbreviation_length(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(
            spec,
            allow_abbreviated_subcommands=True,
            minimum_abbreviation_length=3,
        )

        # 3 chars works
        result = parser.parse(["sta"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

        # 2 chars fails
        with pytest.raises(UnknownSubcommandError):
            _ = parser.parse(["st"])


class TestSubcommandCaseInsensitive:
    def test_case_insensitive_matching(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=True)

        result = parser.parse(["START"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"

    def test_case_insensitive_with_aliases(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={
                "remove": CommandSpec(name="remove", aliases=frozenset({"rm"}))
            },
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

    def test_case_insensitive_mixed_case(self):
        spec = CommandSpec(
            name="cmd",
            subcommands={"start": CommandSpec(name="start")},
        )
        parser = Parser(spec, case_insensitive_subcommands=True)

        result = parser.parse(["StArT"])
        assert result.subcommand is not None
        assert result.subcommand.command == "start"


class TestComplexSubcommandScenarios:
    def test_git_like_cli(self):
        spec = CommandSpec(
            name="git",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            subcommands={
                "commit": CommandSpec(
                    name="commit",
                    options={
                        "message": OptionSpec(
                            "message", short=frozenset({"m"}), arity=EXACTLY_ONE_ARITY
                        ),
                        "all": OptionSpec(
                            "all", short=frozenset({"a"}), arity=ZERO_ARITY
                        ),
                    },
                ),
                "branch": CommandSpec(
                    name="branch",
                    positionals={
                        "name": PositionalSpec("name", arity=ZERO_OR_MORE_ARITY)
                    },
                ),
                "remote": CommandSpec(
                    name="remote",
                    subcommands={
                        "add": CommandSpec(
                            name="add",
                            positionals={
                                "name": PositionalSpec("name", arity=EXACTLY_ONE_ARITY),
                                "url": PositionalSpec("url", arity=EXACTLY_ONE_ARITY),
                            },
                        ),
                    },
                ),
            },
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
        spec = CommandSpec(
            name="docker",
            subcommands={
                "run": CommandSpec(
                    name="run",
                    options={
                        "interactive": OptionSpec(
                            "interactive", short=frozenset({"i"}), arity=ZERO_ARITY
                        ),
                        "tty": OptionSpec(
                            "tty", short=frozenset({"t"}), arity=ZERO_ARITY
                        ),
                        "rm": OptionSpec("rm", arity=ZERO_ARITY),
                    },
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY),
                        "command": PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                    },
                ),
                "ps": CommandSpec(
                    name="ps",
                    options={
                        "all": OptionSpec(
                            "all", short=frozenset({"a"}), arity=ZERO_ARITY
                        )
                    },
                ),
            },
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
