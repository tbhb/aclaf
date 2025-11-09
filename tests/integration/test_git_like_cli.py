"""Integration tests for Git-like CLI patterns.

This module tests realistic Git-style command structures with nested subcommands,
complex option combinations, and various argument patterns.
"""

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    AccumulationMode,
)


class TestGitCommitCommand:
    """Test Git commit command patterns."""

    def test_commit_with_message(self):
        """Test Git-style commit with short message flag.

        Verifies the common Git pattern where a subcommand accepts a short option
        with a required value. This tests subcommand resolution and option parsing
        within subcommand context.

        Tests:
        - Subcommand resolution ("commit")
        - Short option with required value (-m)
        - Value consumption in subcommand scope

        CLI: git commit -m "Initial commit"
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="commit",
                    options=[
                        OptionSpec("message", short=["m"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("all", short=["a"], arity=ZERO_ARITY),
                        OptionSpec("amend", arity=ZERO_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["commit", "-m", "Initial commit"])
        assert result.subcommand is not None
        assert result.subcommand.command == "commit"
        assert result.subcommand.options["message"].value == "Initial commit"

    def test_commit_combined_flags(self):
        """Test Git-style flag clustering with trailing value option.

        Verifies the POSIX pattern of combining short flags where the last flag
        accepts a value. This is common in Git for "commit all with message" (-am).
        Tests the parser's ability to split clustered flags and correctly bind values.

        Tests:
        - Short option clustering (-am)
        - Zero-arity flag in cluster (-a)
        - Value-taking flag as last in cluster (-m)
        - Value consumption after cluster

        CLI: git commit -am "Update files"
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="commit",
                    options=[
                        OptionSpec("message", short=["m"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("all", short=["a"], arity=ZERO_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["commit", "-am", "Update files"])
        assert result.subcommand is not None
        assert result.subcommand.options["all"].value is True
        assert result.subcommand.options["message"].value == "Update files"

    def test_commit_amend(self):
        """Test Git-style commit amend with mixed long and short options.

        Verifies the pattern of combining long boolean flags (--amend) with short
        value-taking options (-m) in a single subcommand. This tests the parser's
        ability to handle heterogeneous option types together.

        Tests:
        - Long zero-arity option (--amend)
        - Short option with value (-m)
        - Mixed option types in subcommand

        CLI: git commit --amend -m "Updated message"
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="commit",
                    options=[
                        OptionSpec("message", short=["m"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("amend", arity=ZERO_ARITY),
                        OptionSpec("no-edit", arity=ZERO_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["commit", "--amend", "-m", "Updated message"])
        assert result.subcommand is not None
        assert result.subcommand.options["amend"].value is True
        assert result.subcommand.options["message"].value == "Updated message"


class TestGitLogCommand:
    """Test Git log command patterns."""

    def test_log_with_options(self):
        """Test Git log with multiple boolean display flags.

        Verifies the pattern of combining multiple long boolean flags to control
        output formatting. Common in Git for customizing log display. Tests the
        parser's ability to handle multiple independent boolean flags.

        Tests:
        - Multiple long zero-arity options
        - Independent boolean flags
        - Subcommand option parsing

        CLI: git log --oneline --graph --all
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="log",
                    options=[
                        OptionSpec("oneline", arity=ZERO_ARITY),
                        OptionSpec("graph", arity=ZERO_ARITY),
                        OptionSpec("all", arity=ZERO_ARITY),
                        OptionSpec("max-count", short=["n"], arity=EXACTLY_ONE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["log", "--oneline", "--graph", "--all"])
        assert result.subcommand is not None
        assert result.subcommand.options["oneline"].value is True
        assert result.subcommand.options["graph"].value is True
        assert result.subcommand.options["all"].value is True

    def test_log_with_limit(self):
        """Test Git log with numeric limit option.

        Verifies the pattern where a short option takes a numeric value to limit
        output. Common in Git log for restricting the number of commits displayed.
        Tests numeric string value consumption.

        Tests:
        - Short option with numeric value (-n)
        - Value parsing for numeric strings
        - Subcommand option with required value

        CLI: git log -n 10
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="log",
                    options=[
                        OptionSpec("max-count", short=["n"], arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["log", "-n", "10"])
        assert result.subcommand is not None
        assert result.subcommand.options["max-count"].value == "10"


class TestGitBranchCommand:
    """Test Git branch command patterns."""

    def test_branch_list(self):
        """Test Git branch listing with no arguments.

        Verifies the pattern where a subcommand with optional positionals is invoked
        without any arguments, defaulting to list behavior. Tests zero-or-more arity
        positionals receiving no values.

        Tests:
        - Subcommand with no arguments
        - Zero-or-more arity positional
        - Empty positional value handling

        CLI: git branch
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="branch",
                    options=[OptionSpec("all", short=["a"], arity=ZERO_ARITY)],
                    positionals=[PositionalSpec("name", arity=ZERO_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["branch"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["name"].value == ()

    def test_branch_create(self):
        """Test Git branch creation with single positional argument.

        Verifies the pattern where a subcommand with optional positionals receives
        a single value to create a new branch. Tests zero-or-more arity positional
        receiving exactly one value.

        Tests:
        - Single positional argument
        - Zero-or-more arity with one value
        - Branch name as positional

        CLI: git branch feature-xyz
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="branch",
                    positionals=[PositionalSpec("name", arity=ZERO_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["branch", "feature-xyz"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["name"].value == ("feature-xyz",)

    def test_branch_delete(self):
        """Test Git branch deletion with flag and positional.

        Verifies the pattern where a deletion flag modifies the subcommand behavior
        followed by required positional arguments (branch names to delete). Tests
        option-positional interaction in subcommands.

        Tests:
        - Short zero-arity flag (-d)
        - One-or-more arity positional
        - Option-positional ordering

        CLI: git branch -d feature-xyz
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="branch",
                    options=[
                        OptionSpec("delete", short=["d"], arity=ZERO_ARITY),
                        OptionSpec("force-delete", short=["D"], arity=ZERO_ARITY),
                    ],
                    positionals=[PositionalSpec("branches", arity=ONE_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["branch", "-d", "feature-xyz"])
        assert result.subcommand is not None
        assert result.subcommand.options["delete"].value is True
        assert result.subcommand.positionals["branches"].value == ("feature-xyz",)


class TestGitRemoteCommand:
    """Test Git remote command with nested subcommands."""

    def test_remote_add(self):
        """Test Git nested subcommand with multiple required positionals.

        Verifies Git's two-level subcommand structure (remote -> add) with multiple
        required positional arguments for remote name and URL. Tests deep nesting
        and positional argument handling at the deepest level.

        Tests:
        - Two-level subcommand nesting
        - Multiple required positionals (name, url)
        - Exact arity positional matching

        CLI: git remote add origin https://github.com/user/repo.git
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
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
                        CommandSpec(
                            name="remove",
                            aliases=("rm",),
                            positionals=[
                                PositionalSpec("name", arity=EXACTLY_ONE_ARITY)
                            ],
                        ),
                    ],
                ),
            ],
        )
        parser = Parser(spec, allow_aliases=True)

        result = parser.parse(
            ["remote", "add", "origin", "https://github.com/user/repo.git"]
        )
        assert result.subcommand is not None
        assert result.subcommand.command == "remote"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "add"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.positionals["name"].value == "origin"
        assert (
            result.subcommand.subcommand.positionals["url"].value
            == "https://github.com/user/repo.git"
        )

    def test_remote_remove_with_alias(self):
        """Test Git nested subcommand using alias instead of canonical name.

        Verifies Git's pattern of providing short aliases for nested subcommands
        (rm instead of remove). Tests the parser's alias resolution in deeply nested
        command structures and proper tracking of which alias was used.

        Tests:
        - Nested subcommand alias resolution
        - Alias vs canonical name tracking
        - Positional parsing with aliased subcommand

        CLI: git remote rm origin
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="remote",
                    subcommands=[
                        CommandSpec(
                            name="remove",
                            aliases=("rm",),
                            positionals=[
                                PositionalSpec("name", arity=EXACTLY_ONE_ARITY)
                            ],
                        ),
                    ],
                ),
            ],
        )
        parser = Parser(spec, allow_aliases=True)

        result = parser.parse(["remote", "rm", "origin"])
        assert result.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "remove"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.alias == "rm"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.positionals["name"].value == "origin"


class TestGitCheckoutCommand:
    """Test Git checkout command patterns."""

    def test_checkout_branch(self):
        """Test Git checkout with single required positional target.

        Verifies the simple checkout pattern where a branch/commit name is provided
        as a required positional argument. Tests exact arity positional matching
        in subcommands.

        Tests:
        - Subcommand with required positional
        - Exact arity positional (exactly one)
        - Branch name as positional value

        CLI: git checkout main
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="checkout",
                    options=[OptionSpec("branch", short=["b"], arity=ZERO_ARITY)],
                    positionals=[PositionalSpec("target", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["checkout", "main"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["target"].value == "main"

    def test_checkout_create_branch(self):
        """Test Git checkout with create-branch flag and name.

        Verifies the pattern where a flag modifies checkout behavior to create a new
        branch, followed by the required branch name. Common Git workflow for creating
        and switching to new branches. Tests flag-positional interaction.

        Tests:
        - Mode-changing flag (-b)
        - Required positional after flag
        - Subcommand option-positional ordering

        CLI: git checkout -b feature-xyz
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="checkout",
                    options=[OptionSpec("branch", short=["b"], arity=ZERO_ARITY)],
                    positionals=[PositionalSpec("name", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["checkout", "-b", "feature-xyz"])
        assert result.subcommand is not None
        assert result.subcommand.options["branch"].value is True
        assert result.subcommand.positionals["name"].value == "feature-xyz"


class TestGitAddCommand:
    """Test Git add command patterns."""

    def test_add_files(self):
        """Test Git add with multiple file arguments.

        Verifies the pattern where multiple file paths are provided as positional
        arguments to stage for commit. Tests one-or-more arity positional receiving
        multiple values.

        Tests:
        - Multiple positional values
        - One-or-more arity positional
        - File paths as positionals

        CLI: git add file1.txt file2.txt
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="add",
                    options=[
                        OptionSpec("all", short=["A"], arity=ZERO_ARITY),
                        OptionSpec("patch", short=["p"], arity=ZERO_ARITY),
                    ],
                    positionals=[PositionalSpec("files", arity=ONE_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["add", "file1.txt", "file2.txt"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
        )

    def test_add_all(self):
        """Test Git add-all flag with no file arguments.

        Verifies the pattern where a flag changes the subcommand to operate on all
        files, making positional arguments optional. Tests zero-or-more arity
        positional with no values when flag is present.

        Tests:
        - Flag-only subcommand invocation
        - Zero-or-more arity with zero values
        - Uppercase short flag (-A)

        CLI: git add -A
        """
        spec = CommandSpec(
            name="git",
            subcommands=[
                CommandSpec(
                    name="add",
                    options=[OptionSpec("all", short=["A"], arity=ZERO_ARITY)],
                    positionals=[PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["add", "-A"])
        assert result.subcommand is not None
        assert result.subcommand.options["all"].value is True
        assert result.subcommand.positionals["files"].value == ()


class TestComplexGitScenarios:
    """Test complex multi-feature Git scenarios."""

    def test_complete_git_cli(self):
        """Test comprehensive Git CLI with multiple subcommands and global options.

        Verifies a realistic full Git CLI specification with global options and
        multiple subcommands, each with their own options and positionals. Tests
        parser stability across diverse command invocations using the same spec.

        Tests:
        - Multiple subcommand definitions
        - Global vs subcommand options
        - Parser reuse across different commands
        - Comprehensive command coverage

        CLI: git commit -am "Update", git log --oneline --graph, git branch -d feature
        """
        spec = CommandSpec(
            name="git",
            options=[
                OptionSpec("version", arity=ZERO_ARITY),
                OptionSpec("help", short=["h"], arity=ZERO_ARITY),
            ],
            subcommands=[
                CommandSpec(
                    name="commit",
                    options=[
                        OptionSpec("message", short=["m"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("all", short=["a"], arity=ZERO_ARITY),
                    ],
                ),
                CommandSpec(
                    name="log",
                    options=[
                        OptionSpec("oneline", arity=ZERO_ARITY),
                        OptionSpec("graph", arity=ZERO_ARITY),
                    ],
                ),
                CommandSpec(
                    name="branch",
                    options=[OptionSpec("delete", short=["d"], arity=ZERO_ARITY)],
                    positionals=[PositionalSpec("names", arity=ZERO_OR_MORE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        # Test multiple commands
        result1 = parser.parse(["commit", "-am", "Update"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "commit"

        result2 = parser.parse(["log", "--oneline", "--graph"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "log"

        result3 = parser.parse(["branch", "-d", "feature"])
        assert result3.subcommand is not None
        assert result3.subcommand.command == "branch"

    def test_git_with_global_options(self):
        """Test Git global options before subcommand with counted verbosity.

        Verifies the pattern where global options (appearing before the subcommand)
        modify behavior across all subcommands. Tests accumulation mode COUNT for
        repeated verbosity flags and proper scoping of global vs subcommand options.

        Tests:
        - Global options before subcommand
        - COUNT accumulation mode (-vv)
        - Option scope separation (global vs subcommand)
        - Multiple global flags with subcommand flags

        CLI: git -vv status -s
        """
        spec = CommandSpec(
            name="git",
            options=[
                OptionSpec(
                    "verbose",
                    short=["v"],
                    arity=ZERO_ARITY,
                    accumulation_mode=AccumulationMode.COUNT,
                ),
                OptionSpec("quiet", short=["q"], arity=ZERO_ARITY),
            ],
            subcommands=[
                CommandSpec(
                    name="status",
                    options=[OptionSpec("short", short=["s"], arity=ZERO_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["-vv", "status", "-s"])
        assert result.options["verbose"].value == 2
        assert result.subcommand is not None
        assert result.subcommand.options["short"].value is True
