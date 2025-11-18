# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnusedFunction=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportUnannotatedClassAttribute=false

from typing import TYPE_CHECKING

from aclaf import EMPTY_COMMAND_FUNCTION, Command

if TYPE_CHECKING:
    from aclaf.logging import Logger


class CustomInt:
    """Custom type for testing converters."""

    def __init__(self, value: int) -> None:
        self.value = value


class CustomStr:
    """Custom type for testing converters."""

    def __init__(self, value: str) -> None:
        self.value = value


class CustomFloat:
    """Custom type for testing converters."""

    def __init__(self, value: float) -> None:
        self.value = value


class TestConverterRegistration:
    def test_converter_decorator_registers_converter(self) -> None:
        cmd = Command(name="test")

        @cmd.converter(CustomInt)
        def parse_custom_int(value, metadata):
            return CustomInt(int(value) * 2)

        assert cmd.converters.has_converter(CustomInt)
        assert cmd.converters.get_converter(CustomInt) is parse_custom_int

    def test_converter_decorator_returns_original_function(self) -> None:
        cmd = Command(name="test")

        def parse_custom_int(value, metadata):
            return CustomInt(int(value))

        result = cmd.converter(CustomInt)(parse_custom_int)

        assert result is parse_custom_int

    def test_converter_decorator_with_custom_type(self) -> None:
        cmd = Command(name="test")

        class CustomType:
            def __init__(self, value: str) -> None:
                self.value = value

        @cmd.converter(CustomType)
        def parse_custom(value, metadata):
            return CustomType(str(value))

        assert cmd.converters.has_converter(CustomType)

    def test_multiple_converters_for_different_types(self) -> None:
        cmd = Command(name="test")

        @cmd.converter(CustomInt)
        def parse_custom_int(value, metadata):
            return CustomInt(int(value))

        @cmd.converter(CustomStr)
        def parse_custom_str(value, metadata):
            return CustomStr(str(value).upper())

        assert cmd.converters.has_converter(CustomInt)
        assert cmd.converters.has_converter(CustomStr)
        assert cmd.converters.get_converter(CustomInt) is parse_custom_int
        assert cmd.converters.get_converter(CustomStr) is parse_custom_str

    def test_converter_preserved_in_runtime_command(self) -> None:
        cmd = Command(name="test", run_func=EMPTY_COMMAND_FUNCTION)

        @cmd.converter(CustomInt)
        def parse_custom_int(value, metadata):
            return CustomInt(int(value) * 2)

        runtime = cmd.to_runtime_command()

        assert runtime.converters is cmd.converters
        assert runtime.converters.has_converter(CustomInt)


class TestConverterInheritance:
    def test_command_decorator_inherits_parent_converters(self) -> None:
        parent = Command(name="parent")

        @parent.converter(CustomInt)
        def parse_custom_int(value, metadata):
            return CustomInt(int(value) * 2)

        @parent.command()
        def child():
            pass

        child_cmd = parent.subcommands["child"]
        assert child_cmd.converters is parent.converters
        assert child_cmd.converters.has_converter(CustomInt)
        assert child_cmd.converters.get_converter(CustomInt) is parse_custom_int

    def test_mount_inherits_parent_converters(self) -> None:
        parent = Command(name="parent")

        @parent.converter(CustomInt)
        def parse_custom_int(value, metadata):
            return CustomInt(int(value) * 2)

        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        parent.mount(child)

        assert child.converters is parent.converters
        assert child.converters.has_converter(CustomInt)

    def test_converter_inheritance_transitive(self) -> None:
        root = Command(name="root")

        @root.converter(CustomInt)
        def parse_custom_int(value, metadata):
            return CustomInt(int(value) * 2)

        @root.command()
        def mid():
            pass

        @root.subcommands["mid"].command()
        def leaf():
            pass

        leaf_cmd = root.subcommands["mid"].subcommands["leaf"]
        assert leaf_cmd.converters is root.converters
        assert leaf_cmd.converters.has_converter(CustomInt)


class TestConverterOverride:
    def test_child_cannot_override_parent_converter_via_decorator(self) -> None:
        parent = Command(name="parent")

        @parent.converter(CustomInt)
        def parent_converter(value, metadata):
            return CustomInt(int(value) * 2)

        @parent.command()
        def child():
            pass

        # Child inherits parent's converters registry (same object)
        # Therefore child cannot register a different converter for same type
        child_cmd = parent.subcommands["child"]
        assert child_cmd.converters is parent.converters


class TestConverterCascading:
    def test_converter_cascades_through_mount(self, logger: "Logger") -> None:
        parent = Command(name="parent", logger=logger)

        @parent.converter(CustomInt)
        def parse_custom_int(value, metadata):
            return CustomInt(int(value) * 3)

        child = Command(name="child", run_func=EMPTY_COMMAND_FUNCTION)
        parent.mount(child)

        assert child.converters is parent.converters
        assert child.converters.get_converter(CustomInt) is parse_custom_int

    def test_converter_registry_shared_across_hierarchy(self) -> None:
        root = Command(name="root")

        @root.converter(CustomFloat)
        def parse_custom_float(value, metadata):
            return CustomFloat(float(value) * 1.5)

        @root.command()
        def level1():
            pass

        @root.subcommands["level1"].command()
        def level2():
            pass

        @root.subcommands["level1"].subcommands["level2"].command()
        def level3():
            pass

        # All levels share the same registry
        level1_cmd = root.subcommands["level1"]
        level2_cmd = level1_cmd.subcommands["level2"]
        level3_cmd = level2_cmd.subcommands["level3"]

        assert level1_cmd.converters is root.converters
        assert level2_cmd.converters is root.converters
        assert level3_cmd.converters is root.converters
