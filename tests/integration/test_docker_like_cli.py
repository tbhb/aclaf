"""Integration tests for Docker-like CLI patterns using the App API.

This module tests realistic Docker-style command structures with subcommands,
short flag combinations, environment variables, and various argument patterns
using the high-level App API.

Note: This file intentionally uses patterns that trigger linting warnings:
- FBT001/FBT002: Boolean arguments are part of the CLI API being tested
- A001/A002: Parameter names like 'all' and 'exec' shadow builtins but match
  actual docker CLI patterns
- PLR0913: Some commands have many parameters matching real docker CLI
- TC001: MockConsole is used at runtime, not just for type checking
"""

# ruff: noqa: FBT001, FBT002, A001, A002, PLR0913, TC001

from typing import Annotated

import pytest

from aclaf import App
from aclaf.console import MockConsole
from aclaf.metadata import AtLeastOne, Collect, ZeroOrMore


@pytest.fixture
def docker_run_cli(console: MockConsole) -> App:
    """Docker CLI with run command for most run tests."""
    app = App("docker", console=console)

    @app.command()
    def run(  # pyright: ignore[reportUnusedFunction]
        image: str,
        command: Annotated[tuple[str, ...], ZeroOrMore()] = (),
        interactive: Annotated[bool, "-i"] = False,
        tty: Annotated[bool, "-t"] = False,
        rm: bool = False,
        env: Annotated[tuple[str, ...], "-e", Collect()] = (),
    ):
        console.print(f"[run] image={image}")
        if command:
            console.print(f"[run] command={command!r}")
        if interactive:
            console.print("[run] interactive=True")
        if tty:
            console.print("[run] tty=True")
        if rm:
            console.print("[run] rm=True")
        if env:
            console.print(f"[run] env={env!r}")

    return app


class TestDockerRunCommand:
    def test_run_basic(self, docker_run_cli: App, console: MockConsole):
        docker_run_cli(["run", "ubuntu"])

        output = console.get_output()
        assert "[run] image=ubuntu" in output

    def test_run_with_command(self, docker_run_cli: App, console: MockConsole):
        docker_run_cli(["run", "ubuntu", "echo", "hello"])

        output = console.get_output()
        assert "[run] image=ubuntu" in output
        assert "[run] command=('echo', 'hello')" in output

    def test_run_with_flags(self, docker_run_cli: App, console: MockConsole):
        docker_run_cli(["run", "-it", "ubuntu"])

        output = console.get_output()
        assert "[run] interactive=True" in output
        assert "[run] tty=True" in output
        assert "[run] image=ubuntu" in output

    def test_run_with_remove_flag(self, docker_run_cli: App, console: MockConsole):
        docker_run_cli(["run", "--rm", "ubuntu"])

        output = console.get_output()
        assert "[run] rm=True" in output
        assert "[run] image=ubuntu" in output

    def test_run_with_environment_variables(
        self, docker_run_cli: App, console: MockConsole
    ):
        docker_run_cli(["run", "-e", "VAR=value", "ubuntu"])

        output = console.get_output()
        assert "[run] env=('VAR=value',)" in output
        assert "[run] image=ubuntu" in output

    def test_run_complex(self, docker_run_cli: App, console: MockConsole):
        docker_run_cli(["run", "-it", "--rm", "-e", "VAR=val", "ubuntu", "/bin/bash"])

        output = console.get_output()
        assert "[run] interactive=True" in output
        assert "[run] tty=True" in output
        assert "[run] rm=True" in output
        assert "[run] env=('VAR=val',)" in output
        assert "[run] image=ubuntu" in output
        assert "[run] command=('/bin/bash',)" in output


class TestDockerExecCommand:
    def test_exec_basic(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def exec(  # pyright: ignore[reportUnusedFunction]
            container: str, command: Annotated[tuple[str, ...], AtLeastOne()]
        ):
            console.print(f"[exec] container={container}")
            console.print(f"[exec] command={command!r}")

        app(["exec", "mycontainer", "ls", "-la"])

        output = console.get_output()
        assert "[exec] container=mycontainer" in output
        assert "[exec] command=('ls', '-la')" in output

    def test_exec_with_flags(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def exec(  # pyright: ignore[reportUnusedFunction]
            container: str,
            command: Annotated[tuple[str, ...], AtLeastOne()],
            interactive: Annotated[bool, "-i"] = False,
            tty: Annotated[bool, "-t"] = False,
        ):
            console.print(f"[exec] container={container}")
            console.print(f"[exec] command={command!r}")
            if interactive:
                console.print("[exec] interactive=True")
            if tty:
                console.print("[exec] tty=True")

        app(["exec", "-it", "mycontainer", "bash"])

        output = console.get_output()
        assert "[exec] interactive=True" in output
        assert "[exec] tty=True" in output
        assert "[exec] container=mycontainer" in output
        assert "[exec] command=('bash',)" in output


class TestDockerPsCommand:
    def test_ps_default(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def ps(  # pyright: ignore[reportUnusedFunction]
            all: Annotated[bool, "-a"] = False, quiet: Annotated[bool, "-q"] = False
        ):
            console.print("[ps] invoked")
            if all:
                console.print("[ps] all=True")
            if quiet:
                console.print("[ps] quiet=True")

        app(["ps"])

        output = console.get_output()
        assert "[ps] invoked" in output

    def test_ps_all(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def ps(all: Annotated[bool, "-a"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print("[ps] invoked")
            if all:
                console.print("[ps] all=True")

        app(["ps", "-a"])

        output = console.get_output()
        assert "[ps] all=True" in output

    def test_ps_quiet(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def ps(  # pyright: ignore[reportUnusedFunction]
            all: Annotated[bool, "-a"] = False, quiet: Annotated[bool, "-q"] = False
        ):
            console.print("[ps] invoked")
            if all:
                console.print("[ps] all=True")
            if quiet:
                console.print("[ps] quiet=True")

        app(["ps", "-aq"])

        output = console.get_output()
        assert "[ps] all=True" in output
        assert "[ps] quiet=True" in output


class TestDockerBuildCommand:
    def test_build_basic(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def build(context: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[build] context={context}")

        app(["build", "."])

        output = console.get_output()
        assert "[build] context=." in output

    def test_build_with_tag(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def build(  # pyright: ignore[reportUnusedFunction]
            context: str, tag: Annotated[str | None, "-t"] = None
        ):
            console.print(f"[build] context={context}")
            if tag:
                console.print(f"[build] tag={tag}")

        app(["build", "-t", "myimage:latest", "."])

        output = console.get_output()
        assert "[build] tag=myimage:latest" in output
        assert "[build] context=." in output

    def test_build_with_file(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def build(  # pyright: ignore[reportUnusedFunction]
            context: str,
            file: Annotated[str | None, "-f"] = None,
            tag: Annotated[str | None, "-t"] = None,
        ):
            console.print(f"[build] context={context}")
            if file:
                console.print(f"[build] file={file}")
            if tag:
                console.print(f"[build] tag={tag}")

        app(["build", "-f", "Dockerfile.prod", "-t", "myimage", "."])

        output = console.get_output()
        assert "[build] file=Dockerfile.prod" in output
        assert "[build] tag=myimage" in output
        assert "[build] context=." in output


class TestDockerVolumeCommand:
    def test_volume_create(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def volume():
            console.print("[volume] invoked")

        @volume.command()
        def create(name: Annotated[tuple[str, ...], ZeroOrMore()] = ()):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[volume create] name={name!r}")

        app(["volume", "create", "myvolume"])

        output = console.get_output()
        assert "[volume] invoked" in output
        assert "[volume create] name=('myvolume',)" in output

    def test_volume_list(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def volume():
            console.print("[volume] invoked")

        @volume.command(aliases=["list"])
        def ls():  # pyright: ignore[reportUnusedFunction]
            console.print("[volume ls] invoked")

        app(["volume", "ls"])

        output = console.get_output()
        assert "[volume] invoked" in output
        assert "[volume ls] invoked" in output


class TestComplexDockerScenarios:
    def test_complete_docker_cli(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def run(  # pyright: ignore[reportUnusedFunction]
            image: str,
            command: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            interactive: Annotated[bool, "-i"] = False,
            tty: Annotated[bool, "-t"] = False,
            rm: bool = False,
        ):
            console.print(f"[run] image={image}")
            if command:
                console.print(f"[run] command={command!r}")
            if interactive:
                console.print("[run] interactive=True")
            if tty:
                console.print("[run] tty=True")
            if rm:
                console.print("[run] rm=True")

        @app.command()
        def ps(  # pyright: ignore[reportUnusedFunction]
            all: Annotated[bool, "-a"] = False, quiet: Annotated[bool, "-q"] = False
        ):
            console.print("[ps] invoked")
            if all:
                console.print("[ps] all=True")
            if quiet:
                console.print("[ps] quiet=True")

        @app.command()
        def exec(  # pyright: ignore[reportUnusedFunction]
            container: str,
            command: Annotated[tuple[str, ...], AtLeastOne()],
            interactive: Annotated[bool, "-i"] = False,
            tty: Annotated[bool, "-t"] = False,
        ):
            console.print(f"[exec] container={container}")
            console.print(f"[exec] command={command!r}")
            if interactive:
                console.print("[exec] interactive=True")
            if tty:
                console.print("[exec] tty=True")

        # Test multiple sequential command invocations
        app(["run", "-it", "ubuntu"])
        output1 = console.get_output()
        assert "[run] interactive=True" in output1
        assert "[run] tty=True" in output1
        assert "[run] image=ubuntu" in output1

        # Clear console between invocations to test commands independently
        console.clear()
        app(["ps", "-a"])
        output2 = console.get_output()
        assert "[ps] all=True" in output2

        console.clear()
        app(["exec", "container", "bash"])
        output3 = console.get_output()
        assert "[exec] container=container" in output3
        assert "[exec] command=('bash',)" in output3

    def test_docker_run_with_port_mappings(self, console: MockConsole):
        app = App("docker", console=console)

        @app.command()
        def run(  # pyright: ignore[reportUnusedFunction]
            image: str, publish: Annotated[tuple[str, ...], "-p", Collect()] = ()
        ):
            console.print(f"[run] image={image}")
            if publish:
                console.print(f"[run] publish={publish!r}")

        app(["run", "-p", "8080:80", "-p", "443:443", "nginx"])

        output = console.get_output()
        assert "[run] publish=('8080:80', '443:443')" in output
        assert "[run] image=nginx" in output
