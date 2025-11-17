
from aclaf import EMPTY_COMMAND_FUNCTION
from aclaf._runtime import RuntimeCommand
from aclaf.parser import CommandSpec


class TestCommandSpecConversion:

    def test_minimal_command_to_spec(self):
        cmd = RuntimeCommand(name="test", run_func=EMPTY_COMMAND_FUNCTION)
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
            aliases=("t", "tst"),
        )
        spec = cmd.to_command_spec()

        assert spec.aliases == frozenset(["t", "tst"])

    def test_command_spec_is_cached(self):
        cmd = RuntimeCommand(name="test", run_func=EMPTY_COMMAND_FUNCTION)

        spec1 = cmd.to_command_spec()
        spec2 = cmd.to_command_spec()

        assert spec1 is spec2

    def test_subcommands_converted_recursively(self):
        child = RuntimeCommand(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        parent = RuntimeCommand(
            name="parent",
            run_func=EMPTY_COMMAND_FUNCTION,
            subcommands={"child": child},
        )

        spec = parent.to_command_spec()

        assert "child" in spec.subcommands
        assert isinstance(spec.subcommands["child"], CommandSpec)
        assert spec.subcommands["child"].name == "child"

    def test_nested_subcommands_converted(self):
        leaf = RuntimeCommand(name="leaf", run_func=EMPTY_COMMAND_FUNCTION)
        mid = RuntimeCommand(
            name="mid",
            run_func=EMPTY_COMMAND_FUNCTION,
            subcommands={"leaf": leaf},
        )
        root = RuntimeCommand(
            name="root",
            run_func=EMPTY_COMMAND_FUNCTION,
            subcommands={"mid": mid},
        )

        spec = root.to_command_spec()

        assert "mid" in spec.subcommands
        assert "leaf" in spec.subcommands["mid"].subcommands
        assert spec.subcommands["mid"].subcommands["leaf"].name == "leaf"
