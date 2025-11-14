"""Integration tests for negative number handling in realistic scenarios.

This module tests negative number parsing in complex, realistic command-line
scenarios that combine multiple parser features.
"""

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    Arity,
)


class TestCalculatorLikeCLI:
    """Test negative numbers in a calculator-style CLI."""

    def test_add_with_negative_numbers(self):
        """Calculator CLI: add -10 5 -3."""
        spec = CommandSpec(
            name="calc",
            subcommands={
                "add": CommandSpec(
                    name="add",
                    positionals={
                        "values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)
                    },
                )
            },
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["add", "-10", "5", "-3"])
        assert result.subcommand is not None
        assert result.subcommand.command == "add"
        assert result.subcommand.positionals["values"].value == ("-10", "5", "-3")

    def test_multiply_with_options_and_negatives(self):
        """Calculator CLI: multiply --precision 2 -5.5 3.14."""
        spec = CommandSpec(
            name="calc",
            subcommands={
                "multiply": CommandSpec(
                    name="multiply",
                    options={
                        "precision": OptionSpec("precision", arity=EXACTLY_ONE_ARITY)
                    },
                    positionals={
                        "values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)
                    },
                )
            },
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["multiply", "--precision", "2", "-5.5", "3.14"])
        assert result.subcommand is not None
        assert result.subcommand.options["precision"].value == "2"
        assert result.subcommand.positionals["values"].value == ("-5.5", "3.14")


class TestDataProcessingCLI:
    """Test negative numbers in data processing scenarios."""

    def test_filter_with_range(self):
        """Data processing: filter --min -100 --max 100 data.csv."""
        spec = CommandSpec(
            name="process",
            options={
                "min": OptionSpec("min", arity=EXACTLY_ONE_ARITY),
                "max": OptionSpec("max", arity=EXACTLY_ONE_ARITY),
            },
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--min", "-100", "--max", "100", "data.csv"])
        assert result.options["min"].value == "-100"
        assert result.options["max"].value == "100"
        assert result.positionals["file"].value == "data.csv"

    def test_threshold_with_scientific_notation(self):
        """Data processing: analyze --threshold -1.5e-10 input.dat."""
        spec = CommandSpec(
            name="analyze",
            options={"threshold": OptionSpec("threshold", arity=EXACTLY_ONE_ARITY)},
            positionals={"input": PositionalSpec("input", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--threshold", "-1.5e-10", "input.dat"])
        assert result.options["threshold"].value == "-1.5e-10"
        assert result.positionals["input"].value == "input.dat"


class TestScientificComputing:
    """Test negative numbers in scientific computing CLIs."""

    def test_simulation_with_multiple_params(self):
        """Simulation: run --temp -273.15 --pressure 1.0 --time -0.5."""
        spec = CommandSpec(
            name="simulate",
            options={
                "temp": OptionSpec("temp", arity=EXACTLY_ONE_ARITY),
                "pressure": OptionSpec("pressure", arity=EXACTLY_ONE_ARITY),
                "time": OptionSpec("time", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(
            [
                "--temp",
                "-273.15",
                "--pressure",
                "1.0",
                "--time",
                "-0.5",
            ]
        )
        assert result.options["temp"].value == "-273.15"
        assert result.options["pressure"].value == "1.0"
        assert result.options["time"].value == "-0.5"

    def test_coordinate_system(self):
        """3D coordinates: plot -5.0 -3.2 10.5."""
        spec = CommandSpec(
            name="plot",
            positionals={"coords": PositionalSpec("coords", arity=Arity(3, 3))},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-5.0", "-3.2", "10.5"])
        assert result.positionals["coords"].value == ("-5.0", "-3.2", "10.5")


class TestFinancialCLI:
    """Test negative numbers in financial/accounting scenarios."""

    def test_transaction_with_negative_amount(self):
        """Finance: transaction --amount -500.00 --description "Refund"."""
        spec = CommandSpec(
            name="finance",
            options={
                "amount": OptionSpec("amount", arity=EXACTLY_ONE_ARITY),
                "description": OptionSpec("description", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--amount", "-500.00", "--description", "Refund"])
        assert result.options["amount"].value == "-500.00"
        assert result.options["description"].value == "Refund"

    def test_balance_adjustment(self):
        """Finance: adjust-balance 12345 -1000.50."""
        spec = CommandSpec(
            name="adjust-balance",
            positionals={
                "account": PositionalSpec("account", arity=EXACTLY_ONE_ARITY),
                "delta": PositionalSpec("delta", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["12345", "-1000.50"])
        assert result.positionals["account"].value == "12345"
        assert result.positionals["delta"].value == "-1000.50"


class TestMixedOptionsAndPositionals:
    """Test negative numbers with complex option/positional interactions."""

    def test_option_precedence_over_negative(self):
        """When -v option exists, it takes precedence over -5 number."""
        spec = CommandSpec(
            name="cmd",
            options={"v": OptionSpec("v", arity=ZERO_ARITY)},
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        # -v is flag, -5 is positional
        result = parser.parse(["-v", "-5"])
        assert result.options["v"].value is True
        assert result.positionals["value"].value == "-5"

    def test_negative_number_without_matching_option(self):
        """When no -1 option, -1 becomes positional."""
        spec = CommandSpec(
            name="cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1"])
        assert result.positionals["value"].value == "-1"

    def test_combined_flags_with_negative_positional(self):
        """Combined flags followed by negative number."""
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", arity=ZERO_ARITY),
                "b": OptionSpec("b", arity=ZERO_ARITY),
                "c": OptionSpec("c", arity=ZERO_ARITY),
            },
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-abc", "-42"])
        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["c"].value is True
        assert result.positionals["value"].value == "-42"


class TestEdgeCasesInRealScenarios:
    """Test edge cases that might occur in real-world usage."""

    def test_negative_zero(self):
        """Handle -0 correctly."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-0"])
        assert result.positionals["value"].value == "-0"

    def test_very_large_negative_exponent(self):
        """Handle large negative exponents in scientific notation."""
        spec = CommandSpec(
            name="cmd",
            positionals={"value": PositionalSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-6.022e-23"])
        assert result.positionals["value"].value == "-6.022e-23"

    def test_multiple_negative_values_for_option(self):
        """Option consuming multiple negative values."""
        spec = CommandSpec(
            name="cmd",
            options={"range": OptionSpec("range", arity=Arity(2, 2))},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--range", "-10", "-5"])
        assert result.options["range"].value == ("-10", "-5")

    def test_delimiter_with_negatives(self):
        """Negatives after -- are literals."""
        spec = CommandSpec(name="cmd")
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--", "-1", "-2", "-3"])
        assert result.extra_args == ("-1", "-2", "-3")


class TestComplexNumberCLI:
    """Test complex numbers in scientific computing scenarios."""

    def test_quantum_simulation_complex_amplitude(self):
        """Quantum simulation: simulate --amplitude -0.5+0.866j."""
        spec = CommandSpec(
            name="quantum",
            options={"amplitude": OptionSpec("amplitude", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--amplitude", "-0.5+0.866j"])
        assert result.options["amplitude"].value == "-0.5+0.866j"

    def test_signal_processing_fft_coefficients(self):
        """Signal processing: fft --coefficients -3+4j -1-2j 5+0j."""
        spec = CommandSpec(
            name="fft",
            options={
                "coefficients": OptionSpec("coefficients", arity=ZERO_OR_MORE_ARITY)
            },
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--coefficients", "-3+4j", "-1-2j", "5+0j"])
        assert result.options["coefficients"].value == ("-3+4j", "-1-2j", "5+0j")

    def test_electrical_engineering_impedance(self):
        """Electrical engineering: analyze --impedance -50+100j."""
        spec = CommandSpec(
            name="analyze",
            options={"impedance": OptionSpec("impedance", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["--impedance", "-50+100j"])
        assert result.options["impedance"].value == "-50+100j"

    def test_mixed_real_and_complex(self):
        """Mix of real and complex numbers."""
        spec = CommandSpec(
            name="compute",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-5", "-3+4j", "10", "-2-1j"])
        assert result.positionals["values"].value == ("-5", "-3+4j", "10", "-2-1j")

    def test_pure_imaginary_positionals(self):
        """Pure imaginary numbers as positionals."""
        spec = CommandSpec(
            name="compute",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1j", "-2.5j", "-3.14j"])
        assert result.positionals["values"].value == ("-1j", "-2.5j", "-3.14j")

    def test_complex_with_scientific_and_real(self):
        """Complex numbers with scientific notation mixed with real numbers."""
        spec = CommandSpec(
            name="compute",
            positionals={"values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec, allow_negative_numbers=True)

        result = parser.parse(["-1e5+2e3j", "-42", "-2.5E-10-3.14E-5j"])
        assert result.positionals["values"].value == (
            "-1e5+2e3j",
            "-42",
            "-2.5E-10-3.14E-5j",
        )
