"""Integration tests for tar-like CLI patterns from spec.

This module implements all test scenarios from specs/cli_test_specs.md
for the tar command, validating bundled option CLI parsing capabilities.

Spec scenarios covered: 11
- Bundled short options with hyphens (-cvf, -xvf)
- Bundled operation+modifier letters
- File argument position based on 'f' modifier
- Separate options with individual hyphens
- Modern GNU long options (--create, --file=)
- Compression modifiers (z, j)
- Exclude patterns (repeatable)

Note: Traditional tar syntax without hyphens (cvf) is not supported by Aclaf,
which follows standard POSIX conventions requiring option prefixes.

This file intentionally uses patterns that trigger linting warnings:
- FBT002: Boolean arguments are part of the CLI API being tested
- ARG001: Unused parameters are part of CLI signature validation
- TC001: MockConsole is used at runtime, not just for type checking
"""

# ruff: noqa: TC001, FBT002, ARG001

from typing import Annotated

from aclaf import App
from aclaf.console import MockConsole
from aclaf.metadata import AtLeastOne, Collect, ZeroOrMore


class TestBundledSyntax:
    """Bundled short option syntax (hyphen-prefixed)."""

    def test_create_archive_bundled_style(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], AtLeastOne()],
            create: Annotated[bool, "-c"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
        ):
            if create:
                console.print("[tar] create=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            console.print(f"[tar] files={files!r}")

        app(["tar", "-cvf", "archive.tar", "file1", "file2"])

        output = console.get_output()
        assert "[tar] create=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar" in output
        assert "[tar] files=('file1', 'file2')" in output

    def test_extract_archive_bundled(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            extract: Annotated[bool, "-x"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
        ):
            if extract:
                console.print("[tar] extract=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            if files:
                console.print(f"[tar] files={files!r}")

        app(["tar", "-xvf", "archive.tar"])

        output = console.get_output()
        assert "[tar] extract=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar" in output

    def test_list_archive_contents(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            list_contents: Annotated[bool, "-t"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
        ):
            if list_contents:
                console.print("[tar] list_contents=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")

        app(["tar", "-tvf", "archive.tar"])

        output = console.get_output()
        assert "[tar] list_contents=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar" in output


class TestModernSyntax:
    """Modern tar syntax with leading hyphens."""

    def test_create_archive_with_hyphen(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], AtLeastOne()],
            create: Annotated[bool, "-c"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
        ):
            if create:
                console.print("[tar] create=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            console.print(f"[tar] files={files!r}")

        app(["tar", "-cvf", "archive.tar", "file1", "file2"])

        output = console.get_output()
        assert "[tar] create=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar" in output
        assert "[tar] files=('file1', 'file2')" in output

    def test_separate_options(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], AtLeastOne()],
            create: Annotated[bool, "-c"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
        ):
            if create:
                console.print("[tar] create=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            console.print(f"[tar] files={files!r}")

        app(["tar", "-c", "-v", "-f", "archive.tar", "file1", "file2"])

        output = console.get_output()
        assert "[tar] create=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar" in output
        assert "[tar] files=('file1', 'file2')" in output


class TestCompressionOptions:
    """Compression modifiers for tar operations."""

    def test_create_gzip_archive(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], AtLeastOne()],
            create: Annotated[bool, "-c"] = False,
            gzip: Annotated[bool, "-z"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
        ):
            if create:
                console.print("[tar] create=True")
            if gzip:
                console.print("[tar] gzip=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            console.print(f"[tar] files={files!r}")

        app(["tar", "-czvf", "archive.tar.gz", "directory/"])

        output = console.get_output()
        assert "[tar] create=True" in output
        assert "[tar] gzip=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar.gz" in output
        assert "[tar] files=('directory/',)" in output

    def test_create_bzip2_archive(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], AtLeastOne()],
            create: Annotated[bool, "-c"] = False,
            bzip2: Annotated[bool, "-j"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
        ):
            if create:
                console.print("[tar] create=True")
            if bzip2:
                console.print("[tar] bzip2=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            console.print(f"[tar] files={files!r}")

        app(["tar", "-cjvf", "archive.tar.bz2", "files/"])

        output = console.get_output()
        assert "[tar] create=True" in output
        assert "[tar] bzip2=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar.bz2" in output
        assert "[tar] files=('files/',)" in output

    def test_extract_with_directory(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            extract: Annotated[bool, "-x"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
            directory: Annotated[str | None, "-C"] = None,
        ):
            if extract:
                console.print("[tar] extract=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            if directory:
                console.print(f"[tar] directory={directory}")

        app(["tar", "-xvf", "archive.tar", "-C", "/destination/"])

        output = console.get_output()
        assert "[tar] extract=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar" in output
        assert "[tar] directory=/destination/" in output


class TestLongOptions:
    """GNU-style long options."""

    def test_archive_with_long_options(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], AtLeastOne()],
            create: Annotated[bool, "-c"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
        ):
            if create:
                console.print("[tar] create=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            console.print(f"[tar] files={files!r}")

        app(["tar", "--create", "--verbose", "--file=archive.tar", "file1", "file2"])

        output = console.get_output()
        assert "[tar] create=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar" in output
        assert "[tar] files=('file1', 'file2')" in output

    def test_exclude_patterns(self, console: MockConsole):
        app = App("tar", console=console)

        @app.command()
        def tar(  # pyright: ignore[reportUnusedFunction]
            files: Annotated[tuple[str, ...], AtLeastOne()],
            create: Annotated[bool, "-c"] = False,
            verbose: Annotated[bool, "-v"] = False,
            file: Annotated[str | None, "-f"] = None,
            exclude: Annotated[tuple[str, ...], "--exclude", Collect()] = (),
        ):
            if create:
                console.print("[tar] create=True")
            if verbose:
                console.print("[tar] verbose=True")
            if file:
                console.print(f"[tar] file={file}")
            if exclude:
                console.print(f"[tar] exclude={exclude!r}")
            console.print(f"[tar] files={files!r}")

        app(
            [
                "tar",
                "-cvf",
                "archive.tar",
                "--exclude=*.log",
                "--exclude=*.tmp",
                "directory/",
            ]
        )

        output = console.get_output()
        assert "[tar] create=True" in output
        assert "[tar] verbose=True" in output
        assert "[tar] file=archive.tar" in output
        assert "[tar] exclude=('*.log', '*.tmp')" in output
        assert "[tar] files=('directory/',)" in output
