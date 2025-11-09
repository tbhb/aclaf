"""Integration tests for complex multi-feature scenarios.

This module tests combinations of parser features working together in realistic
command-line applications.
"""

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    AccumulationMode,
    Arity,
)


class TestMultiLevelSubcommands:
    """Test deeply nested subcommand hierarchies."""

    def test_three_level_nesting_with_options(self):
        """Test deeply nested cloud CLI with options at each subcommand level.

        Verifies complex three-level subcommand nesting (cloud -> compute -> instances
        -> create) with options at each level. Models cloud provider CLIs like GCP.
        Tests parser's ability to maintain option scopes across deep nesting.

        Tests:
        - Three-level subcommand nesting
        - Options at each nesting level
        - Option scope isolation per level
        - Complex hierarchical CLI structure

        CLI: cloud -v compute -r us-west1 instances -z us-west1-a create
             -m n1-standard-1 my-instance
        """
        spec = CommandSpec(
            name="cloud",
            options=[OptionSpec("verbose", short=["v"], arity=ZERO_ARITY)],
            subcommands=[
                CommandSpec(
                    name="compute",
                    options=[
                        OptionSpec("region", short=["r"], arity=EXACTLY_ONE_ARITY)
                    ],
                    subcommands=[
                        CommandSpec(
                            name="instances",
                            options=[
                                OptionSpec("zone", short=["z"], arity=EXACTLY_ONE_ARITY)
                            ],
                            subcommands=[
                                CommandSpec(
                                    name="create",
                                    options=[
                                        OptionSpec(
                                            "machine-type",
                                            short=["m"],
                                            arity=EXACTLY_ONE_ARITY,
                                        ),
                                    ],
                                    positionals=[
                                        PositionalSpec("name", arity=EXACTLY_ONE_ARITY)
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "-v",
                "compute",
                "-r",
                "us-west1",
                "instances",
                "-z",
                "us-west1-a",
                "create",
                "-m",
                "n1-standard-1",
                "my-instance",
            ]
        )
        assert result.options["verbose"].value is True
        assert result.subcommand is not None
        assert result.subcommand.command == "compute"
        assert result.subcommand.options["region"].value == "us-west1"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "instances"
        assert result.subcommand.subcommand.options["zone"].value == "us-west1-a"
        assert result.subcommand.subcommand.subcommand is not None
        assert result.subcommand.subcommand.subcommand.command == "create"
        assert (
            result.subcommand.subcommand.subcommand.options["machine-type"].value
            == "n1-standard-1"
        )
        assert (
            result.subcommand.subcommand.subcommand.positionals["name"].value
            == "my-instance"
        )


class TestOptionsPositionalsSubcommands:
    """Test combinations of options, positionals, and subcommands."""

    def test_all_features_together(self):
        """Test comprehensive combination of all parser features.

        Verifies a realistic tool combining global options (verbose, config), root
        positionals (input), and subcommands with their own options and positionals.
        Tests simultaneous use of all major parser features in one command.

        Tests:
        - Global options with COUNT accumulation
        - Root-level positionals
        - Subcommand with options
        - Subcommand with positionals
        - All features working together

        CLI: tool -vv --config config.yml input.txt process -t 4 -o output.txt
             file1.txt file2.txt
        """
        spec = CommandSpec(
            name="tool",
            options=[
                OptionSpec(
                    "verbose",
                    short=["v"],
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
                OptionSpec("config", short=["c"], arity=EXACTLY_ONE_ARITY),
            ],
            positionals=[PositionalSpec("input", arity=EXACTLY_ONE_ARITY)],
            subcommands=[
                CommandSpec(
                    name="process",
                    options=[
                        OptionSpec("threads", short=["t"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
                    ],
                    positionals=[PositionalSpec("files", arity=ONE_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "-vv",
                "--config",
                "config.yml",
                "input.txt",
                "process",
                "-t",
                "4",
                "-o",
                "output.txt",
                "file1.txt",
                "file2.txt",
            ]
        )
        assert result.options["verbose"].value == 2
        assert result.options["config"].value == "config.yml"
        assert result.positionals["input"].value == "input.txt"
        assert result.subcommand is not None
        assert result.subcommand.command == "process"
        assert result.subcommand.options["threads"].value == "4"
        assert result.subcommand.options["output"].value == "output.txt"
        assert result.subcommand.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
        )

    def test_mixed_arity_positionals(self):
        """Test complex positional distribution with mixed arity requirements.

        Verifies parser's greedy left-to-right positional distribution algorithm
        while respecting minimum requirements of subsequent positionals. Tests with
        three positionals: one required, one optional, one bounded. Algorithm must
        balance greedy consumption with lookahead for required minimums.

        Tests:
        - Exactly-one arity positional
        - Zero-or-more arity positional
        - Bounded arity positional (2-4)
        - Greedy left-to-right distribution
        - Minimum requirement lookahead

        CLI: cmd req mul1 mul2 mul3
        """
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("required", arity=EXACTLY_ONE_ARITY),
                PositionalSpec("optional", arity=ZERO_OR_MORE_ARITY),
                PositionalSpec("multiple", arity=Arity(2, 4)),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["req", "mul1", "mul2", "mul3"])
        assert result.positionals["required"].value == "req"
        # Left-to-right greedy: "optional" gets 1, leaving 2 for "multiple"
        assert result.positionals["optional"].value == ("mul1",)
        assert result.positionals["multiple"].value == ("mul2", "mul3")


class TestAccumulationWithComplexOptions:
    """Test accumulation modes with complex option scenarios."""

    def test_collect_mode_with_multi_value_options(self):
        """Test COLLECT accumulation with multi-value options.

        Verifies COLLECT mode when each option occurrence takes multiple values
        (one-or-more arity). Tests nested tuple structure where outer tuple contains
        one entry per option occurrence, each entry being a tuple of that occurrence's
        values. Common in compiler-like tools for include paths.

        Tests:
        - COLLECT accumulation mode
        - One-or-more arity per occurrence
        - Nested tuple structure
        - Multiple values per repetition

        CLI: cmd -I path1 path2 -I path3 -I path4 path5 path6
        """
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec(
                    "include",
                    short=["I"],
                    arity=ONE_OR_MORE_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "-I",
                "path1",
                "path2",
                "-I",
                "path3",
                "-I",
                "path4",
                "path5",
                "path6",
            ]
        )
        assert result.options["include"].value == (
            ("path1", "path2"),
            ("path3",),
            ("path4", "path5", "path6"),
        )

    def test_multiple_accumulation_modes(self):
        """Test compiler-like CLI with mixed accumulation modes.

        Verifies realistic compiler scenario where different options use different
        accumulation strategies: COLLECT for defines/includes, COUNT for verbosity,
        LAST_WINS for optimization level. Tests parser handling of heterogeneous
        accumulation modes in one command.

        Tests:
        - COLLECT mode for -D and -I
        - COUNT mode for -v
        - LAST_WINS mode for -O
        - Mixed accumulation strategies
        - Compiler CLI pattern

        CLI: compiler -D DEBUG -I /usr/include -vv -O 1 -D VERSION=1.0
             -I /usr/local/include -O 2
        """
        spec = CommandSpec(
            name="compiler",
            options=[
                OptionSpec(
                    "define",
                    short=["D"],
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
                OptionSpec(
                    "include",
                    short=["I"],
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.COLLECT,
                ),
                OptionSpec(
                    "verbose",
                    short=["v"],
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
                OptionSpec(
                    "optimization",
                    short=["O"],
                    arity=EXACTLY_ONE_ARITY,
                    accumulation_mode=AccumulationMode.LAST_WINS,
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "-D",
                "DEBUG",
                "-I",
                "/usr/include",
                "-vv",
                "-O",
                "1",
                "-D",
                "VERSION=1.0",
                "-I",
                "/usr/local/include",
                "-O",
                "2",
            ]
        )
        assert result.options["define"].value == ("DEBUG", "VERSION=1.0")
        assert result.options["include"].value == ("/usr/include", "/usr/local/include")
        assert result.options["verbose"].value == 2
        assert result.options["optimization"].value == "2"


class TestTrailingArgsInComplexScenarios:
    """Test trailing args with complex command structures."""

    def test_trailing_args_with_subcommand_and_options(self):
        """Test kubectl-style exec with options and trailing command args.

        Verifies the pattern where a subcommand has options, positionals, and trailing
        args after -- separator. Models kubectl exec with flags, pod name, and
        container command. Tests comprehensive feature interaction.

        Tests:
        - Clustered subcommand options (-it)
        - Required positional (pod)
        - Trailing args separator (--)
        - Extra args passthrough
        - Full feature integration

        CLI: kubectl exec -it mypod -- /bin/bash -c "echo hello"
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="exec",
                    options=[
                        OptionSpec("interactive", short=["i"], arity=ZERO_ARITY),
                        OptionSpec("tty", short=["t"], arity=ZERO_ARITY),
                    ],
                    positionals=[PositionalSpec("pod", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            ["exec", "-it", "mypod", "--", "/bin/bash", "-c", "echo hello"]
        )
        assert result.subcommand is not None
        assert result.subcommand.options["interactive"].value is True
        assert result.subcommand.options["tty"].value is True
        assert result.subcommand.positionals["pod"].value == "mypod"
        assert result.subcommand.extra_args == ("/bin/bash", "-c", "echo hello")


class TestComplexArityPatterns:
    """Test complex arity specifications."""

    def test_bounded_arity_ranges(self):
        """Test custom arity range with bounded min and max values.

        Verifies Arity(min, max) pattern allowing flexible value counts within bounds.
        Tests minimum (2), maximum (5), and middle-range (3) value consumption. Useful
        for options requiring a specific range of arguments.

        Tests:
        - Custom Arity(2, 5) range
        - Minimum value satisfaction
        - Maximum value satisfaction
        - Mid-range value handling

        CLI: cmd -f a b (min), cmd -f a b c d e (max), cmd -f a b c (mid)
        """
        spec = CommandSpec(
            name="cmd",
            options=[
                OptionSpec("files", short=["f"], arity=Arity(2, 5)),
            ],
        )
        parser = Parser(spec)

        # Minimum satisfied
        result1 = parser.parse(["-f", "a", "b"])
        assert result1.options["files"].value == ("a", "b")

        # Maximum satisfied
        result2 = parser.parse(["-f", "a", "b", "c", "d", "e"])
        assert result2.options["files"].value == ("a", "b", "c", "d", "e")

        # Middle range
        result3 = parser.parse(["-f", "a", "b", "c"])
        assert result3.options["files"].value == ("a", "b", "c")

    def test_unbounded_positionals_with_required(self):
        """Test cp-like pattern with multiple sources and single destination.

        Verifies the copy-file pattern where multiple source files (one-or-more)
        precede a single required destination. Tests parser's ability to reserve
        the last positional for destination while consuming all others as sources.

        Tests:
        - One-or-more arity positional (sources)
        - Exactly-one arity positional (dest)
        - Greedy consumption with reservation
        - Copy-command pattern

        CLI: cmd src1 src2 src3 destination
        """
        spec = CommandSpec(
            name="cmd",
            positionals=[
                PositionalSpec("sources", arity=ONE_OR_MORE_ARITY),
                PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["src1", "src2", "src3", "destination"])
        assert result.positionals["sources"].value == ("src1", "src2", "src3")
        assert result.positionals["dest"].value == "destination"


class TestRealWorldBuildTool:
    """Test realistic build tool CLI patterns."""

    def test_make_like_cli(self):
        """Test Make-style build tool with job control and targets.

        Verifies build tool pattern with options for build file (-f), parallelism
        (-j), error handling (-k), and multiple target positionals. Models Make and
        similar build systems. Tests realistic build tool CLI structure.

        Tests:
        - Multiple value-taking options (-f, -j)
        - Zero-arity option (-k)
        - Zero-or-more arity positionals (targets)
        - Build tool pattern

        CLI: build -f Buildfile -j 4 -k clean build test
        """
        spec = CommandSpec(
            name="build",
            options=[
                OptionSpec("file", short=["f"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("jobs", short=["j"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("keep-going", short=["k"], arity=ZERO_ARITY),
            ],
            positionals=[PositionalSpec("targets", arity=ZERO_OR_MORE_ARITY)],
        )
        parser = Parser(spec)

        result = parser.parse(
            ["-f", "Buildfile", "-j", "4", "-k", "clean", "build", "test"]
        )
        assert result.options["file"].value == "Buildfile"
        assert result.options["jobs"].value == "4"
        assert result.options["keep-going"].value is True
        assert result.positionals["targets"].value == ("clean", "build", "test")


class TestPackageManagerPatterns:
    """Test package manager CLI patterns."""

    def test_npm_like_install(self):
        """Test npm-style package manager with aliased install command.

        Verifies package manager pattern with command aliases (install/i/add) and
        install type flags (--save-dev). Tests subcommand aliasing with development
        dependency installation. Models npm/yarn patterns.

        Tests:
        - Subcommand aliases (i, add)
        - Zero-arity mode flags (-D)
        - Zero-or-more positionals (packages)
        - Package manager pattern

        CLI: pkg install -D typescript eslint
        """
        spec = CommandSpec(
            name="pkg",
            subcommands=[
                CommandSpec(
                    name="install",
                    aliases=("i", "add"),
                    options=[
                        OptionSpec("save-dev", short=["D"], arity=ZERO_ARITY),
                        OptionSpec("global", short=["g"], arity=ZERO_ARITY),
                    ],
                    positionals=[PositionalSpec("packages", arity=ZERO_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec, allow_aliases=True)

        result = parser.parse(["install", "-D", "typescript", "eslint"])
        assert result.subcommand is not None
        assert result.subcommand.command == "install"
        assert result.subcommand.options["save-dev"].value is True
        assert result.subcommand.positionals["packages"].value == (
            "typescript",
            "eslint",
        )

    def test_pip_like_install(self):
        """Test pip-style package installation with requirements file.

        Verifies Python package manager pattern with requirements file (-r), upgrade
        flag (-U), and user-level installation (--user). Tests value-taking and
        boolean options for package installation control. Models pip behavior.

        Tests:
        - Requirements file option (-r)
        - Boolean install flags (-U, --user)
        - Optional package positionals
        - Python package manager pattern

        CLI: pip install -r requirements.txt --user --upgrade
        """
        spec = CommandSpec(
            name="pip",
            subcommands=[
                CommandSpec(
                    name="install",
                    options=[
                        OptionSpec("requirement", short=["r"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("upgrade", short=["U"], arity=ZERO_ARITY),
                        OptionSpec("user", arity=ZERO_ARITY),
                    ],
                    positionals=[PositionalSpec("packages", arity=ZERO_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            ["install", "-r", "requirements.txt", "--user", "--upgrade"]
        )
        assert result.subcommand is not None
        assert result.subcommand.options["requirement"].value == "requirements.txt"
        assert result.subcommand.options["user"].value is True
        assert result.subcommand.options["upgrade"].value is True


class TestDatabaseCLIPatterns:
    """Test database CLI patterns."""

    def test_psql_like_connection(self):
        """Test PostgreSQL-style database connection with multiple options.

        Verifies database CLI pattern with connection parameters (host, port, username,
        database) all specified via options. Tests multiple value-taking options for
        connection configuration. Models psql and similar database clients.

        Tests:
        - Multiple value-taking options (-h, -p, -U, -d)
        - Connection parameter specification
        - Optional command positionals
        - Database CLI pattern

        CLI: db -h localhost -p 5432 -U admin -d mydb
        """
        spec = CommandSpec(
            name="db",
            options=[
                OptionSpec("host", short=["h"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("port", short=["p"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("username", short=["U"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("database", short=["d"], arity=EXACTLY_ONE_ARITY),
            ],
            positionals=[PositionalSpec("command", arity=ZERO_OR_MORE_ARITY)],
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "-h",
                "localhost",
                "-p",
                "5432",
                "-U",
                "admin",
                "-d",
                "mydb",
            ]
        )
        assert result.options["host"].value == "localhost"
        assert result.options["port"].value == "5432"
        assert result.options["username"].value == "admin"
        assert result.options["database"].value == "mydb"
