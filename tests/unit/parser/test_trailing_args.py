from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser._types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
)


class TestBasicTrailingArgs:
    def test_double_dash_starts_trailing_args(self) -> None:
        args = ["--", "a", "b", "c"]
        spec = CommandSpec("cmd")
        parser = Parser(spec)
        result = parser.parse(args)
        assert result.extra_args == ("a", "b", "c")

    def test_empty_trailing_args(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        result = parser.parse(["--"])
        assert result.extra_args == ()

    def test_no_trailing_args(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        result = parser.parse([])
        assert result.extra_args == ()

    def test_single_trailing_arg(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        result = parser.parse(["--", "arg"])
        assert result.extra_args == ("arg",)

    def test_many_trailing_args(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        args = ["--"] + [f"arg{i}" for i in range(100)]
        result = parser.parse(args)
        assert len(result.extra_args) == 100


class TestTrailingArgsWithOptions:
    def test_options_before_trailing_args(self):
        spec = CommandSpec(
            "cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                ),
                "output": OptionSpec(
                    "output", short=frozenset({"o"}), arity=EXACTLY_ONE_ARITY
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(
            ["-v", "--output", "file.txt", "--", "trailing1", "trailing2"]
        )
        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"
        assert result.extra_args == ("trailing1", "trailing2")

    def test_option_like_args_after_double_dash(self):
        spec = CommandSpec(
            "cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--", "-v", "--verbose", "--unknown"])
        assert "verbose" not in result.options
        assert result.extra_args == ("-v", "--verbose", "--unknown")

    def test_options_after_double_dash_ignored(self):
        spec = CommandSpec(
            "cmd",
            options={"verbose": OptionSpec("verbose", arity=ZERO_ARITY)},
        )
        parser = Parser(spec)

        result = parser.parse(["--", "--verbose"])
        assert "verbose" not in result.options
        assert result.extra_args == ("--verbose",)

    def test_short_options_after_double_dash(self):
        spec = CommandSpec(
            "cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
        )
        parser = Parser(spec)

        result = parser.parse(["--", "-v", "-abc"])
        assert result.extra_args == ("-v", "-abc")


class TestTrailingArgsWithPositionals:
    def test_positionals_before_trailing_args(self):
        spec = CommandSpec(
            "cmd",
            positionals={
                "source": PositionalSpec("source", arity=EXACTLY_ONE_ARITY),
                "dest": PositionalSpec("dest", arity=EXACTLY_ONE_ARITY),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["src.txt", "dst.txt", "--", "extra1", "extra2"])
        assert result.positionals["source"].value == "src.txt"
        assert result.positionals["dest"].value == "dst.txt"
        assert result.extra_args == ("extra1", "extra2")

    def test_optional_positionals_before_trailing_args(self):
        spec = CommandSpec(
            "cmd",
            positionals={"files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY)},
        )
        parser = Parser(spec)

        result1 = parser.parse(["--", "trailing"])
        assert result1.positionals["files"].value == ()
        assert result1.extra_args == ("trailing",)

        result2 = parser.parse(["file.txt", "--", "trailing"])
        assert result2.positionals["files"].value == ("file.txt",)
        assert result2.extra_args == ("trailing",)

    def test_greedy_positionals_stop_at_double_dash(self):
        spec = CommandSpec(
            "cmd",
            positionals={"files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)},
        )
        parser = Parser(spec)

        result = parser.parse(["file1.txt", "file2.txt", "--", "extra1", "extra2"])
        assert result.positionals["files"].value == ("file1.txt", "file2.txt")
        assert result.extra_args == ("extra1", "extra2")


class TestTrailingArgsWithSubcommands:
    def test_trailing_args_in_parent_command(self):
        spec = CommandSpec(
            "cmd",
            subcommands={"sub": CommandSpec("sub")},
        )
        parser = Parser(spec)

        result = parser.parse(["--", "trailing"])
        assert result.extra_args == ("trailing",)
        assert result.subcommand is None

    def test_trailing_args_in_subcommand(self):
        spec = CommandSpec(
            "cmd",
            subcommands={"sub": CommandSpec("sub")},
        )
        parser = Parser(spec)

        result = parser.parse(["sub", "--", "trailing1", "trailing2"])
        assert result.subcommand is not None
        assert result.subcommand.command == "sub"
        assert result.subcommand.extra_args == ("trailing1", "trailing2")

    def test_subcommand_with_options_and_trailing_args(self):
        spec = CommandSpec(
            "cmd",
            subcommands={
                "sub": CommandSpec(
                    "sub",
                    options={
                        "verbose": OptionSpec(
                            "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                        )
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["sub", "-v", "--", "trailing"])
        assert result.subcommand is not None
        assert result.subcommand.options["verbose"].value is True
        assert result.subcommand.extra_args == ("trailing",)

    def test_parent_and_subcommand_trailing_args(self):
        spec = CommandSpec(
            "cmd",
            subcommands={"sub": CommandSpec("sub")},
        )
        parser = Parser(spec)

        # The -- before subcommand name means subcommand won't be recognized
        result = parser.parse(["--", "sub", "trailing"])
        assert result.extra_args == ("sub", "trailing")
        assert result.subcommand is None


class TestTrailingArgsEdgeCases:
    def test_double_dash_as_first_argument(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        result = parser.parse(["--", "arg"])
        assert result.extra_args == ("arg",)

    def test_multiple_double_dashes(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        result = parser.parse(["--", "--", "arg"])
        assert result.extra_args == ("--", "arg")

    def test_double_dash_with_empty_strings(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        result = parser.parse(["--", "", "arg", ""])
        assert result.extra_args == ("", "arg", "")

    def test_double_dash_with_special_characters(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        result = parser.parse(["--", "-", "--", "=", "*", "?", "$VAR"])
        assert result.extra_args == ("-", "--", "=", "*", "?", "$VAR")

    def test_trailing_args_with_spaces(self):
        spec = CommandSpec("cmd")
        parser = Parser(spec)

        # In real usage, the shell would handle quotes and pass separate args
        # Here we simulate what the parser would see
        result = parser.parse(["--", "arg with spaces"])
        assert result.extra_args == ("arg with spaces",)


class TestTrailingArgsWithMixedFeatures:
    def test_complex_command_with_everything(self):
        spec = CommandSpec(
            "cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            positionals={"input": PositionalSpec("input", arity=EXACTLY_ONE_ARITY)},
            subcommands={
                "process": CommandSpec(
                    "process",
                    options={
                        "threads": OptionSpec(
                            "threads", short=frozenset({"t"}), arity=EXACTLY_ONE_ARITY
                        )
                    },
                    positionals={
                        "files": PositionalSpec("files", arity=ONE_OR_MORE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "-v",
                "config.yml",
                "process",
                "-t",
                "4",
                "file1.txt",
                "file2.txt",
                "--",
                "extra1",
                "extra2",
            ]
        )
        assert result.options["verbose"].value is True
        assert result.positionals["input"].value == "config.yml"
        assert result.subcommand is not None
        assert result.subcommand.command == "process"
        assert result.subcommand.options["threads"].value == "4"
        assert result.subcommand.positionals["files"].value == (
            "file1.txt",
            "file2.txt",
        )
        assert result.subcommand is not None
        assert result.subcommand.extra_args == ("extra1", "extra2")

    def test_posix_mode_with_trailing_args(self):
        spec = CommandSpec(
            "cmd",
            options={
                "verbose": OptionSpec(
                    "verbose", short=frozenset({"v"}), arity=ZERO_ARITY
                )
            },
            positionals={"file": PositionalSpec("file", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec, strict_options_before_positionals=True)

        result = parser.parse(["-v", "file.txt", "--", "-v"])
        assert result.options["verbose"].value is True
        assert result.positionals["file"].value == "file.txt"
        assert result.extra_args == ("-v",)


class TestTrailingArgsRealWorldExamples:
    def test_git_style_command(self):
        spec = CommandSpec(
            "git",
            subcommands={
                "grep": CommandSpec(
                    "grep",
                    options={
                        "ignore-case": OptionSpec(
                            "ignore-case", short=frozenset({"i"}), arity=ZERO_ARITY
                        )
                    },
                    positionals={
                        "pattern": PositionalSpec("pattern", arity=EXACTLY_ONE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        # git grep -i pattern -- file1 file2
        result = parser.parse(
            ["grep", "-i", "TODO", "--", "src/file1.py", "src/file2.py"]
        )
        assert result.subcommand is not None
        assert result.subcommand.command == "grep"
        assert result.subcommand.options["ignore-case"].value is True
        assert result.subcommand.positionals["pattern"].value == "TODO"
        assert result.subcommand.extra_args == ("src/file1.py", "src/file2.py")

    def test_docker_exec_style_command(self):
        spec = CommandSpec(
            "docker",
            subcommands={
                "exec": CommandSpec(
                    "exec",
                    options={
                        "interactive": OptionSpec(
                            "interactive", short=frozenset({"i"}), arity=ZERO_ARITY
                        ),
                        "tty": OptionSpec(
                            "tty", short=frozenset({"t"}), arity=ZERO_ARITY
                        ),
                    },
                    positionals={
                        "container": PositionalSpec(
                            "container", arity=EXACTLY_ONE_ARITY
                        )
                    },
                ),
            },
        )
        parser = Parser(spec)

        # docker exec -it container -- /bin/bash -c "echo hello"
        result = parser.parse(
            ["exec", "-it", "mycontainer", "--", "/bin/bash", "-c", "echo hello"]
        )
        assert result.subcommand is not None
        assert result.subcommand.options["interactive"].value is True
        assert result.subcommand.options["tty"].value is True
        assert result.subcommand.positionals["container"].value == "mycontainer"
        assert result.subcommand.extra_args == ("/bin/bash", "-c", "echo hello")

    def test_find_exec_style_command(self):
        spec = CommandSpec(
            "find",
            positionals={"path": PositionalSpec("path", arity=EXACTLY_ONE_ARITY)},
            options={"name": OptionSpec("name", arity=EXACTLY_ONE_ARITY)},
        )
        parser = Parser(spec)

        # find . --name "*.txt" -- -exec rm {} \;
        result = parser.parse([".", "--name", "*.txt", "--", "-exec", "rm", "{}", ";"])
        assert result.positionals["path"].value == "."
        assert result.options["name"].value == "*.txt"
        assert result.extra_args == ("-exec", "rm", "{}", ";")
