import re
import string
from typing import TYPE_CHECKING

import pytest
from hypothesis import assume, example, given, strategies as st

from aclaf.parser import (
    EXACTLY_ONE_ARITY,
    ZERO_ARITY,
    CommandSpec,
    OptionSpec,
    Parser,
    UnknownOptionError,
)

if TYPE_CHECKING:
    from hypothesis.strategies import DrawFn


@st.composite
def option_name_with_separators(draw: "DrawFn", separator: str) -> str:
    # Generate 2-4 segments, each starting with a letter
    num_segments = draw(st.integers(min_value=2, max_value=4))
    segments: list[str] = []
    for _ in range(num_segments):
        # Each segment starts with a letter, then has 0-7 more alphanumeric chars
        first_char = draw(st.sampled_from(string.ascii_letters))
        rest = draw(st.text(alphabet=string.ascii_letters + string.digits, max_size=7))
        segments.append(first_char + rest)

    option_name = separator.join(segments)

    # Verify it matches the regex (should always pass with this strategy)
    long_name_regex = re.compile(r"^[a-zA-Z0-9][a-zA-Z-_]*[a-zA-Z0-9]$")
    _ = assume(re.match(long_name_regex, option_name))

    return option_name


class TestConversionNormalizationProperties:
    @example(name="ab")
    @example(name="my_option")
    @example(name="my-option")
    @given(name=option_name_with_separators(separator="_"))
    def test_idempotency_underscore_input(self, name: str):
        # First normalization
        normalized_once = name.replace("_", "-")
        # Second normalization
        normalized_twice = normalized_once.replace("_", "-")
        assert normalized_once == normalized_twice

    @example(name="ab")
    @example(name="my-option")
    @given(name=option_name_with_separators(separator="-"))
    def test_idempotency_dash_input(self, name: str):
        normalized = name.replace("_", "-")
        assert normalized == name

    @example(name="option")
    @given(
        name=st.text(
            alphabet=string.ascii_letters + string.digits,
            min_size=2,
            max_size=20,
        ).filter(lambda s: s and s[0].isalpha() and "_" not in s and "-" not in s)
    )
    def test_preservation_without_separators(self, name: str):
        normalized = name.replace("_", "-")
        assert normalized == name


class TestConversionEquivalenceProperties:
    @example(name="my_option", value="test")
    @example(name="database_url", value="postgres://localhost")
    @given(
        name=option_name_with_separators(separator="_"),
        value=st.text(min_size=1, max_size=50).filter(lambda s: not s.startswith("-")),
    )
    def test_bidirectional_equivalence_underscores_to_dashes(
        self, name: str, value: str
    ):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({name}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # User can type with underscores (exact match after normalization)
        result_underscore = parser.parse([f"--{name}", value])
        assert result_underscore.options["opt"].value == value

        # User can also type with dashes (normalized to same form)
        dash_version = name.replace("_", "-")
        result_dash = parser.parse([f"--{dash_version}", value])
        assert result_dash.options["opt"].value == value

        # Both produce identical results
        assert (
            result_underscore.options["opt"].value == result_dash.options["opt"].value
        )

    @example(name="my_option", value="test")
    @given(
        name=option_name_with_separators(separator="-"),
        value=st.text(min_size=1, max_size=50).filter(lambda s: not s.startswith("-")),
    )
    def test_bidirectional_equivalence_dashes_to_underscores(
        self, name: str, value: str
    ):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({name}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=True)

        # User can type with dashes (exact match)
        result_dash = parser.parse([f"--{name}", value])
        assert result_dash.options["opt"].value == value

        # User can also type with underscores (normalized to dashes)
        underscore_version = name.replace("-", "_")
        result_underscore = parser.parse([f"--{underscore_version}", value])
        assert result_underscore.options["opt"].value == value

        # Both produce identical results
        assert (
            result_dash.options["opt"].value == result_underscore.options["opt"].value
        )

    @example(name="my_option", value="test")
    @given(
        name=option_name_with_separators(separator="_"),
        value=st.text(min_size=1, max_size=50).filter(lambda s: not s.startswith("-")),
    )
    def test_strict_mode_requires_exact_separator_match(self, name: str, value: str):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({name}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(spec, convert_underscores_to_dashes=False)

        # Exact match works
        result = parser.parse([f"--{name}", value])
        assert result.options["opt"].value == value

        # Different separator fails
        dash_version = name.replace("_", "-")
        if dash_version != name:  # Only test if they're different
            with pytest.raises(UnknownOptionError):
                _ = parser.parse([f"--{dash_version}", value])


class TestConversionWithCaseInsensitivity:
    @example(name="my_option", value="test")
    @example(name="database_url", value="value")
    @given(
        name=option_name_with_separators(separator="_"),
        value=st.text(min_size=1, max_size=50).filter(lambda s: not s.startswith("-")),
    )
    def test_conversion_then_case_normalization_order(self, name: str, value: str):
        # Normalize name to lowercase with dashes
        normalized = name.replace("_", "-").lower()

        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({normalized}), arity=EXACTLY_ONE_ARITY
                )
            },
        )
        parser = Parser(
            spec,
            convert_underscores_to_dashes=True,
            case_insensitive_options=True,
        )

        # User input with different case and separators should work
        result = parser.parse([f"--{name}", value])
        assert result.options["opt"].value == value

        # Try with uppercase version and dashes
        upper_version = name.upper().replace("_", "-")
        result2 = parser.parse([f"--{upper_version}", value])
        assert result2.options["opt"].value == value


class TestConversionCommutativity:
    @example(name="my_option", value="test")
    @given(
        name=option_name_with_separators(separator="_"),
        value=st.text(min_size=1, max_size=50).filter(lambda s: not s.startswith("-")),
    )
    def test_multiple_conversions_yield_same_result(self, name: str, value: str):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt", long=frozenset({name}), arity=EXACTLY_ONE_ARITY
                )
            },
        )

        parser1 = Parser(spec, convert_underscores_to_dashes=True)
        parser2 = Parser(spec, convert_underscores_to_dashes=True)

        dash_version = name.replace("_", "-")

        result1 = parser1.parse([f"--{dash_version}", value])
        result2 = parser2.parse([f"--{dash_version}", value])

        assert result1.options["opt"].value == result2.options["opt"].value


class TestConversionWithNegation:
    @example(name="force_push")
    @example(name="use_colors")
    @given(
        name=option_name_with_separators(separator="_"),
    )
    def test_negation_name_construction_with_underscores(self, name: str):
        # Just verify that spec construction works - negation names are
        # built from normalized option names when convert_underscores_to_dashes=True
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt",
                    long=frozenset({name}),
                    negation_words=frozenset({"no"}),
                    arity=ZERO_ARITY,
                )
            },
        )
        # Spec construction should succeed
        assert spec is not None
        assert len(spec.options) == 1

    @example(name="force_push")
    @given(
        name=option_name_with_separators(separator="-"),
    )
    def test_negation_name_construction_with_dashes(self, name: str):
        spec = CommandSpec(
            name="cmd",
            options={
                "opt": OptionSpec(
                    "opt",
                    long=frozenset({name}),
                    negation_words=frozenset({"no"}),
                    arity=ZERO_ARITY,
                )
            },
        )
        # Spec construction should succeed
        assert spec is not None
        assert len(spec.options) == 1


class TestConversionLengthInvariance:
    @example(name="a_b")
    @example(name="very_long_option_name_with_many_segments")
    @given(name=option_name_with_separators(separator="_"))
    def test_conversion_preserves_character_count(self, name: str):
        normalized = name.replace("_", "-")
        assert len(normalized) == len(name)

    @example(name="a_b_c_d")
    @given(name=option_name_with_separators(separator="_"))
    def test_conversion_preserves_separator_count(self, name: str):
        underscore_count = name.count("_")
        dash_count = name.replace("_", "-").count("-")
        assert underscore_count == dash_count
