"""Security tests for input validation and sanitization.

This module tests the parser's handling of potentially malicious or malformed
input, including extremely long strings, Unicode attacks, and null byte injection.

## Test categories

### Buffer overflow protection
Tests that the parser handles extremely long input strings without crashes,
memory corruption, or undefined behavior.

### Unicode validation
Tests that the parser correctly handles Unicode edge cases that could be used
for visual spoofing, string manipulation, or bypass attacks.

### Null byte injection
Tests that null bytes are properly handled and don't cause string truncation
or parsing anomalies.

## Security considerations

While the parser operates on Python strings (which handle Unicode natively),
these tests verify that:

1. No crashes occur with extreme input sizes
2. Unicode control characters don't disrupt parsing logic
3. Special characters are preserved for downstream validation
4. Memory usage remains reasonable with large inputs

Applications using this parser must still validate and sanitize values
appropriate to their security context.
"""

import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.exceptions import UnknownOptionError
from aclaf.parser.types import EXACTLY_ONE_ARITY, ONE_OR_MORE_ARITY


@pytest.mark.security
class TestLongInputHandling:
    """Test handling of extremely long input strings."""

    def test_very_long_option_value(self):
        """Parser handles very long option values without crash.

        Buffer overflow attack vector: Provide extremely long strings that might
        overflow fixed-size buffers in poorly written parsers.

        Python strings are dynamic, but this tests for any unexpected behavior
        with large inputs (e.g., performance degradation, memory issues).
        """
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
        """Parser handles very long option names in error reporting.

        Tests that error messages remain reasonable even when unknown option
        names are extremely long (potential DoS through error message generation).
        """
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
        """Parser handles many positional argument values efficiently.

        Tests that accumulating many positional values doesn't cause
        performance degradation or memory issues.
        """
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
        """Parser handles many repeated option occurrences.

        Tests that repeated options don't cause performance or memory issues.
        """
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
    """Test handling of Unicode control characters and edge cases."""

    def test_right_to_left_override_preserved(self):
        """Right-to-left override character is preserved.

        Unicode attack: U+202E (RIGHT-TO-LEFT OVERRIDE)
        Can be used to visually spoof filenames or paths.

        Example: "file\u202etxt.exe" appears as "fileexe.txt" in some contexts.
        """
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
        """Zero-width characters are preserved in option values.

        Unicode attack: U+200B (ZERO WIDTH SPACE), U+FEFF (ZERO WIDTH NO-BREAK SPACE)
        Can be used to bypass string matching or create visually identical but
        distinct strings.
        """
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
        """Null byte is preserved in option values.

        Null byte injection: '\x00' or '\0'
        In C-based systems, null bytes terminate strings. Python strings
        handle them correctly, but this verifies they're preserved for
        downstream validation.
        """
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
        """Combining characters that modify display are preserved.

        Unicode attack: Combining diacritical marks (U+0300-U+036F)
        Can create visually confusing text or bypass filters.
        """
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
        """Bidirectional text markers are preserved.

        Unicode attack: Bidirectional text control characters
        Can be used to create visual spoofing attacks in mixed-direction text.
        """
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
    """Test handling of special characters in various contexts."""

    def test_newline_in_option_value(self):
        """Newlines in option values are preserved.

        Can be used for log injection or to manipulate output formatting.
        """
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
        """Carriage returns are preserved in option values.

        Can be used for terminal manipulation or log injection.
        """
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
        """Tab characters are preserved in option values.

        Tabs can affect output formatting and log parsing.
        """
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
        """Backspace characters are preserved in option values.

        Can be used for terminal manipulation or to hide characters.
        """
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
