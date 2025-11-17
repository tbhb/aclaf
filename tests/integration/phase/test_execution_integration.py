"""Integration tests for execution phase transitions.

Tests end-to-end: CLI args → parsed → converted → validated → executed → response.
"""

# ruff: noqa: FBT002, TC001

import asyncio
from typing import Annotated

import pytest
from annotated_types import Gt

from aclaf import App
from aclaf.console import MockConsole
from aclaf.metadata import Arg, AtLeastOne, ZeroOrMore
from aclaf.types import PositiveInt


class TestParameterInjection:
    def test_validated_int_reaches_handler(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            assert isinstance(value, int)
            assert value == 42
            console.print(f"value={value} type={type(value).__name__}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42 type=int" in output

    def test_validated_str_length_reaches_handler(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: str):  # pyright: ignore[reportUnusedFunction]
            assert isinstance(name, str)
            assert len(name) == 5
            console.print(f"name={name} len={len(name)}")

        app(["cmd", "alice"])

        output = console.get_output()
        assert "name=alice len=5" in output

    def test_multiple_parameter_injection(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            name: str, count: int, flag: Annotated[bool, Arg()] = False
        ):
            assert isinstance(name, str)
            assert isinstance(count, int)
            assert isinstance(flag, bool)
            console.print(f"name={name} count={count} flag={flag}")

        app(["cmd", "test", "5", "true"])

        output = console.get_output()
        assert "name=test count=5 flag=True" in output


class TestOptionalHandling:
    def test_optional_with_none(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int | None = None):  # pyright: ignore[reportUnusedFunction]
            assert value is None
            console.print(f"value={value}")

        app(["cmd"])

        output = console.get_output()
        assert "value=None" in output

    def test_optional_with_value(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int | None = None):  # pyright: ignore[reportUnusedFunction]
            assert isinstance(value, int)
            assert value == 42
            console.print(f"value={value}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42" in output


class TestVariadicHandling:
    def test_variadic_all_values(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            values: Annotated[tuple[int, ...], ZeroOrMore()] = ()
        ):
            assert isinstance(values, tuple)
            assert all(isinstance(v, int) for v in values)
            console.print(f"values={values!r} count={len(values)}")

        app(["cmd", "1", "2", "3"])

        output = console.get_output()
        assert "values=(1, 2, 3) count=3" in output

    def test_variadic_at_least_one(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            values: Annotated[tuple[str, ...], AtLeastOne()]
        ):
            assert isinstance(values, tuple)
            assert len(values) > 0
            console.print(f"values={values!r}")

        app(["cmd", "a", "b"])

        output = console.get_output()
        assert "values=('a', 'b')" in output


class TestSubcommandExecution:
    def test_subcommand_params_validated(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def parent():
            console.print("[parent] invoked")

        @parent.command()
        def child(value: PositiveInt):  # pyright: ignore[reportUnusedFunction]
            assert isinstance(value, int)
            assert value > 0
            console.print(f"[child] value={value}")

        app(["parent", "child", "42"])

        output = console.get_output()
        assert "[parent] invoked" in output
        assert "[child] value=42" in output

    def test_global_and_local_params(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def parent(global_val: int = 0):
            assert isinstance(global_val, int)
            console.print(f"[parent] global_val={global_val}")

        @parent.command()
        def child(local_val: int):  # pyright: ignore[reportUnusedFunction]
            assert isinstance(local_val, int)
            console.print(f"[child] local_val={local_val}")

        app(["parent", "10", "child", "20"])

        output = console.get_output()
        assert "[parent] global_val=10" in output
        assert "[child] local_val=20" in output


class TestDefaultValues:
    def test_default_value_used(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int = 100):  # pyright: ignore[reportUnusedFunction]
            assert isinstance(value, int)
            assert value == 100
            console.print(f"value={value}")

        app(["cmd"])

        output = console.get_output()
        assert "value=100" in output

    def test_default_value_overridden(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int = 100):  # pyright: ignore[reportUnusedFunction]
            assert isinstance(value, int)
            assert value == 42
            console.print(f"value={value}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42" in output


class TestReturnValues:
    def test_none_return(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd():  # pyright: ignore[reportUnusedFunction]
            console.print("executed")

        result = app(["cmd"])

        output = console.get_output()
        assert "executed" in output
        assert result is None

    @pytest.mark.skip(
        reason="Return value capture not yet implemented - framework returns None"
    )
    def test_int_return(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd() -> int:  # pyright: ignore[reportUnusedFunction]
            console.print("executed")
            return 42

        result = app(["cmd"])

        output = console.get_output()
        assert "executed" in output
        assert result == 42

    @pytest.mark.skip(
        reason="Return value capture not yet implemented - framework returns None"
    )
    def test_str_return(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd() -> str:  # pyright: ignore[reportUnusedFunction]
            console.print("executed")
            return "success"

        result = app(["cmd"])

        output = console.get_output()
        assert "executed" in output
        assert result == "success"


class TestAsyncExecution:
    def test_async_handler_executes(self, console: MockConsole):
        # Framework auto-detects async handlers, no is_async flag needed
        app = App("test", console=console)

        @app.command()
        async def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            await asyncio.sleep(0.001)  # Simulate async work
            console.print(f"value={value}")

        result = app(["cmd", "42"])

        output = console.get_output()
        assert "value=42" in output
        assert result is None

    @pytest.mark.skip(
        reason="Async return value capture not yet implemented - framework returns None"
    )
    def test_async_handler_return_value(self, console: MockConsole):
        # Framework auto-detects async handlers
        app = App("test", console=console)

        @app.command()
        async def cmd() -> int:  # pyright: ignore[reportUnusedFunction]
            await asyncio.sleep(0.001)
            return 42

        result = app(["cmd"])

        assert result == 42


class TestTypePreservation:
    def test_validated_types_preserved(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Gt(0)]):  # pyright: ignore[reportUnusedFunction]
            # Value should still be int after validation
            assert isinstance(value, int)
            assert not isinstance(value, str)
            console.print(f"value={value} type={type(value).__name__}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42 type=int" in output

    def test_execution_receives_python_types(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            name: str, count: int, rate: float, flag: Annotated[bool, Arg()]
        ):
            assert isinstance(name, str)
            assert isinstance(count, int)
            assert isinstance(rate, float)
            assert isinstance(flag, bool)
            console.print("all types correct")

        app(["cmd", "test", "10", "3.14", "true"])

        output = console.get_output()
        assert "all types correct" in output


class TestErrorHandling:
    def test_execution_with_exception(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd():  # pyright: ignore[reportUnusedFunction]
            msg = "intentional error"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="intentional error"):
            app(["cmd"])

    def test_exception_includes_parameter_context(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            if value < 0:
                msg = f"value must be positive, got {value}"
                raise ValueError(msg)
            console.print(f"value={value}")

        app(["cmd", "42"])
        output = console.get_output()
        assert "value=42" in output

        console.clear()
        with pytest.raises(ValueError, match="value must be positive"):
            app(["cmd", "-5"])
