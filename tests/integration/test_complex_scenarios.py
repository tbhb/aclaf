"""Integration tests for complex CLI scenarios using the App API.

This module tests edge cases, unusual combinations, and complex CLI patterns that
push the boundaries of the framework's capabilities. These tests serve as the
reference for the most challenging CLI patterns and validate that the App API
can handle all complexity without falling back to lower-level parser APIs.

Coverage areas:
- Multi-level nested subcommands (3+ levels deep)
- Complex combinations of options, positionals, and subcommands
- Various accumulation modes (COUNT, COLLECT, LAST_WINS)
- Trailing arguments after `--` separator
- Complex arity patterns including bounded ranges
- Real-world CLI patterns (build tools, package managers, database CLIs)

Demonstrates validation system integration with:
- Thread/job counts (positive integers with upper bounds)
- Percentage values (0-100 range)
- Port numbers for database connections
- Optimization levels (0-3 range)

Contains 12 integration tests organized into 8 test classes. Each test is
independent with inline CLI construction (no shared fixtures) to demonstrate
isolated complex scenarios clearly and maintain complete independence between
test cases. This architectural decision prioritizes clarity and self-contained
examples over fixture reuse.

Note: This file intentionally uses patterns that trigger linting warnings:
- FBT001/FBT002: Boolean arguments are part of the CLI API being tested
- PLR0913: Some commands have many parameters matching real CLI patterns
- TC001: MockConsole is used at runtime, not just for type checking
"""

# ruff: noqa: FBT001, FBT002, A001, TC001

from typing import Annotated

import pytest
from annotated_types import Interval

from aclaf import App, Context
from aclaf.console import MockConsole
from aclaf.metadata import AtLeastOne, Collect, Flag, ZeroOrMore
from aclaf.parser import ParserConfiguration
from aclaf.validation import ValidationError
from aclaf.validation.command import ConflictsWith, MutuallyExclusive, Requires

# Type aliases for build tools and complex scenarios
ThreadCount = Annotated[int, Interval(ge=1, le=128)]
JobCount = Annotated[int, Interval(ge=1, le=64)]
Percentage = Annotated[int, Interval(ge=0, le=100)]
Port = Annotated[int, Interval(ge=1, le=65535)]
OptimizationLevel = Annotated[int, Interval(ge=0, le=3)]


class TestMultiLevelSubcommands:
    def test_three_level_nesting_with_options(self, console: MockConsole):
        # Inline CLI construction - 3-level nesting with options at each level
        app = App("cloud", console=console)

        @app.handler()
        def cloud(verbose: Annotated[bool, "-v"] = False):  # pyright: ignore[reportUnusedFunction]
            if verbose:
                console.print("[cloud] verbose=True")

        @app.command()
        def compute(region: Annotated[str | None, "-r"] = None):
            console.print("[compute] invoked")
            if region:
                console.print(f"[compute] region={region}")

        @compute.command()
        def instances(zone: Annotated[str | None, "-z"] = None):
            console.print("[instances] invoked")
            if zone:
                console.print(f"[instances] zone={zone}")

        @instances.command()
        def create(  # pyright: ignore[reportUnusedFunction]
            name: str,
            machine_type: Annotated[str | None, "-m"] = None,
        ):
            console.print(f"[create] name={name}")
            if machine_type:
                console.print(f"[create] machine_type={machine_type}")

        app(
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

        output = console.get_output()
        assert "[cloud] verbose=True" in output
        assert "[compute] invoked" in output
        assert "[compute] region=us-west1" in output
        assert "[instances] invoked" in output
        assert "[instances] zone=us-west1-a" in output
        assert "[create] name=my-instance" in output
        assert "[create] machine_type=n1-standard-1" in output


class TestOptionsPositionalsSubcommands:
    def test_all_features_together(self, console: MockConsole):
        # Inline CLI construction - combining all three CLI features with validation
        app = App("tool", console=console)

        @app.handler()
        def tool(  # pyright: ignore[reportUnusedFunction]
            verbose: Annotated[int, "-v", Flag(count=True)] = 0,
            config: Annotated[str | None, "-c"] = None,
        ):
            if verbose:
                console.print(f"[tool] verbose={verbose}")
            if config:
                console.print(f"[tool] config={config}")

        @app.command()
        def process(  # pyright: ignore[reportUnusedFunction]
            input_file: str,
            files: Annotated[tuple[str, ...], AtLeastOne()],
            threads: Annotated[ThreadCount | None, "-t"] = None,
            output: Annotated[str | None, "-o"] = None,
        ):
            console.print(f"[process] input={input_file}")
            console.print(f"[process] files={files!r}")
            if threads:
                console.print(f"[process] threads={threads}")
            if output:
                console.print(f"[process] output={output}")

        app(
            [
                "-vv",
                "--config",
                "config.yml",
                "process",
                "-t",
                "4",
                "-o",
                "output.txt",
                "input.txt",
                "file1.txt",
                "file2.txt",
            ]
        )

        output = console.get_output()
        assert "[tool] verbose=2" in output
        assert "[tool] config=config.yml" in output
        assert "[process] input=input.txt" in output
        assert "[process] files=('file1.txt', 'file2.txt')" in output
        assert "[process] threads=4" in output
        assert "[process] output=output.txt" in output

    def test_mixed_arity_positionals(self, console: MockConsole):
        # Inline CLI construction - testing mixed arity positionals
        # Note: In the App API, variadic positionals consume greedily
        # This test demonstrates that with ZeroOrMore, all extra args are consumed
        app = App("cmd", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            required: str,
            optional: Annotated[tuple[str, ...], ZeroOrMore()] = (),
        ):
            console.print(f"[cmd] required={required}")
            console.print(f"[cmd] optional={optional!r}")

        app(["cmd", "req", "mul1", "mul2", "mul3"])

        output = console.get_output()
        assert "[cmd] required=req" in output
        # With ZeroOrMore, all remaining positionals are consumed
        assert "[cmd] optional=('mul1', 'mul2', 'mul3')" in output


class TestAccumulationWithComplexOptions:
    def test_collect_mode_with_multi_value_options(self, console: MockConsole):
        # Inline CLI construction - Collect accumulation with variadic option values
        # Each -I occurrence can take multiple values via AtLeastOne
        app = App("cmd", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            include: Annotated[
                tuple[tuple[str, ...], ...], "-I", Collect(), AtLeastOne()
            ] = (),
        ):
            console.print(f"[cmd] include={include!r}")

        app(
            [
                "cmd",
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

        output = console.get_output()
        assert (
            "[cmd] include=(('path1', 'path2'), ('path3',), "
            "('path4', 'path5', 'path6'))"
        ) in output

    def test_multiple_accumulation_modes(self, console: MockConsole):
        # Inline CLI construction - testing COUNT, COLLECT, and default (last-wins)
        # with validated optimization level
        app = App("compiler", console=console)

        @app.command()
        def compiler(  # pyright: ignore[reportUnusedFunction]
            define: Annotated[tuple[str, ...], "-D", Collect()] = (),
            include: Annotated[tuple[str, ...], "-I", Collect()] = (),
            verbose: Annotated[int, "-v", Flag(count=True)] = 0,
            optimization: Annotated[OptimizationLevel, "-O"] = 0,
        ):
            console.print(f"[compiler] define={define!r}")
            console.print(f"[compiler] include={include!r}")
            console.print(f"[compiler] verbose={verbose}")
            console.print(f"[compiler] optimization={optimization}")

        app(
            [
                "compiler",
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

        output = console.get_output()
        assert "[compiler] define=('DEBUG', 'VERSION=1.0')" in output
        assert "[compiler] include=('/usr/include', '/usr/local/include')" in output
        assert "[compiler] verbose=2" in output
        assert "[compiler] optimization=2" in output


class TestTrailingArgsInComplexScenarios:
    def test_trailing_args_with_subcommand_and_options(self, console: MockConsole):
        # Inline CLI construction - testing trailing args after `--`
        # The Context parameter allows access to parse_result.extra_args
        app = App("kubectl", console=console)

        @app.command()
        def exec(  # pyright: ignore[reportUnusedFunction]
            ctx: Context,
            pod: str,
            interactive: Annotated[bool, "-i"] = False,
            tty: Annotated[bool, "-t"] = False,
        ):
            console.print(f"[exec] pod={pod}")
            if interactive:
                console.print("[exec] interactive=True")
            if tty:
                console.print("[exec] tty=True")
            extra_args = ctx.parse_result.extra_args
            if extra_args:
                console.print(f"[exec] extra_args={extra_args!r}")

        app(["exec", "-it", "mypod", "--", "/bin/bash", "-c", "echo hello"])

        output = console.get_output()
        assert "[exec] pod=mypod" in output
        assert "[exec] interactive=True" in output
        assert "[exec] tty=True" in output
        assert "[exec] extra_args=('/bin/bash', '-c', 'echo hello')" in output


class TestComplexArityPatterns:
    def test_bounded_arity_ranges(self, console: MockConsole):
        # Inline CLI construction - testing bounded arity ranges (2-5)
        # Using union type to represent arity bounds (minimum 2, maximum 5)
        app = App("cmd", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[
                tuple[str, str]
                | tuple[str, str, str]
                | tuple[str, str, str, str]
                | tuple[str, str, str, str, str],
                "-f",
                ZeroOrMore(),
            ] = ("", ""),
        ):
            console.print(f"[cmd] files={files!r}")

        # Minimum satisfied (2)
        app(["cmd", "-f", "a", "b"])
        output1 = console.get_output()
        assert "[cmd] files=('a', 'b')" in output1

        # Clear console between invocations to test commands independently
        console.clear()
        # Maximum satisfied (5)
        app(["cmd", "-f", "a", "b", "c", "d", "e"])
        output2 = console.get_output()
        assert "[cmd] files=('a', 'b', 'c', 'd', 'e')" in output2

        console.clear()
        # Middle range (3)
        app(["cmd", "-f", "a", "b", "c"])
        output3 = console.get_output()
        assert "[cmd] files=('a', 'b', 'c')" in output3

    def test_unbounded_positionals_with_required(self, console: MockConsole):
        # Inline CLI construction - testing ONE_OR_MORE followed by EXACTLY_ONE
        app = App("cmd", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            sources: Annotated[tuple[str, ...], AtLeastOne()],
            dest: str,
        ):
            console.print(f"[cmd] sources={sources!r}")
            console.print(f"[cmd] dest={dest}")

        app(["cmd", "src1", "src2", "src3", "destination"])

        output = console.get_output()
        assert "[cmd] sources=('src1', 'src2', 'src3')" in output
        assert "[cmd] dest=destination" in output


class TestRealWorldBuildTool:
    def test_make_like_cli(self, console: MockConsole):
        # Inline CLI construction - make-like build tool with job count validation
        app = App("build", console=console)

        @app.command()
        def build(  # pyright: ignore[reportUnusedFunction]
            targets: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            file: Annotated[str | None, "-f"] = None,
            jobs: Annotated[JobCount | None, "-j"] = None,
            keep_going: Annotated[bool, "-k"] = False,
        ):
            if file:
                console.print(f"[build] file={file}")
            if jobs:
                console.print(f"[build] jobs={jobs}")
            if keep_going:
                console.print("[build] keep_going=True")
            console.print(f"[build] targets={targets!r}")

        app(["build", "-f", "Buildfile", "-j", "4", "-k", "clean", "build", "test"])

        output = console.get_output()
        assert "[build] file=Buildfile" in output
        assert "[build] jobs=4" in output
        assert "[build] keep_going=True" in output
        assert "[build] targets=('clean', 'build', 'test')" in output


class TestPackageManagerPatterns:
    def test_npm_like_install(self, console: MockConsole):
        # Inline CLI construction - npm-like package manager with aliases
        parser_config = ParserConfiguration(allow_aliases=True)
        app = App("pkg", console=console, parser_config=parser_config)

        @app.command(aliases=["i", "add"])
        def install(  # pyright: ignore[reportUnusedFunction]
            packages: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            save_dev: Annotated[bool, "-D"] = False,
            global_install: Annotated[bool, "-g"] = False,
        ):
            console.print("[install] invoked")
            if packages:
                console.print(f"[install] packages={packages!r}")
            if save_dev:
                console.print("[install] save_dev=True")
            if global_install:
                console.print("[install] global=True")

        app(["install", "-D", "typescript", "eslint"])

        output = console.get_output()
        assert "[install] invoked" in output
        assert "[install] save_dev=True" in output
        assert "[install] packages=('typescript', 'eslint')" in output

    def test_pip_like_install(self, console: MockConsole):
        # Inline CLI construction - pip-like package manager
        app = App("pip", console=console)

        @app.command()
        def install(  # pyright: ignore[reportUnusedFunction]
            packages: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            requirement: Annotated[str | None, "-r"] = None,
            upgrade: Annotated[bool, "-U"] = False,
            user: bool = False,
        ):
            if requirement:
                console.print(f"[install] requirement={requirement}")
            if user:
                console.print("[install] user=True")
            if upgrade:
                console.print("[install] upgrade=True")
            if packages:
                console.print(f"[install] packages={packages!r}")

        app(["install", "-r", "requirements.txt", "--user", "--upgrade"])

        output = console.get_output()
        assert "[install] requirement=requirements.txt" in output
        assert "[install] user=True" in output
        assert "[install] upgrade=True" in output


class TestDatabaseCLIPatterns:
    def test_psql_like_connection(self, console: MockConsole):
        # Inline CLI construction - database connection CLI pattern with port validation
        app = App("db", console=console)

        @app.command()
        def db(  # pyright: ignore[reportUnusedFunction]
            command: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            host: Annotated[str | None, "-h"] = None,
            port: Annotated[Port | None, "-p"] = None,
            username: Annotated[str | None, "-U"] = None,
            database: Annotated[str | None, "-d"] = None,
        ):
            if host:
                console.print(f"[db] host={host}")
            if port:
                console.print(f"[db] port={port}")
            if username:
                console.print(f"[db] username={username}")
            if database:
                console.print(f"[db] database={database}")
            if command:
                console.print(f"[db] command={command!r}")

        app(
            [
                "db",
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

        output = console.get_output()
        assert "[db] host=localhost" in output
        assert "[db] port=5432" in output
        assert "[db] username=admin" in output
        assert "[db] database=mydb" in output


class TestComplexCommandValidators:
    """Test command-scoped validators for complex scenarios."""

    def test_build_jobs_and_serial_mutually_exclusive(self, console: MockConsole):
        """Test --jobs and --serial are mutually exclusive."""
        app = App("build", console=console)

        @app.command()
        def build(
            targets: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            jobs: Annotated[JobCount | None, "-j"] = None,
            serial: Annotated[bool, "-s"] = False,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[build] targets={targets!r}")
            if jobs:
                console.print(f"[build] jobs={jobs}")
            if serial:
                console.print("[build] serial=True")

        # Add validation to the command instance
        build.validate(MutuallyExclusive(parameter_names=("jobs", "serial")))

        with pytest.raises(ValidationError) as exc_info:
            app(["build", "-j", "4", "-s", "all"])

        assert "mutually exclusive" in str(exc_info.value).lower()

    def test_build_load_average_requires_jobs(self, console: MockConsole):
        """Test --load-average requires --jobs."""
        app = App("build", console=console)

        @app.command()
        def build(
            targets: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            jobs: Annotated[JobCount | None, "-j"] = None,
            load_average: Annotated[float | None, "-l"] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[build] targets={targets!r}")
            if jobs:
                console.print(f"[build] jobs={jobs}")
            if load_average:
                console.print(f"[build] load_average={load_average}")

        # Add validation to the command instance
        build.validate(Requires(source="load_average", required=("jobs",)))

        with pytest.raises(ValidationError) as exc_info:
            app(["build", "-l", "2.5", "all"])

        assert "requires" in str(exc_info.value).lower()

    def test_npm_install_save_dev_and_global_mutually_exclusive(
        self, console: MockConsole
    ):
        """Test npm --save-dev and --global are mutually exclusive."""
        app = App("npm", console=console)

        @app.command()
        def install(
            packages: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            save_dev: Annotated[bool, "-D"] = False,
            global_install: Annotated[bool, "-g"] = False,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print("[install] invoked")
            if packages:
                console.print(f"[install] packages={packages!r}")
            if save_dev:
                console.print("[install] save_dev=True")
            if global_install:
                console.print("[install] global=True")

        # Add validation to the command instance
        install.validate(
            MutuallyExclusive(parameter_names=("save_dev", "global_install"))
        )

        with pytest.raises(ValidationError) as exc_info:
            app(["install", "-D", "-g", "typescript"])

        assert "mutually exclusive" in str(exc_info.value).lower()

    def test_mysql_raw_conflicts_with_tables(self, console: MockConsole):
        """Test mysql -r conflicts with inline table names."""
        app = App("mysql", console=console)

        @app.command()
        def mysql(
            tables: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            raw: Annotated[bool, "-r"] = False,
            database: Annotated[str | None, "-D"] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            if database:
                console.print(f"[mysql] database={database}")
            if raw:
                console.print("[mysql] raw=True")
            if tables:
                console.print(f"[mysql] tables={tables!r}")

        # Add validation to the command instance
        mysql.validate(ConflictsWith(parameter_names=("raw", "tables")))

        with pytest.raises(ValidationError) as exc_info:
            app(["mysql", "-D", "mydb", "-r", "users", "posts"])

        assert "conflict" in str(exc_info.value).lower()
