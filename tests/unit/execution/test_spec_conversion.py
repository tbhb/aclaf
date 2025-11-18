import pytest

from aclaf import (
    EMPTY_COMMAND_FUNCTION,
    ParameterKind,
    RuntimeParameter,
    ValidatorRegistry,
)
from aclaf.conversion import ConverterRegistry
from aclaf.execution import RuntimeCommand
from aclaf.parser import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    AccumulationMode,
    CommandSpec,
    OptionSpec,
    PositionalSpec,
)


class TestCommandSpecConversion:
    def test_minimal_command_to_spec(self):
        cmd = RuntimeCommand(
            name="test",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
        )
        spec = cmd.to_command_spec()

        assert isinstance(spec, CommandSpec)
        assert spec.name == "test"
        assert spec.aliases == frozenset()
        assert spec.options == {}
        assert spec.positionals == {}
        assert spec.subcommands == {}

    def test_command_with_aliases_to_spec(self):
        cmd = RuntimeCommand(
            name="test",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            aliases=("t", "tst"),
        )
        spec = cmd.to_command_spec()

        assert spec.aliases == frozenset(["t", "tst"])

    def test_command_spec_is_cached(self):
        cmd = RuntimeCommand(
            name="test",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
        )

        spec1 = cmd.to_command_spec()
        spec2 = cmd.to_command_spec()

        assert spec1 is spec2

    def test_subcommands_converted_recursively(self):
        child = RuntimeCommand(
            name="child",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            subcommands={"child": child},
        )

        spec = parent.to_command_spec()

        assert "child" in spec.subcommands
        assert isinstance(spec.subcommands["child"], CommandSpec)
        assert spec.subcommands["child"].name == "child"

    def test_nested_subcommands_converted(self):
        leaf = RuntimeCommand(
            name="leaf",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
        )
        mid = RuntimeCommand(
            name="mid",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            subcommands={"leaf": leaf},
        )
        root = RuntimeCommand(
            name="root",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            subcommands={"mid": mid},
        )

        spec = root.to_command_spec()

        assert "mid" in spec.subcommands
        assert "leaf" in spec.subcommands["mid"].subcommands
        assert spec.subcommands["mid"].subcommands["leaf"].name == "leaf"


class TestParameterToOptionSpecConversion:
    def test_option_parameter_converts_to_option_spec(self):
        param = RuntimeParameter(
            name="verbose",
            kind=ParameterKind.OPTION,
            value_type=bool,
            arity=EXACTLY_ONE_ARITY,
            long=("verbose",),
            short=("v",),
        )

        spec = param.to_option_spec()

        assert isinstance(spec, OptionSpec)
        assert spec.name == "verbose"
        assert spec.long == frozenset(["verbose"])
        assert spec.short == frozenset(["v"])
        assert spec.arity == EXACTLY_ONE_ARITY

    def test_option_spec_preserves_all_fields(self):
        param = RuntimeParameter(
            name="count",
            kind=ParameterKind.OPTION,
            value_type=int,
            arity=ONE_OR_MORE_ARITY,
            long=("count", "num"),
            short=("c", "n"),
            accumulation_mode=AccumulationMode.COLLECT,
            is_flag=False,
            flatten_values=True,
        )

        spec = param.to_option_spec()

        assert spec.name == "count"
        assert spec.long == frozenset(["count", "num"])
        assert spec.short == frozenset(["c", "n"])
        assert spec.arity == ONE_OR_MORE_ARITY
        assert spec.accumulation_mode == AccumulationMode.COLLECT
        assert spec.is_flag is False
        assert spec.flatten_values is True

    def test_flag_parameter_converts_with_flag_values(self):
        param = RuntimeParameter(
            name="debug",
            kind=ParameterKind.OPTION,
            value_type=bool,
            arity=EXACTLY_ONE_ARITY,
            long=("debug",),
            short=("d",),
            is_flag=True,
            truthy_flag_values=("true", "yes"),
            falsey_flag_values=("false", "no"),
            negation_words=("no", "disable"),
        )

        spec = param.to_option_spec()

        assert spec.is_flag is True
        assert spec.truthy_flag_values == frozenset(["true", "yes"])
        assert spec.falsey_flag_values == frozenset(["false", "no"])
        assert spec.negation_words == frozenset(["no", "disable"])

    def test_option_spec_defaults_accumulation_mode(self):
        param = RuntimeParameter(
            name="opt",
            kind=ParameterKind.OPTION,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
            accumulation_mode=None,
        )

        spec = param.to_option_spec()

        assert spec.accumulation_mode == AccumulationMode.LAST_WINS

    def test_option_spec_with_const_value(self):
        param = RuntimeParameter(
            name="verbose",
            kind=ParameterKind.OPTION,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
            const_value="very",
        )

        spec = param.to_option_spec()

        assert spec.const_value == "very"

    def test_to_option_spec_raises_for_positional_parameter(self):
        param = RuntimeParameter(
            name="arg",
            kind=ParameterKind.POSITIONAL,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
        )

        with pytest.raises(TypeError, match="Can only convert option parameters"):
            _ = param.to_option_spec()


class TestParameterToPositionalSpecConversion:
    def test_positional_parameter_converts_to_positional_spec(self):
        param = RuntimeParameter(
            name="filename",
            kind=ParameterKind.POSITIONAL,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
        )

        spec = param.to_positional_spec()

        assert isinstance(spec, PositionalSpec)
        assert spec.name == "filename"
        assert spec.arity == EXACTLY_ONE_ARITY

    def test_positional_spec_with_variadic_arity(self):
        param = RuntimeParameter(
            name="files",
            kind=ParameterKind.POSITIONAL,
            value_type=str,  # type: ignore[arg-type]
            arity=ONE_OR_MORE_ARITY,
        )

        spec = param.to_positional_spec()

        assert spec.name == "files"
        assert spec.arity == ONE_OR_MORE_ARITY

    def test_to_positional_spec_raises_for_option_parameter(self):
        param = RuntimeParameter(
            name="opt",
            kind=ParameterKind.OPTION,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
        )

        with pytest.raises(TypeError, match="Can only convert positional parameters"):
            _ = param.to_positional_spec()


class TestCommandWithParameterSpecConversion:
    def test_command_with_options_converts_to_spec(self):
        opt1 = RuntimeParameter(
            name="verbose",
            kind=ParameterKind.OPTION,
            value_type=bool,
            arity=EXACTLY_ONE_ARITY,
            long=("verbose",),
            short=("v",),
        )
        opt2 = RuntimeParameter(
            name="output",
            kind=ParameterKind.OPTION,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
            long=("output",),
            short=("o",),
        )

        cmd = RuntimeCommand(
            name="test",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            parameters={"verbose": opt1, "output": opt2},
        )

        spec = cmd.to_command_spec()

        assert "verbose" in spec.options
        assert "output" in spec.options
        assert isinstance(spec.options["verbose"], OptionSpec)
        assert isinstance(spec.options["output"], OptionSpec)

    def test_command_with_positionals_converts_to_spec(self):
        pos1 = RuntimeParameter(
            name="source",
            kind=ParameterKind.POSITIONAL,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
        )
        pos2 = RuntimeParameter(
            name="dest",
            kind=ParameterKind.POSITIONAL,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
        )

        cmd = RuntimeCommand(
            name="test",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            parameters={"source": pos1, "dest": pos2},
        )

        spec = cmd.to_command_spec()

        assert "source" in spec.positionals
        assert "dest" in spec.positionals
        assert isinstance(spec.positionals["source"], PositionalSpec)
        assert isinstance(spec.positionals["dest"], PositionalSpec)

    def test_command_with_mixed_parameters_converts_to_spec(self):
        opt = RuntimeParameter(
            name="verbose",
            kind=ParameterKind.OPTION,
            value_type=bool,
            arity=EXACTLY_ONE_ARITY,
            long=("verbose",),
        )
        pos = RuntimeParameter(
            name="file",
            kind=ParameterKind.POSITIONAL,
            value_type=str,
            arity=EXACTLY_ONE_ARITY,
        )

        cmd = RuntimeCommand(
            name="test",
            run_func=EMPTY_COMMAND_FUNCTION,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            parameters={"verbose": opt, "file": pos},
        )

        spec = cmd.to_command_spec()

        assert "verbose" in spec.options
        assert "file" in spec.positionals
        assert len(spec.options) == 1
        assert len(spec.positionals) == 1
