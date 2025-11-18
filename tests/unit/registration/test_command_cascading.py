# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnusedFunction=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportUninitializedInstanceVariable=false, reportUnannotatedClassAttribute=false
# ruff: noqa: ARG001

from typing import TYPE_CHECKING

from annotated_types import BaseMetadata

from aclaf import EMPTY_COMMAND_FUNCTION, Command
from aclaf.logging import MockLogger
from aclaf.validation import ValidatorRegistry

if TYPE_CHECKING:
    from collections.abc import Mapping

    from aclaf.logging import Logger
    from aclaf.types import ParameterValueType


class CascadeInt:
    """Custom type for cascading tests."""

    def __init__(self, value: int) -> None:
        self.value = value


class CascadeStr:
    """Custom type for cascading tests."""

    def __init__(self, value: str) -> None:
        self.value = value


class CascadeFloat:
    """Custom type for cascading tests."""

    def __init__(self, value: float) -> None:
        self.value = value


class CascadeMetadata1(BaseMetadata):
    """Custom metadata for cascading tests."""

    value: int


class CascadeMetadata2(BaseMetadata):
    """Custom metadata for cascading tests."""

    min_value: int


class CascadeMetadata3(BaseMetadata):
    """Custom metadata for cascading tests."""

    max_value: int


class CascadeMetadata4(BaseMetadata):
    """Custom metadata for cascading tests."""

    threshold: int


class CascadeMetadata5(BaseMetadata):
    """Custom metadata for cascading tests."""

    limit: int


class CascadeMetadata6(BaseMetadata):
    """Custom metadata for cascading tests."""

    count: int


class TestConverterCascading:
    def test_mount_cascades_converters_to_child(self) -> None:
        parent = Command(name="parent")

        @parent.converter(CascadeInt)
        def parse_cascade_int(value, metadata):
            return CascadeInt(int(value) * 2)

        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        parent.mount(child)

        # Child gains parent's converter through merge
        assert child.converters.has_converter(CascadeInt)

    def test_mount_merges_child_converter_registry(self) -> None:
        parent = Command(name="parent")

        @parent.converter(CascadeInt)
        def parent_converter(value, metadata):
            return CascadeInt(int(value) * 2)

        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        @child.converter(CascadeStr)
        def child_converter(value, metadata):
            return CascadeStr(str(value).upper())

        # Child has its own registry before mounting
        assert child.converters is not parent.converters
        assert child.converters.has_converter(CascadeStr)
        assert not child.converters.has_converter(CascadeInt)

        # Mount merges parent's converters into child's registry
        parent.mount(child)

        # After merge, child keeps its own registry but gains parent's converters
        assert child.converters is not parent.converters
        assert child.converters.has_converter(CascadeInt)
        # Child's original converter is preserved (child wins)
        assert child.converters.has_converter(CascadeStr)

    def test_command_decorator_inherits_converters(self) -> None:
        parent = Command(name="parent")

        @parent.converter(CascadeFloat)
        def parse_cascade_float(value, metadata):
            return CascadeFloat(float(value) * 1.5)

        @parent.command()
        def child():
            pass

        child_cmd = parent.subcommands["child"]
        assert child_cmd.converters is parent.converters
        assert child_cmd.converters.has_converter(CascadeFloat)


class TestValidatorCascading:
    def test_mount_cascades_parameter_validators_to_child(self) -> None:
        parent = Command(name="parent")

        @parent.parameter_validator(CascadeMetadata1)
        def validate_cascade1(
            value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata,
        ):
            return None

        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        parent.mount(child)

        # Child gains parent's validator through merge
        assert child.parameter_validators is not None
        assert child.parameter_validators.has_validator(CascadeMetadata1)

    def test_mount_merges_child_parameter_validator_registry(self) -> None:
        parent_registry = ValidatorRegistry()
        child_registry = ValidatorRegistry()

        parent = Command(name="parent", parameter_validators=parent_registry)
        child = Command(
            name="child",
            run_func=EMPTY_COMMAND_FUNCTION,
            parameter_validators=child_registry,
        )

        @parent.parameter_validator(CascadeMetadata6)
        def parent_validator(
            value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata,
        ):
            return None

        @child.parameter_validator(CascadeMetadata2)
        def child_validator(
            value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata,
        ):
            return None

        # Child has its own registry before mounting
        assert child.parameter_validators is child_registry
        assert child.parameter_validators is not parent.parameter_validators
        assert child.parameter_validators.has_validator(CascadeMetadata2)
        assert parent.parameter_validators.has_validator(CascadeMetadata6)

        # Mount merges parent's validators into child's registry
        parent.mount(child)

        # After merge, child keeps its own registry but gains parent's validators
        assert child.parameter_validators is child_registry
        assert child.parameter_validators is not parent.parameter_validators
        assert child.parameter_validators.has_validator(CascadeMetadata6)
        # Child's original validator is preserved (child wins)
        assert child.parameter_validators.has_validator(CascadeMetadata2)

    def test_command_decorator_inherits_parameter_validators(self) -> None:
        parent = Command(name="parent")

        @parent.parameter_validator(CascadeMetadata3)
        def validate_cascade3(
            value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata,
        ):
            return None

        @parent.command()
        def child():
            pass

        child_cmd = parent.subcommands["child"]
        assert child_cmd.parameter_validators is parent.parameter_validators
        assert parent.parameter_validators is not None
        assert parent.parameter_validators.has_validator(CascadeMetadata3)


class TestLoggerCascading:
    def test_mount_cascades_logger_to_child(self, logger: "Logger") -> None:
        parent = Command(name="parent", logger=logger)

        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        parent.mount(child)

        assert child.logger is logger

    def test_mount_overwrites_child_logger(self, logger: "Logger") -> None:
        parent = Command(name="parent", logger=logger)

        child_logger = MockLogger()
        child = Command(
            name="child", run_func=EMPTY_COMMAND_FUNCTION, logger=child_logger
        )

        # Child has its own logger before mounting
        assert child.logger is child_logger
        assert child.logger is not parent.logger

        # Mount overwrites child's logger with parent's
        parent.mount(child)

        assert child.logger is logger
        assert child.logger is parent.logger

    def test_command_decorator_inherits_logger(self, logger: "Logger") -> None:
        parent = Command(name="parent", logger=logger)

        @parent.command()
        def child():
            pass

        child_cmd = parent.subcommands["child"]
        assert child_cmd.logger is logger


class TestDeepHierarchyCascading:
    def test_four_level_hierarchy_cascading(self, logger: "Logger") -> None:
        root = Command(name="root", logger=logger)

        @root.converter(CascadeInt)
        def parse_cascade_int(value, metadata):
            return CascadeInt(int(value) * 10)

        @root.parameter_validator(CascadeMetadata4)
        def validate_cascade4(
            value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata,
        ):
            return None

        @root.command()
        def level1():
            pass

        @root.subcommands["level1"].command()
        def level2():
            pass

        @root.subcommands["level1"].subcommands["level2"].command()
        def level3():
            pass

        level1_cmd = root.subcommands["level1"]
        level2_cmd = level1_cmd.subcommands["level2"]
        level3_cmd = level2_cmd.subcommands["level3"]

        # All levels share the same registries and logger
        assert level1_cmd.converters is root.converters
        assert level2_cmd.converters is root.converters
        assert level3_cmd.converters is root.converters

        assert level1_cmd.parameter_validators is root.parameter_validators
        assert level2_cmd.parameter_validators is root.parameter_validators
        assert level3_cmd.parameter_validators is root.parameter_validators

        assert level1_cmd.logger is logger
        assert level2_cmd.logger is logger
        assert level3_cmd.logger is logger

    def test_mount_chain_cascading(self, logger: "Logger") -> None:
        root = Command(name="root", logger=logger)

        @root.converter(CascadeFloat)
        def parse_cascade_float(value, metadata):
            return CascadeFloat(float(value))

        level1 = Command(name="level1", run_func=EMPTY_COMMAND_FUNCTION)
        level2 = Command(name="level2", run_func=EMPTY_COMMAND_FUNCTION)
        level3 = Command(name="level3", run_func=EMPTY_COMMAND_FUNCTION)

        root.mount(level1)
        level1.mount(level2)
        level2.mount(level3)

        # Each mount operation merges parent's converters into child
        assert level1.converters.has_converter(CascadeFloat)
        assert level1.logger is logger

        assert level2.converters.has_converter(CascadeFloat)
        assert level2.logger is logger

        assert level3.converters.has_converter(CascadeFloat)
        assert level3.logger is logger

    def test_root_command_accessible_from_all_levels(self) -> None:
        root = Command(name="root")

        @root.command()
        def level1():
            pass

        @root.subcommands["level1"].command()
        def level2():
            pass

        @root.subcommands["level1"].subcommands["level2"].command()
        def level3():
            pass

        level3_cmd = (
            root.subcommands["level1"]
            .subcommands["level2"]
            .subcommands["level3"]
        )
        assert level3_cmd.root_command is root

    def test_mount_cascades_to_nested_subcommands(self, logger: "Logger") -> None:
        parent = Command(name="parent", logger=logger)

        @parent.converter(CascadeInt)
        def parse_cascade_int(value, metadata):
            return CascadeInt(int(value))

        @parent.parameter_validator(CascadeMetadata5)
        def validate_cascade5(
            value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata,
        ):
            return None

        # Create a command with its own subcommand
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        grandchild = Command(name="grandchild", run_func=EMPTY_COMMAND_FUNCTION)
        child.subcommands["grandchild"] = grandchild

        # Mount child (which has grandchild)
        parent.mount(child)

        # Both child and grandchild should have parent's configuration merged in
        assert child.converters.has_converter(CascadeInt)
        assert grandchild.converters.has_converter(CascadeInt)
        assert child.parameter_validators is not None
        assert child.parameter_validators.has_validator(CascadeMetadata5)
        assert grandchild.parameter_validators is not None
        assert grandchild.parameter_validators.has_validator(CascadeMetadata5)
        assert child.logger is logger
        assert grandchild.logger is logger
        assert child.root_command is parent
        assert grandchild.root_command is parent

    def test_mount_multiple_commands_with_subcommands(
        self, logger: "Logger"
    ) -> None:
        root = Command(name="root", logger=logger)

        @root.converter(CascadeInt)
        def parse_int(value, metadata):
            return CascadeInt(int(value))

        # Create two separate command trees
        tree1 = Command(name="tree1", run_func=EMPTY_COMMAND_FUNCTION)
        tree1_child = Command(name="tree1_child", run_func=EMPTY_COMMAND_FUNCTION)
        tree1.subcommands["child"] = tree1_child

        tree2 = Command(name="tree2", run_func=EMPTY_COMMAND_FUNCTION)
        tree2_child = Command(name="tree2_child", run_func=EMPTY_COMMAND_FUNCTION)
        tree2.subcommands["child"] = tree2_child

        # Mount both trees
        root.mount(tree1)
        root.mount(tree2)

        # All nodes in both trees should have root's configuration merged in
        assert tree1.converters.has_converter(CascadeInt)
        assert tree1_child.converters.has_converter(CascadeInt)
        assert tree2.converters.has_converter(CascadeInt)
        assert tree2_child.converters.has_converter(CascadeInt)

        assert tree1.logger is logger
        assert tree1_child.logger is logger
        assert tree2.logger is logger
        assert tree2_child.logger is logger

    def test_mount_deep_hierarchy(self, logger: "Logger") -> None:
        root = Command(name="root", logger=logger)

        @root.converter(CascadeFloat)
        def parse_float(value, metadata):
            return CascadeFloat(float(value))

        # Create a 5-level deep tree
        level1 = Command(name="level1", run_func=EMPTY_COMMAND_FUNCTION)
        level2 = Command(name="level2", run_func=EMPTY_COMMAND_FUNCTION)
        level3 = Command(name="level3", run_func=EMPTY_COMMAND_FUNCTION)
        level4 = Command(name="level4", run_func=EMPTY_COMMAND_FUNCTION)
        level5 = Command(name="level5", run_func=EMPTY_COMMAND_FUNCTION)

        level1.subcommands["level2"] = level2
        level2.subcommands["level3"] = level3
        level3.subcommands["level4"] = level4
        level4.subcommands["level5"] = level5

        # Mount the entire tree
        root.mount(level1)

        # All levels should have cascaded configuration merged in
        for cmd in [level1, level2, level3, level4, level5]:
            assert cmd.converters.has_converter(CascadeFloat)
            assert cmd.logger is logger
            assert cmd.root_command is root

    def test_mount_empty_command_tree(self, logger: "Logger") -> None:
        parent = Command(name="parent", logger=logger)

        @parent.converter(CascadeStr)
        def parse_str(value, metadata):
            return CascadeStr(str(value))

        # Mount a command with no subcommands
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        parent.mount(child)

        assert child.converters.has_converter(CascadeStr)
        assert child.logger is logger
        assert len(child.subcommands) == 0

    def test_parser_config_cascades_when_child_has_none(self) -> None:
        config = object()
        parent = Command(
            name="parent",
            parser_config=config,  # pyright: ignore[reportArgumentType]
        )

        # Create command tree without parser config
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        grandchild = Command(name="grandchild", run_func=EMPTY_COMMAND_FUNCTION)
        child.subcommands["grandchild"] = grandchild

        # Mount and verify parser_config cascades when child doesn't have one
        parent.mount(child)

        assert child.parser_config is config
        assert grandchild.parser_config is config

    def test_command_validators_cascade(self) -> None:
        parent = Command(name="parent")

        @parent.command_validator(CascadeMetadata1)
        def validate_command(
            value: "ParameterValueType | None",
            other_parameters: "Mapping[str, ParameterValueType | None]",
            metadata,
        ):
            return None

        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        grandchild = Command(name="grandchild", run_func=EMPTY_COMMAND_FUNCTION)
        child.subcommands["grandchild"] = grandchild

        parent.mount(child)

        assert child.command_validators is not None
        assert child.command_validators.has_validator(CascadeMetadata1)
        assert grandchild.command_validators is not None
        assert grandchild.command_validators.has_validator(CascadeMetadata1)

    def test_hooks_do_not_cascade(self, logger: "Logger") -> None:
        parent = Command(name="parent", logger=logger)

        # Add a hook to parent (using a simple hook implementation)
        class DummyHook:
            pass

        parent.hook(DummyHook())

        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        grandchild = Command(name="grandchild", run_func=EMPTY_COMMAND_FUNCTION)
        child.subcommands["grandchild"] = grandchild

        parent.mount(child)

        # Hooks should NOT cascade
        assert child.hooks is None
        assert grandchild.hooks is None
        assert parent.hooks is not None


class TestMergeSemantics:
    def test_child_converter_takes_precedence_over_parent(self) -> None:
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        # Both parent and child define converter for the same type
        @parent.converter(CascadeInt)
        def parent_converter(value, metadata):
            return CascadeInt(int(value) * 2)

        @child.converter(CascadeInt)
        def child_converter(value, metadata):
            return CascadeInt(int(value) * 10)

        # Mount child - child's converter should win
        parent.mount(child)

        # Verify child's converter is preserved (not overwritten by parent's)
        result = child.converters.convert("5", CascadeInt)
        assert isinstance(result, CascadeInt)
        assert result.value == 50  # child multiplies by 10, not parent's 2

    def test_child_validator_takes_precedence_over_parent(self) -> None:
        from aclaf.validation import ValidatorRegistry

        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        # Create separate registries to allow duplicate keys
        parent.parameter_validators = ValidatorRegistry()
        child.parameter_validators = ValidatorRegistry()

        parent_called = False
        child_called = False

        @parent.parameter_validator(CascadeMetadata1)
        def parent_validator(
            value: "ParameterValueType | None",
            metadata,
        ):
            nonlocal parent_called
            parent_called = True
            return None

        @child.parameter_validator(CascadeMetadata1)
        def child_validator(
            value: "ParameterValueType | None",
            metadata,
        ):
            nonlocal child_called
            child_called = True
            return None

        parent.mount(child)

        # Validate using child's registry - should call child's validator
        assert child.parameter_validators is not None
        # Create metadata instance (BaseMetadata subclass with no __init__)
        metadata_instance = CascadeMetadata1()
        metadata_instance.value = 10  # pyright: ignore[reportAttributeAccessIssue]
        child.parameter_validators.validate(42, (metadata_instance,))

        assert child_called
        assert not parent_called

    def test_child_inherits_parent_converters_it_doesnt_have(self) -> None:
        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        @parent.converter(CascadeInt)
        def parent_int_converter(value, metadata):
            return CascadeInt(int(value) * 2)

        @parent.converter(CascadeFloat)
        def parent_float_converter(value, metadata):
            return CascadeFloat(float(value) * 1.5)

        # Child only defines converter for CascadeStr
        @child.converter(CascadeStr)
        def child_str_converter(value, metadata):
            return CascadeStr(str(value).upper())

        parent.mount(child)

        # Child should have all three converters
        assert child.converters.has_converter(CascadeInt)
        assert child.converters.has_converter(CascadeFloat)
        assert child.converters.has_converter(CascadeStr)

    def test_child_inherits_parent_validators_it_doesnt_have(self) -> None:
        from aclaf.validation import ValidatorRegistry

        parent = Command(name="parent")
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)

        # Give both parent and child their own validator registries for test isolation
        parent.parameter_validators = ValidatorRegistry()
        child.parameter_validators = ValidatorRegistry()

        @parent.parameter_validator(CascadeMetadata1)
        def parent_validator1(
            value: "ParameterValueType | None",
            metadata,
        ):
            return None

        @parent.parameter_validator(CascadeMetadata2)
        def parent_validator2(
            value: "ParameterValueType | None",
            metadata,
        ):
            return None

        @child.parameter_validator(CascadeMetadata3)
        def child_validator(
            value: "ParameterValueType | None",
            metadata,
        ):
            return None

        parent.mount(child)

        # Child should have all three validators
        assert child.parameter_validators is not None
        assert child.parameter_validators.has_validator(CascadeMetadata1)
        assert child.parameter_validators.has_validator(CascadeMetadata2)
        assert child.parameter_validators.has_validator(CascadeMetadata3)

    def test_logger_always_overwritten_by_parent(self) -> None:
        from aclaf.logging import MockLogger

        parent_logger = MockLogger()
        child_logger = MockLogger()

        parent = Command(name="parent", logger=parent_logger)
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION, logger=child_logger)

        parent.mount(child)

        # Child's logger is always overwritten by parent's (logger is not merged)
        assert child.logger is parent_logger

    def test_logger_set_for_child_with_default_logger(self) -> None:
        from aclaf.logging import MockLogger

        parent_logger = MockLogger()
        parent = Command(name="parent", logger=parent_logger)
        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)  # NullLogger by default

        parent.mount(child)

        assert child.logger is parent_logger

    def test_parser_config_preserved_when_child_has_custom_config(self) -> None:
        parent_config = object()
        child_config = object()

        parent = Command(
            name="parent",
            parser_config=parent_config,  # pyright: ignore[reportArgumentType]
        )
        child = Command(
            name="child",
            run_func=EMPTY_COMMAND_FUNCTION,
            parser_config=child_config,  # pyright: ignore[reportArgumentType]
        )

        parent.mount(child)

        # Child's parser config should be preserved (not overwritten)
        assert child.parser_config is child_config

    def test_multiple_mounts_preserve_child_specific_configuration(self) -> None:
        root = Command(name="root")
        middle = Command(name="middle", run_func=EMPTY_COMMAND_FUNCTION)
        leaf = Command(name="leaf", run_func=EMPTY_COMMAND_FUNCTION)

        @root.converter(CascadeInt)
        def root_converter(value, metadata):
            return CascadeInt(int(value) * 2)

        @middle.converter(CascadeStr)
        def middle_converter(value, metadata):
            return CascadeStr(str(value).upper())

        @leaf.converter(CascadeFloat)
        def leaf_converter(value, metadata):
            return CascadeFloat(float(value) * 1.5)

        # Mount in chain
        root.mount(middle)
        middle.mount(leaf)

        # Leaf should have all three converters
        assert leaf.converters.has_converter(CascadeInt)
        assert leaf.converters.has_converter(CascadeStr)
        assert leaf.converters.has_converter(CascadeFloat)


class TestRecursionDepthValidation:
    def test_excessive_depth_raises_recursion_error(self) -> None:
        import pytest

        root = Command(name="root")
        current = root

        # Create a very deep hierarchy (beyond max depth of 900)
        # Build the chain first without mounting
        for i in range(905):
            child = Command(name=f"level_{i}", run_func=EMPTY_COMMAND_FUNCTION)
            # Manually add to subcommands dict to avoid _add_subcommand check
            current.subcommands[f"level_{i}"] = child
            current = child

        # Manually reset to first level to call cascade
        first_level = root.subcommands["level_0"]

        # Cascading should raise RecursionError
        with pytest.raises(RecursionError, match="exceeds maximum depth"):
            root._cascade_config_recursive(first_level)

    def test_depth_validation_error_message(self) -> None:
        import pytest

        root = Command(name="root")
        current = root

        # Create hierarchy just over the limit
        for i in range(905):
            child = Command(name=f"level_{i}", run_func=EMPTY_COMMAND_FUNCTION)
            current.subcommands[f"level_{i}"] = child
            current = child

        first_level = root.subcommands["level_0"]

        with pytest.raises(
            RecursionError,
            match="Command hierarchy exceeds maximum depth of 900 levels",
        ):
            root._cascade_config_recursive(first_level)

    def test_within_depth_limit_succeeds(self) -> None:
        root = Command(name="root")
        current = root

        # Create a deep but valid hierarchy (well under 900 levels)
        for i in range(50):
            child = Command(name=f"level_{i}", run_func=EMPTY_COMMAND_FUNCTION)
            current.subcommands[f"level_{i}"] = child
            current = child

        first_level = root.subcommands["level_0"]

        # Should not raise
        root._cascade_config_recursive(first_level)
