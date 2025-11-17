"""Integration tests for error propagation through all phases.

Tests end-to-end error handling: errors at each phase → surfaced correctly.
"""

# ruff: noqa: TC001

from typing import Annotated

import pytest
from annotated_types import Gt, Interval

from aclaf import App
from aclaf.console import MockConsole
from aclaf.exceptions import ValidationError
from aclaf.metadata import Arg, AtLeastOne
from aclaf.parser.exceptions import (
    InsufficientPositionalArgumentsError,
    UnknownOptionError,
)
from aclaf.types import PositiveInt


class TestParsingErrors:
    def test_unknown_option_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd():  # pyright: ignore[reportUnusedFunction]
            console.print("executed")

        with pytest.raises(UnknownOptionError) as exc_info:
            app(["cmd", "-x"])

        assert "-x" in str(exc_info.value)

    def test_missing_required_positional_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name}")

        with pytest.raises(InsufficientPositionalArgumentsError):
            app(["cmd"])

    def test_missing_required_option_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: Annotated[str, "--name"]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name}")

        # Missing required options raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            app(["cmd"])

        # Verify error message indicates the parameter is required
        error_msg = str(exc_info.value)
        assert "name" in error_msg
        assert "required" in error_msg.lower()

    def test_missing_variadic_at_least_one(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            values: Annotated[tuple[str, ...], AtLeastOne()]
        ):
            console.print(f"values={values!r}")

        with pytest.raises(InsufficientPositionalArgumentsError):
            app(["cmd"])


class TestConversionErrors:
    def test_int_conversion_error_message(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        # Conversion errors are wrapped in ValidationError
        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "abc"])

        error_msg = str(exc_info.value)
        assert "abc" in error_msg
        assert "value" in error_msg

    def test_float_conversion_error_message(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: float):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        # Conversion errors are wrapped in ValidationError
        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "not-a-number"])

        error_msg = str(exc_info.value)
        assert "not-a-number" in error_msg
        assert "value" in error_msg

    def test_bool_conversion_error_message(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            flag: Annotated[bool, Arg()]
        ):
            console.print(f"flag={flag}")

        # Conversion errors are wrapped in ValidationError
        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "maybe"])

        error_msg = str(exc_info.value)
        assert "maybe" in error_msg


class TestValidationErrors:
    def test_positive_int_validation_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: PositiveInt):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "-5"])

        error_msg = str(exc_info.value)
        assert "must be greater than" in error_msg or ">" in error_msg

    def test_interval_validation_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)]
        ):
            console.print(f"value={value}")

        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "15"])

        error_msg = str(exc_info.value)
        assert "must be less than or equal to" in error_msg or "<=" in error_msg

    def test_gt_validation_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Gt(0)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "0"])

        error_msg = str(exc_info.value)
        assert "0" in error_msg


class TestExecutionErrors:
    def test_execution_exception_propagates(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd():  # pyright: ignore[reportUnusedFunction]
            msg = "execution failed"
            raise RuntimeError(msg)

        with pytest.raises(RuntimeError, match="execution failed"):
            app(["cmd"])

    def test_execution_error_with_parameter_context(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            if value == 0:
                msg = "division by zero"
                raise ZeroDivisionError(msg)
            console.print(f"result={100 / value}")

        with pytest.raises(ZeroDivisionError, match="division by zero"):
            app(["cmd", "0"])


class TestErrorContext:
    def test_error_includes_parameter_name(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(count: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"count={count}")

        # Conversion errors are wrapped in ValidationError
        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "abc"])

        error_msg = str(exc_info.value)
        # Error should reference the parameter and value that failed
        assert "count" in error_msg
        assert "abc" in error_msg

    def test_error_includes_value_attempted(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: PositiveInt):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "-10"])

        error_msg = str(exc_info.value)
        # Error should describe the constraint violation
        assert "greater than" in error_msg or ">" in error_msg


class TestSubcommandErrors:
    def test_subcommand_parsing_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def parent():
            console.print("[parent] invoked")

        @parent.command()
        def child(value: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[child] value={value}")

        # Conversion errors in subcommands are wrapped in ValidationError
        with pytest.raises(ValidationError):
            app(["parent", "child", "abc"])

    def test_subcommand_validation_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def parent():
            console.print("[parent] invoked")

        @parent.command()
        def child(value: PositiveInt):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[child] value={value}")

        with pytest.raises(ValidationError):
            app(["parent", "child", "-5"])

    def test_subcommand_execution_error(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def parent():
            console.print("[parent] invoked")

        @parent.command()
        def child():  # pyright: ignore[reportUnusedFunction]
            msg = "child error"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="child error"):
            app(["parent", "child"])


class TestMultipleErrors:
    def test_first_error_stops_processing(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value1: int, value2: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value1={value1} value2={value2}")

        # First value fails conversion
        with pytest.raises(ValidationError) as exc_info:
            app(["cmd", "abc", "def"])

        # Error should mention the first failing parameter
        error_msg = str(exc_info.value)
        assert "value1" in error_msg or "abc" in error_msg


class TestErrorRecovery:
    def test_error_in_one_invocation_does_not_affect_next(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: int):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        # First invocation fails with conversion error
        with pytest.raises(ValidationError):
            app(["cmd", "abc"])

        # Second invocation should succeed
        console.clear()
        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42" in output
