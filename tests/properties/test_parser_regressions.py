from aclaf.parser import CommandSpec, OptionSpec, Parser
from aclaf.parser.types import Arity


class TestHypothesisRegressions:
    def test_regression_empty_value_list_2025_11_09(self):
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
