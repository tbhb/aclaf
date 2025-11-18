import pytest

from aclaf.parser import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    CommandSpec,
    OptionSpec,
    Parser,
    PositionalSpec,
    UnknownOptionError,
)


@pytest.mark.security
class TestLongInputHandling:
    def test_very_long_option_value(self):
        spec = CommandSpec(
            name="cmd",
            options={"data": OptionSpec("data", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # 10 MB string - large but reasonable for a CLI argument
        long_value = "A" * (10 * 1024 * 1024)
        result = parser.parse(["--data", long_value])

        assert isinstance(result.options["data"].value, str)
        assert result.options["data"].value == long_value
        assert len(result.options["data"].value) == 10 * 1024 * 1024

    def test_very_long_option_name(self):
        spec = CommandSpec(
            name="cmd",
            options={"verbose": OptionSpec("verbose", is_flag=True)},
        )
        parser = Parser(spec)

        # 1000-character option name
        long_option = "--" + "x" * 1000

        # Should raise error, not crash
        with pytest.raises(UnknownOptionError) as exc_info:
            _ = parser.parse([long_option])

        # Error message should exist and be reasonable
        error_msg = str(exc_info.value)
        assert error_msg  # Not empty
        assert len(error_msg) < 10000  # Reasonable size

    def test_many_positional_values(self):
        spec = CommandSpec(
            name="cmd",
            positionals={
                "files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY),
            },
        )
        parser = Parser(spec)

        # 10,000 file names
        file_list = [f"file{i}.txt" for i in range(10000)]
        result = parser.parse(file_list)

        assert len(result.positionals["files"].value) == 10000
        assert result.positionals["files"].value == tuple(file_list)

    def test_many_repeated_options(self):
        spec = CommandSpec(
            name="cmd",
            options={"item": OptionSpec("item", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # 1,000 repeated options (last one wins by default)
        args: list[str] = []
        for i in range(1000):
            args.extend(["--item", f"value{i}"])

        result = parser.parse(args)

        # Last value should win
        assert isinstance(result.options["item"].value, str)
        assert result.options["item"].value == "value999"


@pytest.mark.security
class TestUnicodeHandling:
    def test_right_to_left_override_preserved(self):
        spec = CommandSpec(
            name="cmd",
            options={"file": OptionSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # RTL override character
        rtl_override = "\u202e"
        malicious_filename = f"file{rtl_override}txt.exe"

        result = parser.parse(["--file", malicious_filename])

        assert isinstance(result.options["file"].value, str)
        assert result.options["file"].value == malicious_filename
        assert "\u202e" in result.options["file"].value

    def test_zero_width_characters_preserved(self):
        spec = CommandSpec(
            name="cmd",
            options={"username": OptionSpec("username", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Zero-width space in username
        zero_width_space = "\u200b"
        spoofed_username = f"admin{zero_width_space}"

        result = parser.parse(["--username", spoofed_username])

        assert isinstance(result.options["username"].value, str)
        assert result.options["username"].value == spoofed_username
        assert "\u200b" in result.options["username"].value
        # Visually looks like "admin" but is different
        assert result.options["username"].value != "admin"

    def test_null_byte_preserved(self):
        spec = CommandSpec(
            name="cmd",
            options={"data": OptionSpec("data", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Null byte in middle of string
        null_byte_input = "before\x00after"

        result = parser.parse(["--data", null_byte_input])

        assert isinstance(result.options["data"].value, str)
        assert result.options["data"].value == null_byte_input
        assert "\x00" in result.options["data"].value
        # Verify entire string is preserved, not truncated
        assert "before" in result.options["data"].value
        assert "after" in result.options["data"].value

    def test_combining_characters_preserved(self):
        spec = CommandSpec(
            name="cmd",
            options={"text": OptionSpec("text", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # "a" with many combining marks (creates "zalgo text")
        combining_marks = "".join(chr(i) for i in range(0x0300, 0x0310))
        malicious_text = f"a{combining_marks}"

        result = parser.parse(["--text", malicious_text])

        assert isinstance(result.options["text"].value, str)
        assert result.options["text"].value == malicious_text
        # Verify combining characters are preserved
        assert len(result.options["text"].value) > 1

    def test_bidirectional_text_preserved(self):
        spec = CommandSpec(
            name="cmd",
            options={"path": OptionSpec("path", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # Mix LTR and RTL text with control characters
        ltr_mark = "\u200e"  # LEFT-TO-RIGHT MARK
        rtl_mark = "\u200f"  # RIGHT-TO-LEFT MARK
        mixed_text = f"english{rtl_mark}عربي{ltr_mark}english"

        result = parser.parse(["--path", mixed_text])

        assert isinstance(result.options["path"].value, str)
        assert result.options["path"].value == mixed_text
        assert ltr_mark in result.options["path"].value
        assert rtl_mark in result.options["path"].value


@pytest.mark.security
class TestSpecialCharacterHandling:
    def test_newline_in_option_value(self):
        spec = CommandSpec(
            name="cmd",
            options={"message": OptionSpec("message", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        message_with_newline = "First line\nSecond line\nThird line"
        result = parser.parse(["--message", message_with_newline])

        assert isinstance(result.options["message"].value, str)
        assert result.options["message"].value == message_with_newline
        assert "\n" in result.options["message"].value
        assert result.options["message"].value.count("\n") == 2

    def test_carriage_return_preserved(self):
        spec = CommandSpec(
            name="cmd",
            options={"data": OptionSpec("data", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        data_with_cr = "Text\rOverwrite"
        result = parser.parse(["--data", data_with_cr])

        assert isinstance(result.options["data"].value, str)
        assert result.options["data"].value == data_with_cr
        assert "\r" in result.options["data"].value

    def test_tab_characters_preserved(self):
        spec = CommandSpec(
            name="cmd",
            options={"text": OptionSpec("text", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        text_with_tabs = "Column1\tColumn2\tColumn3"
        result = parser.parse(["--text", text_with_tabs])

        assert isinstance(result.options["text"].value, str)
        assert result.options["text"].value == text_with_tabs
        assert "\t" in result.options["text"].value
        assert result.options["text"].value.count("\t") == 2

    def test_backspace_preserved(self):
        spec = CommandSpec(
            name="cmd",
            options={"data": OptionSpec("data", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        data_with_backspace = "Visible\b\b\b\b\b\bHidden"
        result = parser.parse(["--data", data_with_backspace])

        assert isinstance(result.options["data"].value, str)
        assert result.options["data"].value == data_with_backspace
        assert "\b" in result.options["data"].value
