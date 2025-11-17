"""Integration tests for validation phase transitions.

Tests end-to-end: CLI args → parsed → converted → validated → verified.
"""

# ruff: noqa: TC001

from typing import Annotated

import pytest
from annotated_types import Ge, Gt, Interval, Le, Lt, MaxLen, MinLen, MultipleOf

from aclaf import App
from aclaf.console import MockConsole
from aclaf.exceptions import ValidationError
from aclaf.metadata import ZeroOrMore
from aclaf.types import PositiveInt


class TestIntervalValidator:
    def test_interval_validator_within_bounds(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)]
        ):
            console.print(f"value={value}")

        app(["cmd", "5"])

        output = console.get_output()
        assert "value=5" in output

    def test_interval_validator_lower_bound(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)]
        ):
            console.print(f"value={value}")

        app(["cmd", "0"])

        output = console.get_output()
        assert "value=0" in output

    def test_interval_validator_upper_bound(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)]
        ):
            console.print(f"value={value}")

        app(["cmd", "10"])

        output = console.get_output()
        assert "value=10" in output

    def test_interval_validator_below_lower(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)]
        ):
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "-5"])

    def test_interval_validator_above_upper(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)]
        ):
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "15"])


class TestMinLenValidator:
    def test_min_len_validator_string_valid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: Annotated[str, MinLen(3)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name}")

        app(["cmd", "hello"])

        output = console.get_output()
        assert "name=hello" in output

    def test_min_len_validator_string_exact(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: Annotated[str, MinLen(3)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name}")

        app(["cmd", "abc"])

        output = console.get_output()
        assert "name=abc" in output

    def test_min_len_validator_string_invalid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: Annotated[str, MinLen(3)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name}")

        with pytest.raises(ValidationError):
            app(["cmd", "hi"])

    def test_min_len_validator_list_valid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            values: Annotated[tuple[int, ...], MinLen(2), ZeroOrMore()] = ()
        ):
            console.print(f"values={values!r}")

        app(["cmd", "1", "2", "3"])

        output = console.get_output()
        assert "values=(1, 2, 3)" in output


class TestMaxLenValidator:
    def test_max_len_validator_string_valid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: Annotated[str, MaxLen(10)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name}")

        app(["cmd", "hello"])

        output = console.get_output()
        assert "name=hello" in output

    def test_max_len_validator_string_exact(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: Annotated[str, MaxLen(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name}")

        app(["cmd", "hello"])

        output = console.get_output()
        assert "name=hello" in output

    def test_max_len_validator_string_invalid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(name: Annotated[str, MaxLen(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"name={name}")

        with pytest.raises(ValidationError):
            app(["cmd", "verylongstring"])

    def test_max_len_validator_list_valid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            values: Annotated[tuple[int, ...], MaxLen(5), ZeroOrMore()] = ()
        ):
            console.print(f"values={values!r}")

        app(["cmd", "1", "2"])

        output = console.get_output()
        assert "values=(1, 2)" in output


class TestPositiveIntTypeAlias:
    def test_positive_int_type_alias_valid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: PositiveInt):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "42"])

        output = console.get_output()
        assert "value=42" in output

    def test_positive_int_type_alias_zero(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: PositiveInt):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "0"])

    def test_positive_int_type_alias_negative(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: PositiveInt):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "-5"])


class TestComparisonValidators:
    def test_ge_validator_equal(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Ge(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "5"])

        output = console.get_output()
        assert "value=5" in output

    def test_ge_validator_greater(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Ge(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "10"])

        output = console.get_output()
        assert "value=10" in output

    def test_gt_validator_not_equal(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Gt(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "5"])

    def test_gt_validator_greater(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Gt(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "6"])

        output = console.get_output()
        assert "value=6" in output

    def test_le_validator_equal(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Le(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "5"])

        output = console.get_output()
        assert "value=5" in output

    def test_le_validator_less(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Le(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "3"])

        output = console.get_output()
        assert "value=3" in output

    def test_lt_validator_not_equal(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Lt(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "5"])

    def test_lt_validator_less(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, Lt(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "4"])

        output = console.get_output()
        assert "value=4" in output


class TestMultipleOfValidator:
    def test_multiple_of_validator_valid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, MultipleOf(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "10"])

        output = console.get_output()
        assert "value=10" in output

    def test_multiple_of_validator_zero(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, MultipleOf(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        app(["cmd", "0"])

        output = console.get_output()
        assert "value=0" in output

    def test_multiple_of_validator_invalid(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(value: Annotated[int, MultipleOf(5)]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "11"])


class TestMultipleValidators:
    def test_multiple_validators_all_pass(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Gt(0), Le(100), MultipleOf(5)]
        ):
            console.print(f"value={value}")

        app(["cmd", "50"])

        output = console.get_output()
        assert "value=50" in output

    def test_multiple_validators_first_fails(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Gt(0), Le(100), MultipleOf(5)]
        ):
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "0"])

    def test_multiple_validators_second_fails(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Gt(0), Le(100), MultipleOf(5)]
        ):
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "101"])

    def test_multiple_validators_third_fails(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Gt(0), Le(100), MultipleOf(5)]
        ):
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "51"])


class TestValidationWithOptional:
    def test_validation_skips_none_for_optional(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)] | None = None
        ):
            console.print(f"value={value}")

        app(["cmd"])

        output = console.get_output()
        assert "value=None" in output

    def test_validation_applies_with_value(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)] | None = None
        ):
            console.print(f"value={value}")

        app(["cmd", "5"])

        output = console.get_output()
        assert "value=5" in output

    @pytest.mark.xfail(
        reason=(
            "Framework bug: validation not applied to union types with None - "
            "validation is skipped for optional parameters"
        )
    )
    def test_validation_fails_with_invalid_value(self, console: MockConsole):
        app = App("test", console=console)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: Annotated[int, Interval(ge=0, le=10)] | None = None
        ):
            console.print(f"value={value}")

        with pytest.raises(ValidationError):
            app(["cmd", "15"])
