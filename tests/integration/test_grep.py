"""Integration tests for grep-like CLI patterns from spec.

This module implements all test scenarios from specs/cli_test_specs.md
for the grep command, validating fundamental CLI parsing capabilities.

Spec scenarios covered: 14
- Basic short and long option forms
- Simple flags (zero arity)
- Value options (single arity)
- Variable arity positionals (PATTERN FILE...)
- Combined short options (-rin)
- Equals syntax (--color=auto)
- Repeatable options (--include)

Note: This file intentionally uses patterns that trigger linting warnings:
- FBT002: Boolean arguments are part of the CLI API being tested
- ARG001: Unused parameters are part of CLI signature validation
- TC001: MockConsole is used at runtime, not just for type checking
"""

# ruff: noqa: TC001, FBT002, ARG001

from typing import Annotated

from aclaf import App
from aclaf.console import MockConsole
from aclaf.metadata import Collect, ZeroOrMore


class TestBasicPatterns:
    """Basic pattern matching - required and optional positionals."""

    def test_basic_pattern_search(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str, files: Annotated[tuple[str, ...], ZeroOrMore()] = ()
        ):
            console.print(f"[grep] pattern={pattern}")
            if files:
                console.print(f"[grep] files={files!r}")

        app(["grep", "error"])

        output = console.get_output()
        assert "[grep] pattern=error" in output

    def test_pattern_with_single_file(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str, files: Annotated[tuple[str, ...], ZeroOrMore()] = ()
        ):
            console.print(f"[grep] pattern={pattern}")
            if files:
                console.print(f"[grep] files={files!r}")

        app(["grep", "error", "app.log"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] files=('app.log',)" in output

    def test_pattern_with_multiple_files(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str, files: Annotated[tuple[str, ...], ZeroOrMore()] = ()
        ):
            console.print(f"[grep] pattern={pattern}")
            if files:
                console.print(f"[grep] files={files!r}")

        app(["grep", "error", "app.log", "error.log", "debug.log"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] files=('app.log', 'error.log', 'debug.log')" in output


class TestShortOptions:
    """Basic short option flags and value options."""

    def test_ignore_case_flag_short(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            ignore_case: Annotated[bool, "-i"] = False,
        ):
            console.print(f"[grep] pattern={pattern}")
            if ignore_case:
                console.print("[grep] ignore_case=True")

        app(["grep", "-i", "error", "file.txt"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] ignore_case=True" in output

    def test_invert_match_flag(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            invert_match: Annotated[bool, "-v"] = False,
        ):
            console.print(f"[grep] pattern={pattern}")
            if invert_match:
                console.print("[grep] invert_match=True")

        app(["grep", "-v", "exclude", "file.txt"])

        output = console.get_output()
        assert "[grep] pattern=exclude" in output
        assert "[grep] invert_match=True" in output

    def test_line_number_flag(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            line_number: Annotated[bool, "-n"] = False,
        ):
            console.print(f"[grep] pattern={pattern}")
            if line_number:
                console.print("[grep] line_number=True")

        app(["grep", "-n", "error"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] line_number=True" in output

    def test_recursive_flag(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            recursive: Annotated[bool, "-r"] = False,
        ):
            console.print(f"[grep] pattern={pattern}")
            if recursive:
                console.print("[grep] recursive=True")

        app(["grep", "-r", "pattern", "src/"])

        output = console.get_output()
        assert "[grep] pattern=pattern" in output
        assert "[grep] recursive=True" in output

    def test_extended_regexp_flag(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            extended_regexp: Annotated[bool, "-E"] = False,
        ):
            console.print(f"[grep] pattern={pattern}")
            if extended_regexp:
                console.print("[grep] extended_regexp=True")

        app(["grep", "-E", "(error|warning)", "file.txt"])

        output = console.get_output()
        assert "[grep] pattern=(error|warning)" in output
        assert "[grep] extended_regexp=True" in output

    def test_context_after_option(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            after_context: Annotated[int | None, "-A"] = None,
        ):
            console.print(f"[grep] pattern={pattern}")
            if after_context is not None:
                console.print(f"[grep] after_context={after_context}")

        app(["grep", "-A", "3", "error", "file.txt"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] after_context=3" in output


class TestLongOptions:
    """Long option forms with and without equals syntax."""

    def test_ignore_case_flag_long(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            ignore_case: Annotated[bool, "-i"] = False,
        ):
            console.print(f"[grep] pattern={pattern}")
            if ignore_case:
                console.print("[grep] ignore_case=True")

        app(["grep", "--ignore-case", "error", "file.txt"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] ignore_case=True" in output

    def test_line_number_flag_long(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            line_number: Annotated[bool, "-n"] = False,
        ):
            console.print(f"[grep] pattern={pattern}")
            if line_number:
                console.print("[grep] line_number=True")

        app(["grep", "--line-number", "error"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] line_number=True" in output

    def test_max_count_with_equals(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            max_count: Annotated[int | None, "-m"] = None,
        ):
            console.print(f"[grep] pattern={pattern}")
            if max_count is not None:
                console.print(f"[grep] max_count={max_count}")

        app(["grep", "--max-count=5", "error", "file.txt"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] max_count=5" in output


class TestCombinedOptions:
    """Combined short option handling."""

    def test_combined_short_options(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            recursive: Annotated[bool, "-r"] = False,
            ignore_case: Annotated[bool, "-i"] = False,
            line_number: Annotated[bool, "-n"] = False,
        ):
            console.print(f"[grep] pattern={pattern}")
            if recursive:
                console.print("[grep] recursive=True")
            if ignore_case:
                console.print("[grep] ignore_case=True")
            if line_number:
                console.print("[grep] line_number=True")

        app(["grep", "-rin", "error", "src/"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] recursive=True" in output
        assert "[grep] ignore_case=True" in output
        assert "[grep] line_number=True" in output

    def test_combined_with_value_option(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            ignore_case: Annotated[bool, "-i"] = False,
            line_number: Annotated[bool, "-n"] = False,
            after_context: Annotated[int | None, "-A"] = None,
        ):
            console.print(f"[grep] pattern={pattern}")
            if ignore_case:
                console.print("[grep] ignore_case=True")
            if line_number:
                console.print("[grep] line_number=True")
            if after_context is not None:
                console.print(f"[grep] after_context={after_context}")

        app(["grep", "-in", "-A", "2", "error", "file.txt"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] ignore_case=True" in output
        assert "[grep] line_number=True" in output
        assert "[grep] after_context=2" in output


class TestRepeatableOptions:
    """Options that can appear multiple times."""

    def test_file_pattern_inclusion(self, console: MockConsole):
        app = App("grep", console=console)

        @app.command()
        def grep(  # pyright: ignore[reportUnusedFunction]
            pattern: str,
            files: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            include: Annotated[tuple[str, ...], "--include", Collect()] = (),
        ):
            console.print(f"[grep] pattern={pattern}")
            if include:
                console.print(f"[grep] include={include!r}")

        app(["grep", "--include=*.py", "--include=*.txt", "error", "src/"])

        output = console.get_output()
        assert "[grep] pattern=error" in output
        assert "[grep] include=('*.py', '*.txt')" in output
