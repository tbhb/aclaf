
import pytest

from aclaf import RuntimeCommand, ValidatorRegistry
from aclaf._conversion import ConverterRegistry
from aclaf.parser import ParseResult


class TestAsyncDetection:

    def test_sync_command_returns_false(self):

        def handler():
            pass

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
        )
        parse_result = ParseResult(command="test", options={}, positionals={})

        assert cmd.check_async(parse_result) is False

    def test_async_command_returns_true(self):

        async def handler():
            pass

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
        )
        parse_result = ParseResult(command="test", options={}, positionals={})

        assert cmd.check_async(parse_result) is True

    def test_sync_command_no_subcommand_returns_false(self):

        def handler():
            pass

        cmd = RuntimeCommand(
            name="test",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
        )
        parse_result = ParseResult(
            command="test",
            options={},
            positionals={},
            subcommand=None,
        )

        assert cmd.check_async(parse_result) is False


class TestAsyncPropagationFromSubcommands:

    def test_sync_parent_with_async_subcommand(self):

        def parent_handler():
            pass

        async def child_handler():
            pass

        child = RuntimeCommand(
            name="child",
            run_func=child_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
            subcommands={"child": child},
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="child", options={}, positionals={}),
        )

        assert parent.check_async(parse_result) is True

    def test_sync_parent_with_sync_subcommand(self):

        def parent_handler():
            pass

        def child_handler():
            pass

        child = RuntimeCommand(
            name="child",
            run_func=child_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
            subcommands={"child": child},
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="child", options={}, positionals={}),
        )

        assert parent.check_async(parse_result) is False

    def test_async_parent_returns_true_regardless_of_subcommand(self):

        async def parent_handler():
            pass

        def child_handler():
            pass

        child = RuntimeCommand(
            name="child",
            run_func=child_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
            subcommands={"child": child},
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="child", options={}, positionals={}),
        )

        # Parent is async, so True regardless of child
        assert parent.check_async(parse_result) is True


class TestNestedAsyncPropagation:

    def test_three_level_async_in_leaf(self):

        def root_handler():
            pass

        def mid_handler():
            pass

        async def leaf_handler():
            pass

        leaf = RuntimeCommand(
            name="leaf",
            run_func=leaf_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=True,
        )
        mid = RuntimeCommand(
            name="mid",
            run_func=mid_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
            subcommands={"leaf": leaf},
        )
        root = RuntimeCommand(
            name="root",
            run_func=root_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
            subcommands={"mid": mid},
        )

        parse_result = ParseResult(
            command="root",
            options={},
            positionals={},
            subcommand=ParseResult(
                command="mid",
                options={},
                positionals={},
                subcommand=ParseResult(command="leaf", options={}, positionals={}),
            ),
        )

        assert root.check_async(parse_result) is True

    def test_three_level_all_sync(self):

        def root_handler():
            pass

        def mid_handler():
            pass

        def leaf_handler():
            pass

        leaf = RuntimeCommand(
            name="leaf",
            run_func=leaf_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
        )
        mid = RuntimeCommand(
            name="mid",
            run_func=mid_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
            subcommands={"leaf": leaf},
        )
        root = RuntimeCommand(
            name="root",
            run_func=root_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            is_async=False,
            subcommands={"mid": mid},
        )

        parse_result = ParseResult(
            command="root",
            options={},
            positionals={},
            subcommand=ParseResult(
                command="mid",
                options={},
                positionals={},
                subcommand=ParseResult(command="leaf", options={}, positionals={}),
            ),
        )

        assert root.check_async(parse_result) is False


class TestAsyncDetectionErrorHandling:

    def test_unknown_subcommand_raises_error(self):

        def handler():
            pass

        cmd = RuntimeCommand(
            name="parent",
            run_func=handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            subcommands={},
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="unknown", options={}, positionals={}),
        )

        with pytest.raises(ValueError, match="Unknown subcommand: unknown"):
            _ = cmd.check_async(parse_result)

    def test_missing_subcommand_in_registry(self):

        def parent_handler():
            pass

        def child_handler():
            pass

        # Register "child" but parse result asks for "other"
        child = RuntimeCommand(
            name="child",
            run_func=child_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
        )
        parent = RuntimeCommand(
            name="parent",
            run_func=parent_handler,
            converters=ConverterRegistry(),
            parameter_validators=ValidatorRegistry(),
            subcommands={"child": child},
        )

        parse_result = ParseResult(
            command="parent",
            options={},
            positionals={},
            subcommand=ParseResult(command="other", options={}, positionals={}),
        )

        with pytest.raises(ValueError, match="Unknown subcommand: other"):
            _ = parent.check_async(parse_result)
