"""Regression tests for property-based test failures.

This file contains specific test cases that were discovered by Hypothesis
during property-based testing. Each test is kept as a regression test to
ensure previously-found bugs don't resurface.

When to add a test here:
1. Hypothesis discovers a failing test case
2. You fix the bug
3. Add the minimal failing case as a regression test
4. Include: what property found it, date, and description of the bug
"""

from aclaf.parser import CommandSpec, OptionSpec, Parser
from aclaf.parser.types import Arity


class TestHypothesisRegressions:
    """Regression tests from Hypothesis failures."""

    def test_regression_empty_value_list_2025_11_09(self):
        """Regression: Parser bug with min_arity=0, max_arity=1, no values.

        Found by: test_option_consumes_within_arity_bounds
        Date: 2025-11-09
        Issue: IndexError when accessing values[0] on empty list

        When an option has optional values (min_arity=0) but can accept
        one value (max_arity=1), and no values are provided, the parser
        should handle it gracefully.
        """
        spec = CommandSpec(
            name="cmd",
            options={"opt": OptionSpec("opt", arity=Arity(0, 1))},
        )
        parser = Parser(spec)

        # This should not raise IndexError
        result = parser.parse(["--opt"])

        # Expected: option is present but has no value
        assert "opt" in result.options
        # Value should be empty tuple for optional parameter with no values
        assert result.options["opt"].value == ()

    # Future regression tests will be added here as Hypothesis discovers them
