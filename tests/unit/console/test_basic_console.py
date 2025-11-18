import sys
from io import StringIO

from aclaf.console import DEFAULT_END, DEFAULT_SEP, BasicConsole


class TestBasicConsoleCreation:
    def test_default_file_is_stdout(self):
        console = BasicConsole()
        assert console._file is sys.stdout  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    def test_custom_file(self):
        buffer = StringIO()
        console = BasicConsole(file=buffer)
        assert console._file is buffer  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]


class TestBasicConsolePrint:
    def test_print_single_object(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print("hello")

        assert string_buffer.getvalue() == "hello\n"

    def test_print_multiple_objects(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print("hello", "world")

        assert string_buffer.getvalue() == "hello world\n"

    def test_print_custom_separator(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print("a", "b", "c", sep=", ")

        assert string_buffer.getvalue() == "a, b, c\n"

    def test_print_custom_end(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print("hello", end="")

        assert string_buffer.getvalue() == "hello"

    def test_print_no_end(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print("line1", end="")
        console.print("line2", end="")

        assert string_buffer.getvalue() == "line1line2"

    def test_print_multiple_calls(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print("first")
        console.print("second")
        console.print("third")

        assert string_buffer.getvalue() == "first\nsecond\nthird\n"

    def test_print_empty(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print()

        assert string_buffer.getvalue() == "\n"

    def test_print_converts_objects_to_string(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print(42, True, None)  # noqa: FBT003

        assert string_buffer.getvalue() == "42 True None\n"

    def test_print_uses_default_sep(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print("a", "b", "c")

        assert string_buffer.getvalue() == f"a{DEFAULT_SEP}b{DEFAULT_SEP}c{DEFAULT_END}"

    def test_print_uses_default_end(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        console.print("hello")

        assert string_buffer.getvalue() == f"hello{DEFAULT_END}"


class TestBasicConsoleFlush:
    def test_flush_true_flushes_buffer(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        flush_called: list[bool] = []
        original_flush = string_buffer.flush

        def mock_flush():
            flush_called.append(True)
            original_flush()

        string_buffer.flush = mock_flush

        console.print("hello", flush=True)

        assert len(flush_called) == 1
        assert string_buffer.getvalue() == "hello\n"

    def test_flush_false_does_not_flush(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        flush_called: list[bool] = []
        original_flush = string_buffer.flush

        def mock_flush():
            flush_called.append(True)
            original_flush()

        string_buffer.flush = mock_flush

        console.print("hello", flush=False)

        assert len(flush_called) == 0
        assert string_buffer.getvalue() == "hello\n"

    def test_default_flush_is_false(self, string_buffer: StringIO) -> None:
        console = BasicConsole(file=string_buffer)
        flush_called: list[bool] = []
        original_flush = string_buffer.flush

        def mock_flush():
            flush_called.append(True)
            original_flush()

        string_buffer.flush = mock_flush

        console.print("hello")

        assert len(flush_called) == 0
