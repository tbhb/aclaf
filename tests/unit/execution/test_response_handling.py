# ruff: noqa: SLF001
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from aclaf import ConsoleResponder, Context
from aclaf.console import BasicConsole
from aclaf.parser import ParseResult

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator


class TestSyncResponseHandling:
    def test_none_result_does_nothing(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder.respond(None, context)

        assert output.getvalue() == ""

    def test_simple_value_printed(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder.respond("Hello, World!", context)

        assert "Hello, World!" in output.getvalue()

    def test_generator_yields_multiple_values(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        def generator() -> "Generator[str, None, None]":
            yield "First"
            yield "Second"
            yield "Third"

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder.respond(generator(), context)

        lines = output.getvalue().strip().split("\n")
        assert "First" in lines[0]
        assert "Second" in lines[1]
        assert "Third" in lines[2]

    def test_generator_with_none_values_skipped(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        def generator() -> "Generator[str | None, None, None]":
            yield "Before"
            yield None
            yield "After"

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder.respond(generator(), context)

        lines = output.getvalue().strip().split("\n")
        assert len(lines) == 2
        assert "Before" in lines[0]
        assert "After" in lines[1]

    def test_generator_stop_iteration_value_printed(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        def generator() -> "Generator[str, None, str]":
            yield "During"
            return "Stop value"

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder.respond(generator(), context)

        output_text = output.getvalue()
        assert "During" in output_text
        assert "Stop value" in output_text

    def test_generator_empty_yields_nothing(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        def generator() -> "Generator[str, None, None]":
            return
            yield  # unreachable, but needed for type

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder.respond(generator(), context)

        assert output.getvalue() == ""

    def test_generator_with_none_stop_value(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        def generator() -> "Generator[str, None, None]":
            yield "Value"
            return  # StopIteration with None value

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder.respond(generator(), context)

        output_text = output.getvalue()
        assert "Value" in output_text
        # Should not crash on None stop value


class TestAsyncResponseHandling:
    @pytest.mark.asyncio
    async def test_none_result_does_nothing(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        await responder.respond_async(None, context)

        assert output.getvalue() == ""

    @pytest.mark.asyncio
    async def test_async_generator_yields_printed(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        async def async_gen() -> "AsyncGenerator[str, None]":
            yield "First"
            yield "Second"
            yield "Third"

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        await responder.respond_async(async_gen(), context)

        lines = output.getvalue().strip().split("\n")
        assert "First" in lines[0]
        assert "Second" in lines[1]
        assert "Third" in lines[2]

    @pytest.mark.asyncio
    async def test_async_generator_none_values_skipped(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        async def async_gen() -> "AsyncGenerator[str | None, None]":
            yield "Before"
            yield None
            yield "After"

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        await responder.respond_async(async_gen(), context)

        lines = output.getvalue().strip().split("\n")
        assert len(lines) == 2
        assert "Before" in lines[0]
        assert "After" in lines[1]

    @pytest.mark.asyncio
    async def test_coroutine_awaited_and_printed(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        async def coro() -> str:
            return "Coroutine result"

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        await responder.respond_async(coro(), context)

        assert "Coroutine result" in output.getvalue()

    @pytest.mark.asyncio
    async def test_coroutine_returns_none(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        async def coro() -> None:
            return None

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        await responder.respond_async(coro(), context)

        assert output.getvalue() == ""

    @pytest.mark.asyncio
    async def test_async_generator_empty(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        async def async_gen() -> "AsyncGenerator[str, None]":
            return
            yield  # unreachable, but needed for type

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        await responder.respond_async(async_gen(), context)

        assert output.getvalue() == ""

    @pytest.mark.asyncio
    async def test_sync_value_in_async_context(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        # Pass a sync value to respond_async
        await responder.respond_async("Sync value", context)

        assert "Sync value" in output.getvalue()


class TestProtocolDispatch:
    def test_supports_console_protocol(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        class CustomConsoleResponse:
            console_called: bool

            def __init__(self) -> None:
                self.console_called = False

            def __console__(self, console_obj: BasicConsole) -> None:
                self.console_called = True

        custom = CustomConsoleResponse()
        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder._render_value(custom, context)

        assert custom.console_called is True

    def test_supports_responder_protocol(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        class CustomResponderResponse:
            response_called: bool

            def __init__(self) -> None:
                self.response_called = False

            def __response__(
                self, responder_obj: ConsoleResponder, context_obj: Context
            ) -> None:
                self.response_called = True

        custom = CustomResponderResponse()
        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder._render_value(custom, context)

        assert custom.response_called is True

    def test_supports_print_protocol(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        class CustomPrintResponse:
            def __str__(self) -> str:
                return "Custom string representation"

        custom = CustomPrintResponse()
        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder._render_value(custom, context)

        assert "Custom string representation" in output.getvalue()

    def test_protocol_precedence_console_over_responder(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        class BothProtocols:
            console_called: bool
            response_called: bool

            def __init__(self) -> None:
                self.console_called = False
                self.response_called = False

            def __console__(self, console_obj: BasicConsole) -> None:
                self.console_called = True

            def __response__(
                self, responder_obj: ConsoleResponder, context_obj: Context
            ) -> None:
                self.response_called = True

        custom = BothProtocols()
        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder._render_value(custom, context)

        # SupportsConsole should be called, NOT SupportsResponder
        assert custom.console_called is True
        assert custom.response_called is False

    def test_protocol_precedence_responder_over_print(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        class ResponderAndPrint:
            response_called: bool

            def __init__(self) -> None:
                self.response_called = False

            def __response__(
                self, responder_obj: ConsoleResponder, context_obj: Context
            ) -> None:
                self.response_called = True

            def __str__(self) -> str:
                return "Should not be called"

        custom = ResponderAndPrint()
        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder._render_value(custom, context)

        # SupportsResponder should be called, NOT __str__
        assert custom.response_called is True
        assert "Should not be called" not in output.getvalue()

    def test_none_value_does_nothing(self):
        output = StringIO()
        console = BasicConsole(file=output)
        responder = ConsoleResponder(console=console)

        parse_result = ParseResult(command="test", options={}, positionals={})
        context = Context(
            command="test", command_path=("test",), parse_result=parse_result
        )

        responder._render_value(None, context)

        assert output.getvalue() == ""
