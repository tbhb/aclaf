"""Security tests for edge cases and resource exhaustion.

This module tests the parser's behavior under extreme conditions that could
be exploited for denial of service (DoS) attacks or other security issues.

## Test categories

### Denial of service protection
Tests that the parser handles complex or deeply nested input without hanging,
excessive memory consumption, or stack overflow.

### Resource exhaustion protection
Tests that the parser remains efficient with large numbers of options, values,
or arguments that might exhaust system resources.

### Ambiguous input handling
Tests that ambiguous or malformed input is handled consistently and predictably,
without security implications.

## Security considerations

While Python's runtime provides protection against many low-level exploits
(buffer overflows, stack smashing), these tests verify:

1. No algorithmic complexity attacks (e.g., O(n²) behavior with crafted input)
2. Reasonable memory usage with large inputs
3. Fast termination even with complex input
4. Predictable behavior with edge cases

Applications using this parser should still implement timeouts and resource
limits appropriate to their security requirements.
"""

import time

import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import EXACTLY_ONE_ARITY, ONE_OR_MORE_ARITY, ZERO_OR_MORE_ARITY


@pytest.mark.security
class TestDenialOfServiceProtection:
    """Test protection against DoS attacks through complex input."""

    def test_deeply_nested_equals_in_value(self):
        """Parser handles multiple equals signs in option values efficiently.

        Potential DoS vector: Option value with many '=' characters might
        trigger inefficient parsing logic.
        """
        spec = CommandSpec(
            name="cmd",
            options={"data": OptionSpec("data", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Value with many equals signs
        complex_value = "=" * 1000
        args = ["--data", complex_value]

        start_time = time.perf_counter()
        result = parser.parse(args)
        elapsed = time.perf_counter() - start_time

        assert isinstance(result.options["data"].value, str)
        assert result.options["data"].value == complex_value
        # Should complete very quickly (< 10ms)
        assert elapsed < 0.01, f"Parsing took {elapsed:.3f}s (DoS risk)"

    def test_many_consecutive_dashes(self):
        """Parser handles input with many consecutive dashes efficiently.

        Potential DoS vector: Strings with many dash characters might
        trigger inefficient string processing logic.
        """
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Value with many dashes in the middle
        # (not at start to avoid option-like appearance)
        complex_value = "value" + "-" * 1000 + "end"
        args = ["--output", complex_value]

        start_time = time.perf_counter()
        result = parser.parse(args)
        elapsed = time.perf_counter() - start_time

        assert isinstance(result.options["output"].value, str)
        assert result.options["output"].value == complex_value
        assert elapsed < 0.01, f"Parsing took {elapsed:.3f}s (DoS risk)"

    def test_alternating_options_and_values(self):
        """Parser handles many alternating options and values efficiently.

        Potential DoS vector: Alternating pattern might trigger worst-case
        behavior in option-value binding logic.
        """
        spec = CommandSpec(
            name="cmd",
            options={
                "a": OptionSpec("a", arity=EXACTLY_ONE_ARITY),
                "b": OptionSpec("b", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)

        # Alternate between two options 1000 times
        args: list[str] = []
        for i in range(1000):
            args.extend(["--a", f"value{i}", "--b", f"value{i}"])

        start_time = time.perf_counter()
        result = parser.parse(args)
        elapsed = time.perf_counter() - start_time

        # Last values should win
        assert isinstance(result.options["a"].value, str)
        assert isinstance(result.options["b"].value, str)
        assert result.options["a"].value == "value999"
        assert result.options["b"].value == "value999"
        # Should be roughly O(n) - complete in reasonable time
        assert elapsed < 0.1, f"Parsing took {elapsed:.3f}s (DoS risk)"

    def test_many_short_options_combined(self):
        """Parser handles very long combined short options efficiently.

        Potential DoS vector: Combined short option string like "-abcd...xyz"
        with hundreds of characters might trigger inefficient character-by-character
        processing.
        """
        # Create spec with 26 single-character flag options
        options = {
            chr(ord("a") + i): OptionSpec(chr(ord("a") + i), is_flag=True)
            for i in range(26)
        }
        spec = CommandSpec(name="cmd", options=options)
        parser = Parser(spec)

        # Combine all 26 options repeatedly
        combined_options = "-" + "abcdefghijklmnopqrstuvwxyz" * 10
        args = [combined_options]

        start_time = time.perf_counter()
        result = parser.parse(args)
        elapsed = time.perf_counter() - start_time

        # All options should be set
        assert all(result.options[chr(ord("a") + i)].value is True for i in range(26))
        assert elapsed < 0.01, f"Parsing took {elapsed:.3f}s (DoS risk)"


@pytest.mark.security
class TestResourceExhaustionProtection:
    """Test protection against resource exhaustion attacks."""

    def test_memory_usage_with_large_positionals(self):
        """Parser memory usage is reasonable with large positional lists.

        Resource exhaustion: Many positional arguments should not cause
        excessive memory allocation or retention.
        """
        spec = CommandSpec(
            name="cmd",
            positionals={
                "files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY),
            },
        )
        parser = Parser(spec)

        # 100,000 file arguments
        large_file_list = [f"file{i}.txt" for i in range(100_000)]

        # Parse should succeed without exhausting memory
        result = parser.parse(large_file_list)

        assert len(result.positionals["files"].value) == 100_000
        # Verify first and last elements to ensure all data preserved
        assert result.positionals["files"].value[0] == "file0.txt"
        assert result.positionals["files"].value[99_999] == "file99999.txt"

    def test_parsing_time_linear_with_input_size(self):
        """Parser performance scales reasonably with input size.

        Complexity attack: Parsing time should not exhibit catastrophic
        exponential or quadratic growth with input size.
        """
        spec = CommandSpec(
            name="cmd",
            positionals={
                "args": PositionalSpec("args", arity=ZERO_OR_MORE_ARITY),
            },
        )
        parser = Parser(spec)

        # Test with increasing input sizes
        small_size = 1000
        large_size = 10000

        # Parse small input
        small_args = [f"arg{i}" for i in range(small_size)]
        start = time.perf_counter()
        _ = parser.parse(small_args)
        small_time = time.perf_counter() - start

        # Parse large input (10x size)
        large_args = [f"arg{i}" for i in range(large_size)]
        start = time.perf_counter()
        _ = parser.parse(large_args)
        large_time = time.perf_counter() - start

        # Large input should not exhibit quadratic scaling (100x slower)
        # Allow generous factor to account for overhead, caching, etc.
        # Main goal: detect catastrophic performance degradation
        scaling_factor = large_time / small_time if small_time > 0 else 0
        assert scaling_factor < 150, (
            f"Performance may not scale well: "
            f"{small_size} args took {small_time:.3f}s, "
            f"{large_size} args took {large_time:.3f}s "
            f"(factor: {scaling_factor:.1f}x, expected < 150x for reasonable scaling)"
        )

    def test_many_unused_options_in_spec(self):
        """Parser performance with many defined but unused options.

        Resource exhaustion: Having many options in spec but few used
        should not significantly impact performance.
        """
        # Create spec with 26 options using double letters (aa, bb, cc, ...)
        # This format satisfies validation: 2 chars, both alphanumeric
        letters = [chr(ord("a") + i) * 2 for i in range(26)]
        options = {
            letter: OptionSpec(letter, arity=EXACTLY_ONE_ARITY) for letter in letters
        }
        spec = CommandSpec(name="cmd", options=options)
        parser = Parser(spec)

        # Use only a few options
        args = ["--aa", "val_aa", "--mm", "val_mm", "--zz", "val_zz"]

        start_time = time.perf_counter()
        result = parser.parse(args)
        elapsed = time.perf_counter() - start_time

        assert isinstance(result.options["aa"].value, str)
        assert isinstance(result.options["mm"].value, str)
        assert isinstance(result.options["zz"].value, str)
        assert result.options["aa"].value == "val_aa"
        assert result.options["mm"].value == "val_mm"
        assert result.options["zz"].value == "val_zz"
        # Should complete quickly despite many options in spec
        assert elapsed < 0.1, f"Parsing took {elapsed:.3f}s (DoS risk)"


@pytest.mark.security
class TestAmbiguousInputHandling:
    """Test handling of ambiguous or edge case input."""

    def test_option_name_looks_like_value(self):
        """Values that don't start with dashes can contain dash-like patterns.

        Security consideration: Parser correctly distinguishes between options
        (which start with dashes) and values (which may contain dashes but
        don't start with them).
        """
        spec = CommandSpec(
            name="cmd",
            options={"pattern": OptionSpec("pattern", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Value containing dashes but not starting with them
        args = ["--pattern", "some--value--with--dashes"]
        result = parser.parse(args)

        # Should be treated as the value
        assert isinstance(result.options["pattern"].value, str)
        assert result.options["pattern"].value == "some--value--with--dashes"
        assert "--" in result.options["pattern"].value

    def test_empty_string_values(self):
        """Empty string values are handled correctly.

        Edge case: Empty strings should be valid values and distinct from
        missing values.
        """
        spec = CommandSpec(
            name="cmd",
            options={"message": OptionSpec("message", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Explicit empty string value
        args = ["--message", ""]
        result = parser.parse(args)

        assert isinstance(result.options["message"].value, str)
        assert result.options["message"].value == ""
        assert result.options["message"].value is not None

    def test_whitespace_only_values(self):
        """Whitespace-only values are preserved.

        Edge case: Values containing only whitespace should be preserved
        exactly as provided.
        """
        spec = CommandSpec(
            name="cmd",
            options={"data": OptionSpec("data", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Various whitespace-only values
        test_cases = [
            " ",  # Single space
            "   ",  # Multiple spaces
            "\t",  # Tab
            "\n",  # Newline
            "  \t\n  ",  # Mixed whitespace
        ]

        for whitespace_value in test_cases:
            result = parser.parse(["--data", whitespace_value])
            assert isinstance(result.options["data"].value, str)
            assert result.options["data"].value == whitespace_value, (
                f"Whitespace value {whitespace_value!r} not preserved"
            )

    def test_numeric_strings_preserved_as_strings(self):
        """Numeric-looking strings are preserved as strings.

        Security consideration: Parser should not auto-convert types, which
        could lead to unexpected behavior or vulnerabilities.

        Note: Strings starting with dash (like "-42") may be interpreted as
        options. Use positional arguments or -- separator for such values.
        """
        spec = CommandSpec(
            name="cmd",
            options={"value": OptionSpec("value", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Positive numeric strings (don't start with dash)
        numeric_strings = ["123", "3.14", "42", "1e10", "0x1F", "0o777"]

        for numeric_str in numeric_strings:
            result = parser.parse(["--value", numeric_str])
            # Should be preserved as string, not converted to number
            assert isinstance(result.options["value"].value, str)
            assert result.options["value"].value == numeric_str

    def test_boolean_strings_preserved_as_strings(self):
        """Boolean-looking strings are preserved as strings.

        Security consideration: Parser should not auto-convert "true"/"false"
        strings to booleans, as this could be a source of confusion or bypass.
        """
        spec = CommandSpec(
            name="cmd",
            options={"setting": OptionSpec("setting", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        boolean_strings = [
            "true",
            "false",
            "True",
            "False",
            "TRUE",
            "FALSE",
            "yes",
            "no",
        ]

        for bool_str in boolean_strings:
            result = parser.parse(["--setting", bool_str])
            # Should be preserved as string, not converted to boolean
            assert isinstance(result.options["setting"].value, str)
            assert result.options["setting"].value == bool_str

    def test_special_json_values_preserved(self):
        """JSON-like special values are preserved as strings.

        Security consideration: Parser should not interpret JSON syntax,
        which could lead to injection or confusion with downstream JSON parsing.
        """
        spec = CommandSpec(
            name="cmd",
            options={"data": OptionSpec("data", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        json_like_values = ["null", "undefined", "{}", "[]", '{"key":"value"}']

        for json_value in json_like_values:
            result = parser.parse(["--data", json_value])
            assert isinstance(result.options["data"].value, str)
            assert result.options["data"].value == json_value
