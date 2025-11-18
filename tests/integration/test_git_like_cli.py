"""Integration tests for Git-like CLI patterns using the App API.

This module tests realistic Git-style command structures with nested subcommands,
complex option combinations, and various argument patterns using the high-level App API.

Demonstrates validation system integration with:
- Commit count limits (positive integers)
- Clone depth values (positive integers)
- Verbosity levels (0-5 range)

Note: This file intentionally uses patterns that trigger linting warnings:
- FBT001/FBT002: Boolean arguments are part of the CLI API being tested
- A002: Parameter names like 'all' shadow builtins but match actual git CLI patterns
"""

# ruff: noqa: FBT001, FBT002, A002, TC001

from typing import Annotated

import pytest
from annotated_types import Interval

from aclaf import App
from aclaf.console import MockConsole
from aclaf.metadata import AtLeastOne, Flag, Opt
from aclaf.types import PositiveInt
from aclaf.validation import ValidationError
from aclaf.validation.command import AtLeastOneOf, MutuallyExclusive
from aclaf.validation.parameter import Pattern

# Type aliases for Git-specific constraints
CommitCount = PositiveInt
CloneDepth = PositiveInt
VerbosityLevel = Annotated[int, Interval(ge=0, le=5)]


@pytest.fixture
def git_cli(console: MockConsole) -> App:
    """Standard git CLI with common commands for most tests."""
    app = App("git", console=console)

    @app.command()
    def commit(  # pyright: ignore[reportUnusedFunction]
        message: Annotated[str, "-m"],
        all: Annotated[bool, "-a"] = False,
        amend: bool = False,
    ):
        console.print(f"[commit] message={message}")
        if all:
            console.print("[commit] all=True")
        if amend:
            console.print("[commit] amend=True")

    @app.command()
    def log(  # pyright: ignore[reportUnusedFunction]
        oneline: bool = False,
        graph: bool = False,
        all: bool = False,
        max_count: Annotated[CommitCount | None, "-n"] = None,
    ):
        if oneline:
            console.print("[log] oneline=True")
        if graph:
            console.print("[log] graph=True")
        if all:
            console.print("[log] all=True")
        if max_count:
            console.print(f"[log] max_count={max_count}")

    @app.command()
    def branch(name: tuple[str, ...] = (), all: Annotated[bool, "-a"] = False):  # pyright: ignore[reportUnusedFunction]
        console.print(f"[branch] name={name!r}")
        if all:
            console.print("[branch] all=True")

    @app.command()
    def remote():
        console.print("[remote] invoked")

    @remote.command(name="add")
    def remote_add(name: str, url: str):  # pyright: ignore[reportUnusedFunction]
        console.print(f"[remote add] name={name}")
        console.print(f"[remote add] url={url}")

    @remote.command(name="remove", aliases=["rm"])
    def remote_remove(name: str):  # pyright: ignore[reportUnusedFunction]
        console.print(f"[remote remove] name={name}")

    @app.command()
    def checkout(target: str, branch: Annotated[bool, "-b"] = False):  # pyright: ignore[reportUnusedFunction]
        console.print(f"[checkout] target={target}")
        if branch:
            console.print("[checkout] branch=True")

    @app.command()
    def add(  # pyright: ignore[reportUnusedFunction]
        files: Annotated[tuple[str, ...], AtLeastOne()],
        all: Annotated[bool, "-A"] = False,
        patch: Annotated[bool, "-p"] = False,
    ):
        console.print(f"[add] files={files!r}")
        if all:
            console.print("[add] all=True")
        if patch:
            console.print("[add] patch=True")

    return app


class TestGitCommitCommand:
    def test_commit_with_message(self, git_cli: App, console: MockConsole):
        git_cli(["commit", "-m", "Initial commit"])

        output = console.get_output()
        assert "[commit] message=Initial commit" in output

    def test_commit_combined_flags(self, git_cli: App, console: MockConsole):
        git_cli(["commit", "-am", "Update files"])

        output = console.get_output()
        assert "[commit] all=True" in output
        assert "[commit] message=Update files" in output

    def test_commit_amend(self, git_cli: App, console: MockConsole):
        git_cli(["commit", "--amend", "-m", "Updated message"])

        output = console.get_output()
        assert "[commit] amend=True" in output
        assert "[commit] message=Updated message" in output


class TestGitLogCommand:
    def test_log_with_options(self, git_cli: App, console: MockConsole):
        git_cli(["log", "--oneline", "--graph", "--all"])

        output = console.get_output()
        assert "[log] oneline=True" in output
        assert "[log] graph=True" in output
        assert "[log] all=True" in output

    def test_log_with_limit_valid(self, git_cli: App, console: MockConsole):
        git_cli(["log", "-n", "10"])

        output = console.get_output()
        assert "[log] max_count=10" in output


class TestGitBranchCommand:
    def test_branch_list(self, git_cli: App, console: MockConsole):
        git_cli(["branch"])

        output = console.get_output()
        assert "[branch] name=()" in output

    def test_branch_create(self, git_cli: App, console: MockConsole):
        git_cli(["branch", "feature-xyz"])

        output = console.get_output()
        assert "[branch] name=('feature-xyz',)" in output

    def test_branch_delete(self, console: MockConsole):
        # Inline CLI construction - different parameter signature than standard fixture
        app = App("git", console=console)

        @app.command()
        def branch(  # pyright: ignore[reportUnusedFunction]
            branches: tuple[str, ...],
            delete: Annotated[bool, "-d"] = False,
            force_delete: Annotated[bool, "-D"] = False,
        ):
            console.print(f"[branch] branches={branches!r}")
            if delete:
                console.print("[branch] delete=True")
            if force_delete:
                console.print("[branch] force_delete=True")

        app(["branch", "-d", "feature-xyz"])

        output = console.get_output()
        assert "[branch] delete=True" in output
        assert "[branch] branches=('feature-xyz',)" in output


class TestGitRemoteCommand:
    def test_remote_add(self, git_cli: App, console: MockConsole):
        git_cli(["remote", "add", "origin", "https://github.com/user/repo.git"])

        output = console.get_output()
        assert "[remote] invoked" in output
        assert "[remote add] name=origin" in output
        assert "[remote add] url=https://github.com/user/repo.git" in output

    def test_remote_remove_with_alias(self, git_cli: App, console: MockConsole):
        git_cli(["remote", "rm", "origin"])

        output = console.get_output()
        assert "[remote] invoked" in output
        assert "[remote remove] name=origin" in output


class TestGitCheckoutCommand:
    def test_checkout_branch(self, git_cli: App, console: MockConsole):
        git_cli(["checkout", "main"])

        output = console.get_output()
        assert "[checkout] target=main" in output

    def test_checkout_create_branch(self, git_cli: App, console: MockConsole):
        git_cli(["checkout", "-b", "feature-xyz"])

        output = console.get_output()
        assert "[checkout] branch=True" in output
        assert "[checkout] target=feature-xyz" in output


class TestGitAddCommand:
    def test_add_files(self, git_cli: App, console: MockConsole):
        git_cli(["add", "file1.txt", "file2.txt"])

        output = console.get_output()
        assert "[add] files=('file1.txt', 'file2.txt')" in output

    def test_add_all(self, console: MockConsole):
        # Inline CLI construction - different parameter signature than standard fixture
        app = App("git", console=console)

        @app.command()
        def add(files: tuple[str, ...] = (), all: Annotated[bool, "-A"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[add] files={files!r}")
            if all:
                console.print("[add] all=True")

        app(["add", "-A"])

        output = console.get_output()
        assert "[add] all=True" in output
        assert "[add] files=()" in output


class TestGitValidationFailures:
    """Test validation failures for git command parameters."""

    def test_clone_with_invalid_depth_zero(self, console: MockConsole):
        """Test clone depth validation rejects zero."""
        app = App("git", console=console)

        @app.command()
        def clone(
            repository: str,
            depth: Annotated[CloneDepth | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[clone] repository={repository}")
            if depth:
                console.print(f"[clone] depth={depth}")

        with pytest.raises(ValidationError) as exc_info:
            app(["clone", "https://github.com/user/repo.git", "--depth", "0"])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_clone_with_invalid_depth_negative(self, console: MockConsole):
        """Test clone depth validation rejects negative values."""
        app = App("git", console=console)

        @app.command()
        def clone(
            repository: str,
            depth: Annotated[CloneDepth | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[clone] repository={repository}")
            if depth:
                console.print(f"[clone] depth={depth}")

        with pytest.raises(ValidationError) as exc_info:
            app(["clone", "https://github.com/user/repo.git", "--depth", "-1"])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_log_with_invalid_max_count_zero(self, console: MockConsole):
        """Test log max_count validation rejects zero."""
        app = App("git", console=console)

        @app.command()
        def log(
            max_count: Annotated[CommitCount | None, "-n"] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            if max_count:
                console.print(f"[log] max_count={max_count}")

        with pytest.raises(ValidationError) as exc_info:
            app(["log", "-n", "0"])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_log_with_invalid_max_count_negative(self, console: MockConsole):
        """Test log max_count validation rejects negative values."""
        app = App("git", console=console)

        @app.command()
        def log(
            max_count: Annotated[CommitCount | None, "-n"] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            if max_count:
                console.print(f"[log] max_count={max_count}")

        with pytest.raises(ValidationError) as exc_info:
            app(["log", "-n", "-5"])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_fetch_with_invalid_depth_zero(self, console: MockConsole):
        """Test fetch depth validation rejects zero."""
        app = App("git", console=console)

        @app.command()
        def fetch(
            remotes: tuple[str, ...] = (),
            depth: Annotated[CloneDepth | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            if remotes:
                console.print(f"[fetch] remotes={remotes!r}")
            if depth:
                console.print(f"[fetch] depth={depth}")

        with pytest.raises(ValidationError) as exc_info:
            app(["fetch", "origin", "--depth", "0"])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_shortlog_with_invalid_max_count_zero(self, console: MockConsole):
        """Test shortlog max_count validation rejects zero."""
        app = App("git", console=console)

        @app.command()
        def shortlog(
            max_count: Annotated[CommitCount | None, "-n"] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            if max_count:
                console.print(f"[shortlog] max_count={max_count}")

        with pytest.raises(ValidationError) as exc_info:
            app(["shortlog", "-n", "0"])

        assert "must be greater than 0" in str(exc_info.value).lower()


class TestGitCommandValidators:
    """Test command-scoped validators for git commands."""

    def test_clone_depth_and_shallow_since_mutually_exclusive(
        self, console: MockConsole
    ):
        """Test that --depth and --shallow-since are mutually exclusive."""
        app = App("git", console=console)

        @app.command()
        def clone(
            repository: str,
            depth: Annotated[CloneDepth | None, Opt()] = None,
            shallow_since: Annotated[str | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[clone] repository={repository}")
            if depth:
                console.print(f"[clone] depth={depth}")
            if shallow_since:
                console.print(f"[clone] shallow_since={shallow_since}")

        # Add validation to the command instance
        clone.validate(MutuallyExclusive(parameter_names=("depth", "shallow_since")))

        with pytest.raises(ValidationError) as exc_info:
            app(
                [
                    "clone",
                    "https://github.com/user/repo.git",
                    "--depth",
                    "1",
                    "--shallow-since",
                    "2024-01-01",
                ]
            )

        assert "mutually exclusive" in str(exc_info.value).lower()

    def test_log_oneline_and_format_mutually_exclusive(self, console: MockConsole):
        """Test that --oneline and --format are mutually exclusive."""
        app = App("git", console=console)

        @app.command()
        def log(
            oneline: bool = False,
            format: Annotated[str | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            if oneline:
                console.print("[log] oneline=True")
            if format:
                console.print(f"[log] format={format}")

        # Add validation to the command instance
        log.validate(MutuallyExclusive(parameter_names=("oneline", "format")))

        with pytest.raises(ValidationError) as exc_info:
            app(["log", "--oneline", "--format", "%H %s"])

        assert "mutually exclusive" in str(exc_info.value).lower()

    @pytest.mark.xfail(
        reason="AtLeastOneOf doesn't distinguish between user-provided boolean flags "
        "and default values. Boolean flags with defaults are always present in the "
        "parameter dict, so validation incorrectly considers them 'provided' even "
        "when the user didn't specify them. This requires tracking which parameters "
        "were explicitly set by the user vs. which are defaults."
    )
    def test_commit_amend_requires_message_or_no_edit(self, console: MockConsole):
        """Test that --amend requires either -m or --no-edit."""
        app = App("git", console=console)

        @app.command()
        def commit(
            message: Annotated[str | None, "-m"] = None,
            amend: bool = False,
            no_edit: bool = False,
        ):  # pyright: ignore[reportUnusedFunction]
            if message:
                console.print(f"[commit] message={message}")
            if amend:
                console.print("[commit] amend=True")
            if no_edit:
                console.print("[commit] no_edit=True")

        # Add validation: if amend is set, need at least message or no_edit
        # Note: This test demonstrates the limitation - Requires validator doesn't
        # check conditional relationships like "if A then B or C". We'd need custom
        # validator logic. For now, let's use AtLeastOneOf to require at least one
        # option when amend is used.
        commit.validate(AtLeastOneOf(parameter_names=("message", "no_edit")))

        with pytest.raises(ValidationError) as exc_info:
            app(["commit", "--amend"])

        assert "at least one" in str(exc_info.value).lower()

    def test_branch_name_pattern_validation(self, console: MockConsole):
        """Test branch name pattern validation."""
        app = App("git", console=console)

        branch_name = Annotated[str, Pattern(r"^[a-zA-Z0-9/_-]+$")]

        @app.command()
        def branch(name: branch_name):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[branch] name={name}")

        with pytest.raises(ValidationError) as exc_info:
            app(["branch", "invalid branch name!"])

        assert "pattern" in str(exc_info.value).lower()


class TestComplexGitScenarios:
    def test_complete_git_cli(self, console: MockConsole):
        app = App("git", console=console)

        @app.command()
        def commit(message: Annotated[str, "-m"], all: Annotated[bool, "-a"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[commit] message={message}")
            if all:
                console.print("[commit] all=True")

        @app.command()
        def log(oneline: bool = False, graph: bool = False):  # pyright: ignore[reportUnusedFunction]
            if oneline:
                console.print("[log] oneline=True")
            if graph:
                console.print("[log] graph=True")

        @app.command()
        def branch(names: tuple[str, ...] = (), delete: Annotated[bool, "-d"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[branch] names={names!r}")
            if delete:
                console.print("[branch] delete=True")

        # Test multiple sequential command invocations
        app(["commit", "-am", "Update"])
        output1 = console.get_output()
        assert "[commit] message=Update" in output1
        assert "[commit] all=True" in output1

        # Clear console between invocations to test commands independently
        console.clear()
        app(["log", "--oneline", "--graph"])
        output2 = console.get_output()
        assert "[log] oneline=True" in output2
        assert "[log] graph=True" in output2

        console.clear()
        app(["branch", "-d", "feature"])
        output3 = console.get_output()
        assert "[branch] delete=True" in output3
        assert "[branch] names=('feature',)" in output3

    def test_git_with_global_options(self, console: MockConsole):
        app = App("git", console=console)

        @app.handler()
        def git(  # pyright: ignore[reportUnusedFunction]
            verbose: Annotated[int, "-v", Flag(count=True)] = 0,
            quiet: Annotated[bool, "-q"] = False,
        ):
            if verbose:
                console.print(f"[git] verbose={verbose}")
            if quiet:
                console.print("[git] quiet=True")

        @app.command()
        def status(short: Annotated[bool, "-s"] = False):  # pyright: ignore[reportUnusedFunction]
            if short:
                console.print("[status] short=True")

        app(["-vv", "status", "-s"])

        output = console.get_output()
        assert "[git] verbose=2" in output
        assert "[status] short=True" in output


class TestGitCloneCommand:
    def test_clone_with_depth_valid(self, console: MockConsole):
        """Test clone command with valid depth."""
        app = App("git", console=console)

        @app.command()
        def clone(
            repository: str,
            depth: Annotated[CloneDepth | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[clone] repository={repository}")
            if depth:
                console.print(f"[clone] depth={depth}")

        app(["clone", "https://github.com/user/repo.git", "--depth", "1"])

        output = console.get_output()
        assert "[clone] repository=https://github.com/user/repo.git" in output
        assert "[clone] depth=1" in output


class TestGitFetchCommand:
    def test_fetch_with_depth_valid(self, console: MockConsole):
        """Test fetch command with valid depth."""
        app = App("git", console=console)

        @app.command()
        def fetch(
            remotes: tuple[str, ...] = (),
            depth: Annotated[CloneDepth | None, Opt()] = None,
            prune: Annotated[bool, "-p"] = False,
        ):  # pyright: ignore[reportUnusedFunction]
            if remotes:
                console.print(f"[fetch] remotes={remotes!r}")
            if depth:
                console.print(f"[fetch] depth={depth}")
            if prune:
                console.print("[fetch] prune=True")

        app(["fetch", "origin", "--depth", "50", "-p"])

        output = console.get_output()
        assert "[fetch] remotes=('origin',)" in output
        assert "[fetch] depth=50" in output
        assert "[fetch] prune=True" in output


class TestGitShortlogCommand:
    def test_shortlog_with_count_valid(self, console: MockConsole):
        """Test shortlog command with valid commit count."""
        app = App("git", console=console)

        @app.command()
        def shortlog(
            max_count: Annotated[CommitCount | None, "-n"] = None,
            summary: Annotated[bool, "-s"] = False,
            numbered: Annotated[bool, Opt()] = False,
        ):  # pyright: ignore[reportUnusedFunction]
            if max_count:
                console.print(f"[shortlog] max_count={max_count}")
            if summary:
                console.print("[shortlog] summary=True")
            if numbered:
                console.print("[shortlog] numbered=True")

        app(["shortlog", "-n", "25", "-s", "--numbered"])

        output = console.get_output()
        assert "[shortlog] max_count=25" in output
        assert "[shortlog] summary=True" in output
        assert "[shortlog] numbered=True" in output
