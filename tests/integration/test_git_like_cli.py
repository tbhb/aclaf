"""Integration tests for Git-like CLI patterns using the App API.

This module tests realistic Git-style command structures with nested subcommands,
complex option combinations, and various argument patterns using the high-level App API.

Note: This file intentionally uses patterns that trigger linting warnings:
- FBT001/FBT002: Boolean arguments are part of the CLI API being tested
- A002: Parameter names like 'all' shadow builtins but match actual git CLI patterns
"""

# ruff: noqa: FBT001, FBT002, A002, TC001

from typing import Annotated

import pytest

from aclaf import App
from aclaf.console import MockConsole
from aclaf.metadata import AtLeastOne, Flag


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
        max_count: Annotated[str | None, "-n"] = None,
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

    def test_log_with_limit(self, git_cli: App, console: MockConsole):
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
