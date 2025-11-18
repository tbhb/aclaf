"""Integration tests for conversion phase transitions.

Tests end-to-end: CLI args → parsed → converted → verified.
"""

# ruff: noqa: TC001

from enum import Enum
from pathlib import Path
from typing import Annotated

import pytest

from aclaf import App
from aclaf.console import MockConsole
from aclaf.metadata import Arg, ZeroOrMore
from aclaf.types import PositiveInt
from aclaf.validation import ValidationError


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class TestStringConversion:
    def test_str_conversion_simple(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name} type={type(name).__name__}")

        app(["cmd", "alice"])

        output = console.get_output()
        assert "name=alice type=str" in output

    def test_str_conversion_with_spaces(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(message: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"message={message}")

        app(["cmd", "hello world"])

        output = console.get_output()
        assert "message=hello world" in output

    def test_str_conversion_empty(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: str = ""):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value!r}")

        app(["cmd"])

        output = console.get_output()
        assert "value=''" in output


class TestIntConversion:
    def test_int_conversion_valid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(count: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"count={count} type={type(count).__name__}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "count=42 type=int" in output

    def test_int_conversion_negative(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "-10"])

        output = console.get_output()
        assert "value=-10" in output

    def test_int_conversion_zero(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "0"])

        output = console.get_output()
        assert "value=0" in output

    def test_int_conversion_invalid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        # Conversion errors are wrapped in ValidationError
        with pytest.raises(ValidationError):
            app(["cmd", "abc"])


class TestFloatConversion:
    def test_float_conversion_valid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: float):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value} type={type(value).__name__}")

        app(["cmd", "3.14"])

        output = console.get_output()
        assert "value=3.14 type=float" in output

    def test_float_conversion_scientific(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: float):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "1.5e-10"])

        output = console.get_output()
        assert "value=1.5e-10" in output

    def test_float_conversion_integer(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: float):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value} type={type(value).__name__}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42.0 type=float" in output


class TestBoolConversion:
    def test_bool_conversion_true_variants(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            flag: Annotated[bool, Arg()],
        ):
            console.print(f"flag={flag}")

        for value in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            console.clear()
            app(["cmd", value])
            output = console.get_output()
            assert "flag=True" in output, f"Failed for value: {value}"

    def test_bool_conversion_false_variants(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            flag: Annotated[bool, Arg()],
        ):
            console.print(f"flag={flag}")

        for value in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF"]:
            console.clear()
            app(["cmd", value])
            output = console.get_output()
            assert "flag=False" in output, f"Failed for value: {value}"

    def test_bool_conversion_invalid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            flag: Annotated[bool, Arg()],
        ):
            console.print(f"flag={flag}")

        # Invalid bool values raise ValidationError (wrapped conversion error)
        with pytest.raises(ValidationError):
            app(["cmd", "maybe"])


class TestPathConversion:
    def test_path_conversion_relative(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(file: Path):  # pyright: ignore[reportUnusedFunction]
            console.print(f"file={file} type={type(file).__name__}")

        app(["cmd", "./file.txt"])

        output = console.get_output()
        # Path returns PosixPath on Unix/macOS, WindowsPath on Windows
        assert (
            "file=file.txt type=PosixPath" in output
            or "file=file.txt type=WindowsPath" in output
        )

    def test_path_conversion_absolute(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(file: Path):  # pyright: ignore[reportUnusedFunction]
            console.print(f"file={file} type={type(file).__name__}")

        app(["cmd", "/tmp/file"])  # noqa: S108

        output = console.get_output()
        # Path returns PosixPath on Unix/macOS, WindowsPath on Windows
        assert (
            "file=/tmp/file type=PosixPath" in output
            or "file=\\tmp\\file type=WindowsPath" in output
        )


class TestEnumConversion:
    def test_enum_conversion_by_value(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(level: LogLevel):  # pyright: ignore[reportUnusedFunction]
            console.print(f"level={level.value} type={type(level).__name__}")

        app(["cmd", "debug"])

        output = console.get_output()
        assert "level=debug type=LogLevel" in output

    def test_enum_conversion_by_name(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(level: LogLevel):  # pyright: ignore[reportUnusedFunction]
            console.print(f"level={level.value}")

        app(["cmd", "DEBUG"])

        output = console.get_output()
        assert "level=debug" in output

    def test_enum_conversion_invalid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(level: LogLevel):  # pyright: ignore[reportUnusedFunction]
            console.print(f"level={level}")

        # Conversion errors are wrapped in ValidationError
        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "UNKNOWN"])

        # Verify the error message contains the conversion error details
        error_msg = str(exc_info.value)
        assert "UNKNOWN" in error_msg
        assert "LogLevel" in error_msg


class TestTupleConversion:
    def test_tuple_conversion_variadic(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            values: Annotated[tuple[str, ...], ZeroOrMore()] = (),
        ):
            console.print(f"values={values!r} type={type(values).__name__}")

        app(["cmd", "a", "b", "c"])

        output = console.get_output()
        assert "values=('a', 'b', 'c') type=tuple" in output

    def test_tuple_conversion_int_elements(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            values: Annotated[tuple[int, ...], ZeroOrMore()] = (),
        ):
            console.print(f"values={values!r}")

        app(["cmd", "1", "2", "3"])

        output = console.get_output()
        assert "values=(1, 2, 3)" in output


class TestOptionalConversion:
    def test_optional_conversion_none(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int | None = None):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd"])

        output = console.get_output()
        assert "value=None" in output

    def test_optional_conversion_value(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int | None = None):  # pyright: ignore[reportUnusedFunction]
            type_name = type(value).__name__ if value is not None else "None"
            console.print(f"value={value} type={type_name}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42 type=int" in output


class TestUnionConversion:
    def test_union_conversion_int_first(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int | str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value} type={type(value).__name__}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42 type=int" in output

    def test_union_conversion_str_fallback(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int | str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value} type={type(value).__name__}")

        app(["cmd", "abc"])

        output = console.get_output()
        assert "value=abc type=str" in output


class TestTypeAliasConversion:
    def test_positive_int_type_alias(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: PositiveInt):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value} type={type(value).__name__}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42 type=int" in output
