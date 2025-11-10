"""Integration tests for Docker-like CLI patterns.

This module tests realistic Docker-style command structures with complex options,
container management patterns, and exec/run scenarios.
"""

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    AccumulationMode,
)


class TestDockerRunCommand:
    """Test Docker run command patterns."""

    def test_run_basic(self):
        """Test Docker run with minimal image-only syntax.

        Verifies the basic Docker run pattern where only an image name is provided
        without additional command arguments. Tests required positional for image
        and optional positional for command with no values.

        Tests:
        - Required positional (image)
        - Optional positional with no values (command)
        - Minimal subcommand invocation

        CLI: docker run ubuntu
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "run": CommandSpec(
                    name="run",
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY),
                        "command": PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["run", "ubuntu"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["image"].value == "ubuntu"
        assert result.subcommand.positionals["command"].value == ()

    def test_run_with_command(self):
        """Test Docker run with image and container command.

        Verifies the pattern where an image is followed by a command to execute
        inside the container. Tests multiple positionals where the first is required
        (image) and subsequent ones are optional (command arguments).

        Tests:
        - Required positional followed by optional ones
        - Zero-or-more arity positional with values
        - Command-as-positionals pattern

        CLI: docker run ubuntu echo hello
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "run": CommandSpec(
                    name="run",
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY),
                        "command": PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["run", "ubuntu", "echo", "hello"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["image"].value == "ubuntu"
        assert result.subcommand.positionals["command"].value == ("echo", "hello")

    def test_run_with_flags(self):
        """Test Docker run with interactive and TTY flags clustered.

        Verifies Docker's common -it flag cluster for interactive terminal sessions.
        Tests short option clustering with two zero-arity flags before positional
        argument. Common pattern for running interactive containers.

        Tests:
        - Short option clustering (-it)
        - Multiple zero-arity flags in cluster
        - Clustered options before positional

        CLI: docker run -it ubuntu
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "run": CommandSpec(
                    name="run",
                    options={
                        "interactive": OptionSpec(
                            "interactive", short=frozenset({"i"}), arity=ZERO_ARITY
                        ),
                        "tty": OptionSpec(
                            "tty", short=frozenset({"t"}), arity=ZERO_ARITY
                        ),
                    },
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["run", "-it", "ubuntu"])
        assert result.subcommand is not None
        assert result.subcommand.options["interactive"].value is True
        assert result.subcommand.options["tty"].value is True
        assert result.subcommand.positionals["image"].value == "ubuntu"

    def test_run_with_remove_flag(self):
        """Test Docker run with auto-remove cleanup flag.

        Verifies the pattern where a long boolean flag modifies container lifecycle
        behavior (automatically remove on exit). Tests long zero-arity option before
        required positional.

        Tests:
        - Long zero-arity option (--rm)
        - Option before required positional
        - Cleanup behavior flag

        CLI: docker run --rm ubuntu
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "run": CommandSpec(
                    name="run",
                    options={"rm": OptionSpec("rm", arity=ZERO_ARITY)},
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["run", "--rm", "ubuntu"])
        assert result.subcommand is not None
        assert result.subcommand.options["rm"].value is True

    def test_run_with_environment_variables(self):
        """Test Docker run with environment variable option and COLLECT mode.

        Verifies the pattern where environment variables are passed via repeated
        -e flags, each taking one value. Uses COLLECT accumulation mode to gather
        all environment variable assignments. Common for configuring containers.

        Tests:
        - Value-taking option with COLLECT mode
        - Repeated option for multiple values
        - Environment variable passing pattern

        CLI: docker run -e VAR=value ubuntu
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "run": CommandSpec(
                    name="run",
                    options={
                        "env": OptionSpec(
                            "env",
                            short=frozenset({"e"}),
                            arity=EXACTLY_ONE_ARITY,
                            accumulation_mode=AccumulationMode.COLLECT,
                        )
                    },
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["run", "-e", "VAR=value", "ubuntu"])
        assert result.subcommand is not None
        assert result.subcommand.options["env"].value == ("VAR=value",)

    def test_run_complex(self):
        """Test Docker run with complex option combination and command.

        Verifies realistic Docker run with multiple option types: clustered flags
        (-it), long boolean (--rm), accumulated value option (-e), image, and
        container command. Tests comprehensive option-positional interaction.

        Tests:
        - Clustered zero-arity options (-it)
        - Long zero-arity option (--rm)
        - COLLECT accumulation mode (-e)
        - Multiple positionals (image, command)
        - Complex real-world option combination

        CLI: docker run -it --rm -e VAR=val ubuntu /bin/bash
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "run": CommandSpec(
                    name="run",
                    options={
                        "interactive": OptionSpec(
                            "interactive", short=frozenset({"i"}), arity=ZERO_ARITY
                        ),
                        "tty": OptionSpec(
                            "tty", short=frozenset({"t"}), arity=ZERO_ARITY
                        ),
                        "rm": OptionSpec("rm", arity=ZERO_ARITY),
                        "env": OptionSpec(
                            "env",
                            short=frozenset({"e"}),
                            arity=EXACTLY_ONE_ARITY,
                            accumulation_mode=AccumulationMode.COLLECT,
                        ),
                    },
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY),
                        "command": PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(
            ["run", "-it", "--rm", "-e", "VAR=val", "ubuntu", "/bin/bash"]
        )
        assert result.subcommand is not None
        assert result.subcommand.options["interactive"].value is True
        assert result.subcommand.options["tty"].value is True
        assert result.subcommand.options["rm"].value is True
        assert result.subcommand.options["env"].value == ("VAR=val",)
        assert result.subcommand.positionals["image"].value == "ubuntu"
        assert result.subcommand.positionals["command"].value == ("/bin/bash",)


class TestDockerExecCommand:
    """Test Docker exec command patterns."""

    def test_exec_basic(self):
        """Test Docker exec with container name and command arguments.

        Verifies the exec pattern where a container name is followed by a command
        and its arguments. Tests two positionals: one required (container), one
        requiring at least one value (command).

        Tests:
        - Required positional (container)
        - One-or-more arity positional (command)
        - Multiple positional values for command

        CLI: docker exec mycontainer ls -la
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "exec": CommandSpec(
                    name="exec",
                    positionals={
                        "container": PositionalSpec(
                            "container", arity=EXACTLY_ONE_ARITY
                        ),
                        "command": PositionalSpec("command", arity=ONE_OR_MORE_ARITY),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["exec", "mycontainer", "ls", "-la"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["container"].value == "mycontainer"
        assert result.subcommand.positionals["command"].value == ("ls", "-la")

    def test_exec_with_flags(self):
        """Test Docker exec with interactive flags and shell command.

        Verifies the exec pattern with clustered -it flags for interactive terminal
        sessions in running containers. Common pattern for debugging containers.
        Tests option cluster before multiple positionals.

        Tests:
        - Clustered zero-arity options (-it)
        - Options before multiple positionals
        - Interactive exec pattern

        CLI: docker exec -it mycontainer bash
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "exec": CommandSpec(
                    name="exec",
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
                        ),
                        "command": PositionalSpec("command", arity=ONE_OR_MORE_ARITY),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["exec", "-it", "mycontainer", "bash"])
        assert result.subcommand is not None
        assert result.subcommand.options["interactive"].value is True
        assert result.subcommand.options["tty"].value is True
        assert result.subcommand.positionals["container"].value == "mycontainer"
        assert result.subcommand.positionals["command"].value == ("bash",)


class TestDockerPsCommand:
    """Test Docker ps command patterns."""

    def test_ps_default(self):
        """Test Docker ps with no arguments for default listing.

        Verifies the simple list-containers pattern with no options or arguments.
        Tests subcommand invocation with all options and positionals using default
        values.

        Tests:
        - Subcommand with no arguments
        - Default option behavior
        - Simple listing pattern

        CLI: docker ps
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "ps": CommandSpec(
                    name="ps",
                    options={
                        "all": OptionSpec(
                            "all", short=frozenset({"a"}), arity=ZERO_ARITY
                        ),
                        "quiet": OptionSpec(
                            "quiet", short=frozenset({"q"}), arity=ZERO_ARITY
                        ),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["ps"])
        assert result.subcommand is not None
        assert result.subcommand.command == "ps"

    def test_ps_all(self):
        """Test Docker ps with all-containers flag.

        Verifies the pattern where a flag modifies listing behavior to show all
        containers (not just running ones). Tests simple flag-only subcommand usage.

        Tests:
        - Single short zero-arity option
        - Flag modifying list behavior
        - No positional arguments

        CLI: docker ps -a
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "ps": CommandSpec(
                    name="ps",
                    options={
                        "all": OptionSpec(
                            "all", short=frozenset({"a"}), arity=ZERO_ARITY
                        )
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["ps", "-a"])
        assert result.subcommand is not None
        assert result.subcommand.options["all"].value is True

    def test_ps_quiet(self):
        """Test Docker ps with clustered display control flags.

        Verifies the pattern of combining multiple output control flags (-a for all,
        -q for quiet/IDs only). Tests flag clustering for list customization without
        positional arguments.

        Tests:
        - Flag clustering with multiple options
        - Combined output control flags
        - No positional arguments

        CLI: docker ps -aq
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "ps": CommandSpec(
                    name="ps",
                    options={
                        "all": OptionSpec(
                            "all", short=frozenset({"a"}), arity=ZERO_ARITY
                        ),
                        "quiet": OptionSpec(
                            "quiet", short=frozenset({"q"}), arity=ZERO_ARITY
                        ),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["ps", "-aq"])
        assert result.subcommand is not None
        assert result.subcommand.options["all"].value is True
        assert result.subcommand.options["quiet"].value is True


class TestDockerBuildCommand:
    """Test Docker build command patterns."""

    def test_build_basic(self):
        """Test Docker build with minimal context-only syntax.

        Verifies the basic build pattern with only a build context path. Tests
        required positional for build context (often current directory ".").

        Tests:
        - Single required positional
        - Build context as positional
        - Minimal build command

        CLI: docker build .
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "build": CommandSpec(
                    name="build",
                    positionals={
                        "context": PositionalSpec("context", arity=EXACTLY_ONE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["build", "."])
        assert result.subcommand is not None
        assert result.subcommand.positionals["context"].value == "."

    def test_build_with_tag(self):
        """Test Docker build with image tag option.

        Verifies the pattern where an option specifies the output image name/tag
        before the build context. Common for naming built images. Tests value-taking
        option before required positional.

        Tests:
        - Short option with value (-t)
        - Image tag specification
        - Option before required positional

        CLI: docker build -t myimage:latest .
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "build": CommandSpec(
                    name="build",
                    options={
                        "tag": OptionSpec(
                            "tag", short=frozenset({"t"}), arity=EXACTLY_ONE_ARITY
                        )
                    },
                    positionals={
                        "context": PositionalSpec("context", arity=EXACTLY_ONE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["build", "-t", "myimage:latest", "."])
        assert result.subcommand is not None
        assert result.subcommand.options["tag"].value == "myimage:latest"
        assert result.subcommand.positionals["context"].value == "."

    def test_build_with_file(self):
        """Test Docker build with custom Dockerfile and tag.

        Verifies the pattern of specifying both a custom Dockerfile path and output
        tag before the build context. Tests multiple value-taking options before
        required positional.

        Tests:
        - Multiple value-taking options (-f, -t)
        - Custom Dockerfile path
        - Option order independence
        - Options before required positional

        CLI: docker build -f Dockerfile.prod -t myimage .
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "build": CommandSpec(
                    name="build",
                    options={
                        "file": OptionSpec(
                            "file", short=frozenset({"f"}), arity=EXACTLY_ONE_ARITY
                        ),
                        "tag": OptionSpec(
                            "tag", short=frozenset({"t"}), arity=EXACTLY_ONE_ARITY
                        ),
                    },
                    positionals={
                        "context": PositionalSpec("context", arity=EXACTLY_ONE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["build", "-f", "Dockerfile.prod", "-t", "myimage", "."])
        assert result.subcommand is not None
        assert result.subcommand.options["file"].value == "Dockerfile.prod"
        assert result.subcommand.options["tag"].value == "myimage"


class TestDockerVolumeCommand:
    """Test Docker volume commands with nested subcommands."""

    def test_volume_create(self):
        """Test Docker nested volume create subcommand.

        Verifies Docker's two-level subcommand structure for volume management
        (volume -> create). Tests nested subcommands with optional positional for
        volume name.

        Tests:
        - Two-level subcommand nesting
        - Optional positional at nested level
        - Volume management pattern

        CLI: docker volume create myvolume
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "volume": CommandSpec(
                    name="volume",
                    subcommands={
                        "create": CommandSpec(
                            name="create",
                            positionals={
                                "name": PositionalSpec("name", arity=ZERO_OR_MORE_ARITY)
                            },
                        ),
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["volume", "create", "myvolume"])
        assert result.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "create"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.positionals["name"].value == ("myvolume",)

    def test_volume_list(self):
        """Test Docker nested volume list with aliased subcommand.

        Verifies the pattern where nested subcommands have short aliases (ls for list).
        Tests alias resolution in two-level subcommand structures.

        Tests:
        - Two-level subcommand nesting
        - Nested subcommand aliases
        - Alias resolution at depth

        CLI: docker volume ls
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "volume": CommandSpec(
                    name="volume",
                    subcommands={
                        "ls": CommandSpec(name="ls", aliases=frozenset({"list"})),
                    },
                ),
            },
        )
        parser = Parser(spec, allow_aliases=True)

        result = parser.parse(["volume", "ls"])
        assert result.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "ls"


class TestComplexDockerScenarios:
    """Test complex multi-feature Docker scenarios."""

    def test_complete_docker_cli(self):
        """Test comprehensive Docker CLI with multiple subcommand families.

        Verifies a realistic Docker CLI specification with diverse subcommands (run,
        ps, exec) each having different option and positional patterns. Tests parser
        stability and spec reuse across different command invocations.

        Tests:
        - Multiple diverse subcommands
        - Global options
        - Parser reuse across commands
        - Heterogeneous subcommand patterns

        CLI: docker run -it ubuntu, docker ps -a, docker exec container bash
        """
        spec = CommandSpec(
            name="docker",
            options={"version": OptionSpec("version", arity=ZERO_ARITY)},
            subcommands={
                "run": CommandSpec(
                    name="run",
                    options={
                        "interactive": OptionSpec(
                            "interactive", short=frozenset({"i"}), arity=ZERO_ARITY
                        ),
                        "tty": OptionSpec(
                            "tty", short=frozenset({"t"}), arity=ZERO_ARITY
                        ),
                        "rm": OptionSpec("rm", arity=ZERO_ARITY),
                    },
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY),
                        "command": PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                    },
                ),
                "ps": CommandSpec(
                    name="ps",
                    options={
                        "all": OptionSpec(
                            "all", short=frozenset({"a"}), arity=ZERO_ARITY
                        ),
                        "quiet": OptionSpec(
                            "quiet", short=frozenset({"q"}), arity=ZERO_ARITY
                        ),
                    },
                ),
                "exec": CommandSpec(
                    name="exec",
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
                        ),
                        "command": PositionalSpec("command", arity=ONE_OR_MORE_ARITY),
                    },
                ),
            },
        )
        parser = Parser(spec)

        # Test multiple commands
        result1 = parser.parse(["run", "-it", "ubuntu"])
        assert result1.subcommand is not None
        assert result1.subcommand.command == "run"

        result2 = parser.parse(["ps", "-a"])
        assert result2.subcommand is not None
        assert result2.subcommand.command == "ps"

        result3 = parser.parse(["exec", "container", "bash"])
        assert result3.subcommand is not None
        assert result3.subcommand.command == "exec"

    def test_docker_run_with_port_mappings(self):
        """Test Docker run with multiple port mapping options.

        Verifies the pattern of repeated -p flags to map multiple ports using COLLECT
        accumulation mode. Common for exposing multiple container ports. Tests option
        repetition and value collection.

        Tests:
        - COLLECT accumulation mode
        - Repeated value-taking options (-p)
        - Multiple port mappings
        - Accumulated values tuple

        CLI: docker run -p 8080:80 -p 443:443 nginx
        """
        spec = CommandSpec(
            name="docker",
            subcommands={
                "run": CommandSpec(
                    name="run",
                    options={
                        "publish": OptionSpec(
                            "publish",
                            short=frozenset({"p"}),
                            arity=EXACTLY_ONE_ARITY,
                            accumulation_mode=AccumulationMode.COLLECT,
                        ),
                    },
                    positionals={
                        "image": PositionalSpec("image", arity=EXACTLY_ONE_ARITY)
                    },
                ),
            },
        )
        parser = Parser(spec)

        result = parser.parse(["run", "-p", "8080:80", "-p", "443:443", "nginx"])
        assert result.subcommand is not None
        assert result.subcommand.options["publish"].value == ("8080:80", "443:443")
        assert result.subcommand.positionals["image"].value == "nginx"
