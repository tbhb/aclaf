"""Integration tests for negative number handling using the App API.

This module tests the parsing of negative numbers (e.g., -1, -2.5, -1.5e-10)
and complex numbers (e.g., -3+4j) in CLI arguments using the high-level App API.
Negative numbers are inherently ambiguous with options (is `-1` a flag or a number?),
so these tests validate that `allow_negative_numbers=True` in ParserConfiguration
correctly disambiguates based on whether a matching option is registered.

Test coverage includes:
- Calculator-like CLIs with negative operands
- Scientific computing with scientific notation and complex numbers
- Data processing with negative ranges and thresholds
- Financial applications with negative amounts
- Mixed scenarios where options take precedence over negative numbers
- Edge cases like negative zero, pure imaginary numbers, trailing args

All tests use inline CLI construction to demonstrate isolated scenarios clearly.

Note: This file intentionally uses patterns that trigger linting warnings:
- FBT002: Boolean arguments are part of the CLI API being tested
- A002: Parameter names like 'min', 'max', 'range', 'input' shadow builtins but
  match actual CLI patterns
- TC001: MockConsole is used at runtime, not just for type checking
"""

# ruff: noqa: FBT002, A002, TC001

from typing import Annotated

from aclaf import App, Context
from aclaf.console import MockConsole
from aclaf.metadata import ZeroOrMore
from aclaf.parser import ParserConfiguration


class TestCalculatorLikeCLI:
    def test_add_with_negative_numbers(self, console: MockConsole):
        # Inline CLI construction - calculator with negative number support
        # Negative numbers (-10, -3) are treated as positional values, not options
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("calc", console=console, parser_config=parser_config)

        @app.command()
        def add(values: Annotated[tuple[str, ...], ZeroOrMore()] = ()):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[add] values={values!r}")

        app(["add", "-10", "5", "-3"])

        output = console.get_output()
        assert "[add] values=('-10', '5', '-3')" in output

    def test_multiply_with_options_and_negatives(self, console: MockConsole):
        # Inline CLI construction - multiply command with precision option
        # and negative values. --precision takes an option value, negative
        # floats are positionals
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("calc", console=console, parser_config=parser_config)

        @app.command()
        def multiply(  # pyright: ignore[reportUnusedFunction]
            values: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            precision: Annotated[str | None, "--precision"] = None,
        ):
            if precision:
                console.print(f"[multiply] precision={precision}")
            console.print(f"[multiply] values={values!r}")

        app(["multiply", "--precision", "2", "-5.5", "3.14"])

        output = console.get_output()
        assert "[multiply] precision=2" in output
        assert "[multiply] values=('-5.5', '3.14')" in output


class TestDataProcessingCLI:
    def test_filter_with_range(self, console: MockConsole):
        # Inline CLI construction - data filter with min/max range options
        # Negative numbers can be option values when explicitly assigned
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("process", console=console, parser_config=parser_config)

        @app.command()
        def process(  # pyright: ignore[reportUnusedFunction]
            file: str,
            min: Annotated[str | None, "--min"] = None,
            max: Annotated[str | None, "--max"] = None,
        ):
            console.print(f"[process] file={file}")
            if min:
                console.print(f"[process] min={min}")
            if max:
                console.print(f"[process] max={max}")

        app(["process", "--min", "-100", "--max", "100", "data.csv"])

        output = console.get_output()
        assert "[process] min=-100" in output
        assert "[process] max=100" in output
        assert "[process] file=data.csv" in output

    def test_threshold_with_scientific_notation(self, console: MockConsole):
        # Inline CLI construction - analyzer with scientific notation negative threshold
        # Negative scientific notation (e.g., -1.5e-10) is recognized as a number
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("analyze", console=console, parser_config=parser_config)

        @app.command()
        def analyze(  # pyright: ignore[reportUnusedFunction]
            input: str,
            threshold: Annotated[str | None, "--threshold"] = None,
        ):
            console.print(f"[analyze] input={input}")
            if threshold:
                console.print(f"[analyze] threshold={threshold}")

        app(["analyze", "--threshold", "-1.5e-10", "input.dat"])

        output = console.get_output()
        assert "[analyze] threshold=-1.5e-10" in output
        assert "[analyze] input=input.dat" in output


class TestScientificComputing:
    def test_simulation_with_multiple_params(self, console: MockConsole):
        # Inline CLI construction - scientific simulation with multiple
        # negative parameters. Demonstrates negative temps (absolute zero)
        # and negative time values
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("simulate", console=console, parser_config=parser_config)

        @app.command()
        def simulate(  # pyright: ignore[reportUnusedFunction]
            temp: Annotated[str | None, "--temp"] = None,
            pressure: Annotated[str | None, "--pressure"] = None,
            time: Annotated[str | None, "--time"] = None,
        ):
            if temp:
                console.print(f"[simulate] temp={temp}")
            if pressure:
                console.print(f"[simulate] pressure={pressure}")
            if time:
                console.print(f"[simulate] time={time}")

        app(
            [
                "simulate",
                "--temp",
                "-273.15",
                "--pressure",
                "1.0",
                "--time",
                "-0.5",
            ]
        )

        output = console.get_output()
        assert "[simulate] temp=-273.15" in output
        assert "[simulate] pressure=1.0" in output
        assert "[simulate] time=-0.5" in output

    def test_coordinate_system(self, console: MockConsole):
        # Inline CLI construction - 3D coordinate plotting with negative values
        # All three coordinates can be negative (representing all octants of 3D space)
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("plot", console=console, parser_config=parser_config)

        @app.command()
        def plot(  # pyright: ignore[reportUnusedFunction]
            x: str,
            y: str,
            z: str,
        ):
            console.print(f"[plot] x={x}")
            console.print(f"[plot] y={y}")
            console.print(f"[plot] z={z}")

        app(["plot", "-5.0", "-3.2", "10.5"])

        output = console.get_output()
        assert "[plot] x=-5.0" in output
        assert "[plot] y=-3.2" in output
        assert "[plot] z=10.5" in output


class TestFinancialCLI:
    def test_transaction_with_negative_amount(self, console: MockConsole):
        # Inline CLI construction - financial transaction recording
        # Negative amounts represent refunds or withdrawals
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("finance", console=console, parser_config=parser_config)

        @app.command()
        def finance(  # pyright: ignore[reportUnusedFunction]
            amount: Annotated[str | None, "--amount"] = None,
            description: Annotated[str | None, "--description"] = None,
        ):
            if amount:
                console.print(f"[finance] amount={amount}")
            if description:
                console.print(f"[finance] description={description}")

        app(["finance", "--amount", "-500.00", "--description", "Refund"])

        output = console.get_output()
        assert "[finance] amount=-500.00" in output
        assert "[finance] description=Refund" in output

    def test_balance_adjustment(self, console: MockConsole):
        # Inline CLI construction - account balance adjustment
        # Second positional is a delta (can be negative for withdrawals)
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("adjust-balance", console=console, parser_config=parser_config)

        @app.command(name="adjust-balance")
        def adjust_balance(account: str, delta: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[adjust-balance] account={account}")
            console.print(f"[adjust-balance] delta={delta}")

        app(["adjust-balance", "12345", "-1000.50"])

        output = console.get_output()
        assert "[adjust-balance] account=12345" in output
        assert "[adjust-balance] delta=-1000.50" in output


class TestMixedOptionsAndPositionals:
    def test_option_precedence_over_negative(self, console: MockConsole):
        # Inline CLI construction - option takes precedence over negative interpretation
        # -v is registered as a flag, so it's treated as option; -5 is a negative number
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("cmd", console=console, parser_config=parser_config)

        @app.command()
        def cmd(value: str, v: Annotated[bool, "-v"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[cmd] value={value}")
            if v:
                console.print("[cmd] v=True")

        app(["cmd", "-v", "-5"])

        output = console.get_output()
        assert "[cmd] v=True" in output
        assert "[cmd] value=-5" in output

    def test_negative_number_without_matching_option(self, console: MockConsole):
        # Inline CLI construction - no -1 option registered, so -1 is a negative number
        # Only -v is registered as an option; -1 becomes a positional
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("cmd", console=console, parser_config=parser_config)

        @app.command()
        def cmd(value: str, verbose: Annotated[bool, "-v"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[cmd] value={value}")
            if verbose:
                console.print("[cmd] verbose=True")

        app(["cmd", "-1"])

        output = console.get_output()
        assert "[cmd] value=-1" in output

    def test_combined_flags_with_negative_positional(self, console: MockConsole):
        # Inline CLI construction - combined short flags followed by negative number
        # -abc is three flags; -42 is a negative number positional
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("cmd", console=console, parser_config=parser_config)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            value: str,
            a: Annotated[bool, "-a"] = False,
            b: Annotated[bool, "-b"] = False,
            c: Annotated[bool, "-c"] = False,
        ):
            console.print(f"[cmd] value={value}")
            if a:
                console.print("[cmd] a=True")
            if b:
                console.print("[cmd] b=True")
            if c:
                console.print("[cmd] c=True")

        app(["cmd", "-abc", "-42"])

        output = console.get_output()
        assert "[cmd] a=True" in output
        assert "[cmd] b=True" in output
        assert "[cmd] c=True" in output
        assert "[cmd] value=-42" in output


class TestEdgeCasesInRealScenarios:
    def test_negative_zero(self, console: MockConsole):
        # Inline CLI construction - edge case: negative zero
        # Mathematically -0 == 0, but as a string it's preserved
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("cmd", console=console, parser_config=parser_config)

        @app.command()
        def cmd(value: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[cmd] value={value}")

        app(["cmd", "-0"])

        output = console.get_output()
        assert "[cmd] value=-0" in output

    def test_very_large_negative_exponent(self, console: MockConsole):
        # Inline CLI construction - Avogadro's number with negative exponent
        # Scientific notation with very small numbers (chemistry/physics constant)
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("cmd", console=console, parser_config=parser_config)

        @app.command()
        def cmd(value: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[cmd] value={value}")

        app(["cmd", "-6.022e-23"])

        output = console.get_output()
        assert "[cmd] value=-6.022e-23" in output

    def test_multiple_negative_values_for_option(self, console: MockConsole):
        # Inline CLI construction - option accepting multiple negative values
        # --range takes exactly 2 values, both can be negative
        # Note: tuple[str, str] with default None doesn't work well with negative
        # numbers, so we use optional flag and check if values were provided
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("cmd", console=console, parser_config=parser_config)

        @app.command()
        def cmd(  # pyright: ignore[reportUnusedFunction]
            range: Annotated[tuple[str, ...], "--range", ZeroOrMore()] = (),
        ):
            # Only print if we got exactly 2 values
            if len(range) == 2:
                console.print(f"[cmd] range={range!r}")

        app(["cmd", "--range", "-10", "-5"])

        output = console.get_output()
        assert "[cmd] range=('-10', '-5')" in output

    def test_delimiter_with_negatives(self, console: MockConsole):
        # Inline CLI construction - trailing args after `--` can include
        # negative numbers. Everything after `--` is captured in
        # ctx.parse_result.extra_args
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("cmd", console=console, parser_config=parser_config)

        @app.command()
        def cmd(ctx: Context):  # pyright: ignore[reportUnusedFunction]
            extra_args = ctx.parse_result.extra_args
            if extra_args:
                console.print(f"[cmd] extra_args={extra_args!r}")

        app(["cmd", "--", "-1", "-2", "-3"])

        output = console.get_output()
        assert "[cmd] extra_args=('-1', '-2', '-3')" in output


class TestComplexNumberCLI:
    def test_quantum_simulation_complex_amplitude(self, console: MockConsole):
        # Inline CLI construction - quantum mechanics with complex amplitudes
        # Complex numbers like -0.5+0.866j represent quantum state amplitudes
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("quantum", console=console, parser_config=parser_config)

        @app.command()
        def quantum(  # pyright: ignore[reportUnusedFunction]
            amplitude: Annotated[str | None, "--amplitude"] = None,
        ):
            if amplitude:
                console.print(f"[quantum] amplitude={amplitude}")

        app(["quantum", "--amplitude", "-0.5+0.866j"])

        output = console.get_output()
        assert "[quantum] amplitude=-0.5+0.866j" in output

    def test_signal_processing_fft_coefficients(self, console: MockConsole):
        # Inline CLI construction - FFT with multiple complex coefficients
        # Multiple complex number values with varying signs on real/imaginary parts
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("fft", console=console, parser_config=parser_config)

        @app.command()
        def fft(  # pyright: ignore[reportUnusedFunction]
            coefficients: Annotated[
                tuple[str, ...], "--coefficients", ZeroOrMore()
            ] = (),
        ):
            if coefficients:
                console.print(f"[fft] coefficients={coefficients!r}")

        app(["fft", "--coefficients", "-3+4j", "-1-2j", "5+0j"])

        output = console.get_output()
        assert "[fft] coefficients=('-3+4j', '-1-2j', '5+0j')" in output

    def test_electrical_engineering_impedance(self, console: MockConsole):
        # Inline CLI construction - electrical impedance (complex resistance)
        # Negative real component with positive imaginary (capacitive circuit)
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("analyze", console=console, parser_config=parser_config)

        @app.command()
        def analyze(  # pyright: ignore[reportUnusedFunction]
            impedance: Annotated[str | None, "--impedance"] = None,
        ):
            if impedance:
                console.print(f"[analyze] impedance={impedance}")

        app(["analyze", "--impedance", "-50+100j"])

        output = console.get_output()
        assert "[analyze] impedance=-50+100j" in output

    def test_mixed_real_and_complex(self, console: MockConsole):
        # Inline CLI construction - mix of real and complex numbers as positionals
        # Demonstrates parser handles both negative reals and complex numbers
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("compute", console=console, parser_config=parser_config)

        @app.command()
        def compute(values: Annotated[tuple[str, ...], ZeroOrMore()] = ()):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[compute] values={values!r}")

        app(["compute", "-5", "-3+4j", "10", "-2-1j"])

        output = console.get_output()
        assert "[compute] values=('-5', '-3+4j', '10', '-2-1j')" in output

    def test_pure_imaginary_positionals(self, console: MockConsole):
        # Inline CLI construction - pure imaginary numbers (negative imaginary part)
        # Numbers like -1j, -2.5j have no real component, only imaginary
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("compute", console=console, parser_config=parser_config)

        @app.command()
        def compute(values: Annotated[tuple[str, ...], ZeroOrMore()] = ()):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[compute] values={values!r}")

        app(["compute", "-1j", "-2.5j", "-3.14j"])

        output = console.get_output()
        assert "[compute] values=('-1j', '-2.5j', '-3.14j')" in output

    def test_complex_with_scientific_and_real(self, console: MockConsole):
        # Inline CLI construction - complex scientific notation mixed with
        # regular negatives. Extremely small complex numbers using
        # scientific notation
        parser_config = ParserConfiguration(allow_negative_numbers=True)
        app = App("compute", console=console, parser_config=parser_config)

        @app.command()
        def compute(values: Annotated[tuple[str, ...], ZeroOrMore()] = ()):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[compute] values={values!r}")

        app(["compute", "-1e5+2e3j", "-42", "-2.5E-10-3.14E-5j"])

        output = console.get_output()
        assert "[compute] values=('-1e5+2e3j', '-42', '-2.5E-10-3.14E-5j')" in output
