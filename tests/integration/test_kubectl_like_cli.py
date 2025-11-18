"""Integration tests for Kubernetes kubectl-like CLI patterns using the App API.

This module tests realistic kubectl-style command structures with resource type + name
patterns, namespace flags, output formats, and various argument patterns using the
high-level App API.

Contains integration tests organized into test classes covering:
- Resource operations (get, describe, delete, apply)
- Pod interaction (logs, exec)
- Global flags (namespace, context, kubeconfig)
- Complex multi-command scenarios

Demonstrates validation system integration with:
- Replica counts (positive integers, typically 0-10000)
- Timeout seconds (positive integers)
- Non-empty resource names
- Tail line counts (positive integers)

Note: This file intentionally uses patterns that trigger linting warnings:
- FBT002: Boolean arguments are part of the CLI API being tested
- A001: Function name 'exec' shadows builtin but matches actual kubectl CLI
- PLR0915: test_complete_kubectl_cli is intentionally long to test
  comprehensive scenarios
- TC001: MockConsole is used at runtime, not just for type checking
"""

# ruff: noqa: FBT002, A001, PLR0915, TC001

from typing import Annotated

import pytest
from annotated_types import Interval, MinLen

from aclaf import App
from aclaf.console import MockConsole
from aclaf.exceptions import ValidationError
from aclaf.metadata import AtLeastOne, Collect, Opt, ZeroOrMore
from aclaf.types import PositiveInt

# Type aliases for Kubernetes-specific constraints
ReplicaCount = Annotated[int, Interval(ge=0, le=10000)]
TimeoutSeconds = PositiveInt
TailLines = PositiveInt
NonEmptyResourceName = Annotated[str, MinLen(1)]


@pytest.fixture
def kubectl_get_cli(console: MockConsole) -> App:
    """Kubectl CLI with get command for most get tests."""
    app = App("kubectl", console=console)

    @app.command()
    def get(  # pyright: ignore[reportUnusedFunction]
        resource_type: str,
        resource_names: Annotated[tuple[str, ...], ZeroOrMore()] = (),
        output: Annotated[str | None, "-o"] = None,
        watch: Annotated[bool, "-w"] = False,
        all_namespaces: Annotated[bool, "-A"] = False,
    ):
        console.print(f"[get] resource_type={resource_type}")
        if resource_names:
            console.print(f"[get] resource_names={resource_names!r}")
        if output:
            console.print(f"[get] output={output}")
        if watch:
            console.print("[get] watch=True")
        if all_namespaces:
            console.print("[get] all_namespaces=True")

    return app


@pytest.fixture
def kubectl_cli_with_namespace(console: MockConsole) -> App:
    """Kubectl CLI with global namespace flag for namespace tests."""
    app = App("kubectl", console=console)

    @app.handler()
    def kubectl(namespace: Annotated[str | None, "-n"] = None):  # pyright: ignore[reportUnusedFunction]
        if namespace:
            console.print(f"[kubectl] namespace={namespace}")

    @app.command()
    def get(resource_type: str):  # pyright: ignore[reportUnusedFunction]
        console.print(f"[get] resource_type={resource_type}")

    return app


@pytest.fixture
def kubectl_exec_cli(console: MockConsole) -> App:
    """Kubectl CLI with exec command for most exec tests."""
    app = App("kubectl", console=console)

    @app.command()
    def exec(  # pyright: ignore[reportUnusedFunction]
        pod_name: str,
        command: Annotated[tuple[str, ...], ZeroOrMore()] = (),
        interactive: Annotated[bool, "-i"] = False,
        tty: Annotated[bool, "-t"] = False,
        container: Annotated[str | None, "-c"] = None,
    ):
        console.print(f"[exec] pod_name={pod_name}")
        if interactive:
            console.print("[exec] interactive=True")
        if tty:
            console.print("[exec] tty=True")
        if container:
            console.print(f"[exec] container={container}")
        if command:
            console.print(f"[exec] command={command!r}")

    return app


class TestKubectlGetCommand:
    def test_get_pods(self, kubectl_get_cli: App, console: MockConsole):
        kubectl_get_cli(["get", "pods"])

        output = console.get_output()
        assert "[get] resource_type=pods" in output

    def test_get_specific_pod(self, kubectl_get_cli: App, console: MockConsole):
        kubectl_get_cli(["get", "pod", "my-pod"])

        output = console.get_output()
        assert "[get] resource_type=pod" in output
        assert "[get] resource_names=('my-pod',)" in output

    def test_get_multiple_pods(self, kubectl_get_cli: App, console: MockConsole):
        kubectl_get_cli(["get", "pods", "pod1", "pod2", "pod3"])

        output = console.get_output()
        assert "[get] resource_type=pods" in output
        assert "[get] resource_names=('pod1', 'pod2', 'pod3')" in output

    def test_get_with_output_format(self, kubectl_get_cli: App, console: MockConsole):
        kubectl_get_cli(["get", "pods", "-o", "yaml"])

        output = console.get_output()
        assert "[get] output=yaml" in output
        assert "[get] resource_type=pods" in output

    def test_get_with_watch(self, kubectl_get_cli: App, console: MockConsole):
        kubectl_get_cli(["get", "pods", "--watch"])

        output = console.get_output()
        assert "[get] watch=True" in output

    def test_get_with_watch_short(self, kubectl_get_cli: App, console: MockConsole):
        kubectl_get_cli(["get", "pods", "-w"])

        output = console.get_output()
        assert "[get] watch=True" in output

    def test_get_with_all_namespaces(self, kubectl_get_cli: App, console: MockConsole):
        kubectl_get_cli(["get", "pods", "--all-namespaces"])

        output = console.get_output()
        assert "[get] all_namespaces=True" in output

    def test_get_with_all_namespaces_short(
        self, kubectl_get_cli: App, console: MockConsole
    ):
        kubectl_get_cli(["get", "pods", "-A"])

        output = console.get_output()
        assert "[get] all_namespaces=True" in output


class TestKubectlDescribeCommand:
    def test_describe_pod(self, console: MockConsole):
        # Inline CLI construction - simple, consistent signature
        app = App("kubectl", console=console)

        @app.command()
        def describe(resource_type: str, resource_name: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[describe] resource_type={resource_type}")
            console.print(f"[describe] resource_name={resource_name}")

        app(["describe", "pod", "my-pod"])

        output = console.get_output()
        assert "[describe] resource_type=pod" in output
        assert "[describe] resource_name=my-pod" in output

    def test_describe_deployment(self, console: MockConsole):
        # Inline CLI construction - simple, consistent signature
        app = App("kubectl", console=console)

        @app.command()
        def describe(resource_type: str, resource_name: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[describe] resource_type={resource_type}")
            console.print(f"[describe] resource_name={resource_name}")

        app(["describe", "deployment", "my-app"])

        output = console.get_output()
        assert "[describe] resource_type=deployment" in output
        assert "[describe] resource_name=my-app" in output


class TestKubectlDeleteCommand:
    def test_delete_pod(self, console: MockConsole):
        # Inline CLI construction - uses AtLeastOne validation
        app = App("kubectl", console=console)

        @app.command()
        def delete(  # pyright: ignore[reportUnusedFunction]
            resource_type: str, resource_names: Annotated[tuple[str, ...], AtLeastOne()]
        ):
            console.print(f"[delete] resource_type={resource_type}")
            console.print(f"[delete] resource_names={resource_names!r}")

        app(["delete", "pod", "my-pod"])

        output = console.get_output()
        assert "[delete] resource_type=pod" in output
        assert "[delete] resource_names=('my-pod',)" in output

    def test_delete_multiple_pods(self, console: MockConsole):
        # Inline CLI construction - uses AtLeastOne validation
        app = App("kubectl", console=console)

        @app.command()
        def delete(  # pyright: ignore[reportUnusedFunction]
            resource_type: str, resource_names: Annotated[tuple[str, ...], AtLeastOne()]
        ):
            console.print(f"[delete] resource_type={resource_type}")
            console.print(f"[delete] resource_names={resource_names!r}")

        app(["delete", "pods", "pod1", "pod2"])

        output = console.get_output()
        assert "[delete] resource_names=('pod1', 'pod2')" in output

    def test_delete_deployment(self, console: MockConsole):
        # Inline CLI construction - uses AtLeastOne validation
        app = App("kubectl", console=console)

        @app.command()
        def delete(  # pyright: ignore[reportUnusedFunction]
            resource_type: str, resource_names: Annotated[tuple[str, ...], AtLeastOne()]
        ):
            console.print(f"[delete] resource_type={resource_type}")
            console.print(f"[delete] resource_names={resource_names!r}")

        app(["delete", "deployment", "my-app"])

        output = console.get_output()
        assert "[delete] resource_type=deployment" in output
        assert "[delete] resource_names=('my-app',)" in output


class TestKubectlApplyCommand:
    def test_apply_with_file(self, console: MockConsole):
        # Inline CLI construction - apply uses Collect() for repeatable -f flags
        app = App("kubectl", console=console)

        @app.command()
        def apply(filename: Annotated[tuple[str, ...], "-f", Collect()]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[apply] filename={filename!r}")

        app(["apply", "-f", "manifest.yaml"])

        output = console.get_output()
        assert "[apply] filename=('manifest.yaml',)" in output

    def test_apply_multiple_files(self, console: MockConsole):
        # Inline CLI construction - apply uses Collect() for repeatable -f flags
        app = App("kubectl", console=console)

        @app.command()
        def apply(filename: Annotated[tuple[str, ...], "-f", Collect()]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[apply] filename={filename!r}")

        app(["apply", "-f", "file1.yaml", "-f", "file2.yaml"])

        output = console.get_output()
        assert "[apply] filename=('file1.yaml', 'file2.yaml')" in output


class TestKubectlLogsCommand:
    def test_logs_basic(self, console: MockConsole):
        # Inline CLI construction - logs has simple signature, different in each test
        app = App("kubectl", console=console)

        @app.command()
        def logs(pod_name: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[logs] pod_name={pod_name}")

        app(["logs", "my-pod"])

        output = console.get_output()
        assert "[logs] pod_name=my-pod" in output

    def test_logs_with_follow(self, console: MockConsole):
        # Inline CLI construction - signature varies by test
        app = App("kubectl", console=console)

        @app.command()
        def logs(pod_name: str, follow: Annotated[bool, "-f"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[logs] pod_name={pod_name}")
            if follow:
                console.print("[logs] follow=True")

        app(["logs", "my-pod", "--follow"])

        output = console.get_output()
        assert "[logs] follow=True" in output
        assert "[logs] pod_name=my-pod" in output

    def test_logs_with_follow_short(self, console: MockConsole):
        # Inline CLI construction - signature varies by test
        app = App("kubectl", console=console)

        @app.command()
        def logs(pod_name: str, follow: Annotated[bool, "-f"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[logs] pod_name={pod_name}")
            if follow:
                console.print("[logs] follow=True")

        app(["logs", "my-pod", "-f"])

        output = console.get_output()
        assert "[logs] follow=True" in output

    def test_logs_with_tail_valid(
        self, console: MockConsole):
        """Test logs command with valid tail line count."""
        app = App("kubectl", console=console)

        @app.command()
        def logs(
            pod_name: NonEmptyResourceName,
            tail: Annotated[TailLines | None, Opt()] = None,
            follow: Annotated[bool, "-f"] = False,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[logs] pod_name={pod_name}")
            if tail:
                console.print(f"[logs] tail={tail}")
            if follow:
                console.print("[logs] follow=True")

        app(["logs", "my-pod", "--tail", "100", "-f"])

        output = console.get_output()
        assert "[logs] pod_name=my-pod" in output
        assert "[logs] tail=100" in output
        assert "[logs] follow=True" in output

class TestKubectlExecCommand:
    def test_exec_basic(self, kubectl_exec_cli: App, console: MockConsole):
        kubectl_exec_cli(["exec", "my-pod", "env"])

        output = console.get_output()
        assert "[exec] pod_name=my-pod" in output
        assert "[exec] command=('env',)" in output

    def test_exec_interactive(self, kubectl_exec_cli: App, console: MockConsole):
        kubectl_exec_cli(["exec", "-it", "my-pod", "/bin/bash"])

        output = console.get_output()
        assert "[exec] interactive=True" in output
        assert "[exec] tty=True" in output
        assert "[exec] pod_name=my-pod" in output
        assert "[exec] command=('/bin/bash',)" in output

    def test_exec_with_container_flag(
        self, kubectl_exec_cli: App, console: MockConsole
    ):
        kubectl_exec_cli(["exec", "my-pod", "-c", "container-name", "env"])

        output = console.get_output()
        assert "[exec] container=container-name" in output
        assert "[exec] pod_name=my-pod" in output
        assert "[exec] command=('env',)" in output


class TestKubectlGlobalFlags:
    def test_namespace_flag(
        self, kubectl_cli_with_namespace: App, console: MockConsole
    ):
        kubectl_cli_with_namespace(["--namespace", "kube-system", "get", "pods"])

        output = console.get_output()
        assert "[kubectl] namespace=kube-system" in output
        assert "[get] resource_type=pods" in output

    def test_namespace_flag_short(
        self, kubectl_cli_with_namespace: App, console: MockConsole
    ):
        kubectl_cli_with_namespace(["-n", "kube-system", "get", "pods"])

        output = console.get_output()
        assert "[kubectl] namespace=kube-system" in output

    def test_context_flag(self, console: MockConsole):
        # Inline CLI construction - testing specific global flag (context) with Opt()
        app = App("kubectl", console=console)

        @app.handler()
        def kubectl(context: Annotated[str | None, Opt()] = None):  # pyright: ignore[reportUnusedFunction]
            if context:
                console.print(f"[kubectl] context={context}")

        @app.command()
        def get(resource_type: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[get] resource_type={resource_type}")

        app(["--context", "production", "get", "pods"])

        output = console.get_output()
        assert "[kubectl] context=production" in output
        assert "[get] resource_type=pods" in output

    def test_kubeconfig_flag(self, console: MockConsole):
        # Inline CLI construction - testing specific global flag (kubeconfig) with Opt()
        app = App("kubectl", console=console)

        @app.handler()
        def kubectl(kubeconfig: Annotated[str | None, Opt()] = None):  # pyright: ignore[reportUnusedFunction]
            if kubeconfig:
                console.print(f"[kubectl] kubeconfig={kubeconfig}")

        @app.command()
        def get(resource_type: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[get] resource_type={resource_type}")

        app(["--kubeconfig", "~/.kube/custom-config", "get", "pods"])

        output = console.get_output()
        assert "[kubectl] kubeconfig=~/.kube/custom-config" in output

    def test_multiple_global_flags(self, console: MockConsole):
        # Inline CLI construction - testing combination of multiple global flags
        app = App("kubectl", console=console)

        @app.handler()
        def kubectl(  # pyright: ignore[reportUnusedFunction]
            namespace: Annotated[str | None, "-n"] = None,
            context: Annotated[str | None, Opt()] = None,
        ):
            if namespace:
                console.print(f"[kubectl] namespace={namespace}")
            if context:
                console.print(f"[kubectl] context={context}")

        @app.command()
        def get(resource_type: str, output: Annotated[str | None, "-o"] = None):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[get] resource_type={resource_type}")
            if output:
                console.print(f"[get] output={output}")

        app(
            [
                "--namespace",
                "kube-system",
                "--context",
                "production",
                "get",
                "pods",
                "-o",
                "yaml",
            ]
        )

        output = console.get_output()
        assert "[kubectl] namespace=kube-system" in output
        assert "[kubectl] context=production" in output
        assert "[get] output=yaml" in output


class TestKubectlValidationFailures:
    """Test validation failures for kubectl command parameters."""

    def test_scale_with_invalid_replica_count_negative(self, console: MockConsole):
        """Test replica count validation rejects negative values."""
        app = App("kubectl", console=console)

        @app.command()
        def scale(
            resource_type: NonEmptyResourceName,
            resource_name: NonEmptyResourceName,
            replicas: Annotated[ReplicaCount, Opt()],
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[scale] resource_type={resource_type}")
            console.print(f"[scale] resource_name={resource_name}")
            console.print(f"[scale] replicas={replicas}")

        with pytest.raises(ValidationError) as exc_info:
            app(["scale", "deployment", "my-app", "--replicas", "-1"])

        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_scale_with_invalid_replica_count_exceeds_max(self, console: MockConsole):
        """Test replica count validation rejects values exceeding 10000."""
        app = App("kubectl", console=console)

        @app.command()
        def scale(
            resource_type: NonEmptyResourceName,
            resource_name: NonEmptyResourceName,
            replicas: Annotated[ReplicaCount, Opt()],
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[scale] resource_type={resource_type}")
            console.print(f"[scale] resource_name={resource_name}")
            console.print(f"[scale] replicas={replicas}")

        with pytest.raises(ValidationError) as exc_info:
            app(["scale", "deployment", "my-app", "--replicas", "10001"])

        assert "10000" in str(exc_info.value)

    def test_wait_with_invalid_timeout_zero(self, console: MockConsole):
        """Test timeout validation rejects zero."""
        app = App("kubectl", console=console)

        @app.command()
        def wait(
            resource_type: NonEmptyResourceName,
            resource_name: NonEmptyResourceName,
            for_condition: Annotated[str, "--for"],
            timeout: Annotated[TimeoutSeconds | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[wait] resource_type={resource_type}")
            console.print(f"[wait] resource_name={resource_name}")
            console.print(f"[wait] for_condition={for_condition}")
            if timeout:
                console.print(f"[wait] timeout={timeout}")

        with pytest.raises(ValidationError) as exc_info:
            app([
                "wait",
                "pod",
                "my-pod",
                "--for",
                "condition=Ready",
                "--timeout",
                "0",
            ])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_wait_with_invalid_timeout_negative(self, console: MockConsole):
        """Test timeout validation rejects negative values."""
        app = App("kubectl", console=console)

        @app.command()
        def wait(
            resource_type: NonEmptyResourceName,
            resource_name: NonEmptyResourceName,
            for_condition: Annotated[str, "--for"],
            timeout: Annotated[TimeoutSeconds | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[wait] resource_type={resource_type}")
            console.print(f"[wait] resource_name={resource_name}")
            console.print(f"[wait] for_condition={for_condition}")
            if timeout:
                console.print(f"[wait] timeout={timeout}")

        with pytest.raises(ValidationError) as exc_info:
            app([
                "wait",
                "pod",
                "my-pod",
                "--for",
                "condition=Ready",
                "--timeout",
                "-5",
            ])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_logs_with_invalid_tail_zero(self, console: MockConsole):
        """Test tail lines validation rejects zero."""
        app = App("kubectl", console=console)

        @app.command()
        def logs(
            pod_name: NonEmptyResourceName,
            tail: Annotated[TailLines | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[logs] pod_name={pod_name}")
            if tail:
                console.print(f"[logs] tail={tail}")

        with pytest.raises(ValidationError) as exc_info:
            app(["logs", "my-pod", "--tail", "0"])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_logs_with_invalid_tail_negative(self, console: MockConsole):
        """Test tail lines validation rejects negative values."""
        app = App("kubectl", console=console)

        @app.command()
        def logs(
            pod_name: NonEmptyResourceName,
            tail: Annotated[TailLines | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[logs] pod_name={pod_name}")
            if tail:
                console.print(f"[logs] tail={tail}")

        with pytest.raises(ValidationError) as exc_info:
            app(["logs", "my-pod", "--tail", "-10"])

        assert "must be greater than 0" in str(exc_info.value).lower()

    def test_describe_with_empty_resource_name(self, console: MockConsole):
        """Test resource name validation rejects empty string."""
        app = App("kubectl", console=console)

        @app.command()
        def describe(
            resource_type: NonEmptyResourceName,
            resource_name: NonEmptyResourceName,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[describe] resource_type={resource_type}")
            console.print(f"[describe] resource_name={resource_name}")

        with pytest.raises(ValidationError) as exc_info:
            app(["describe", "pod", ""])

        assert "at least 1" in str(exc_info.value).lower()

    def test_scale_with_empty_resource_name(self, console: MockConsole):
        """Test resource name validation rejects empty string in scale command."""
        app = App("kubectl", console=console)

        @app.command()
        def scale(
            resource_type: NonEmptyResourceName,
            resource_name: NonEmptyResourceName,
            replicas: Annotated[ReplicaCount, Opt()],
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[scale] resource_type={resource_type}")
            console.print(f"[scale] resource_name={resource_name}")
            console.print(f"[scale] replicas={replicas}")

        with pytest.raises(ValidationError) as exc_info:
            app(["scale", "deployment", "", "--replicas", "3"])

        assert "at least 1" in str(exc_info.value).lower()


class TestKubectlCommandValidators:
    """Test command-scoped validators for kubectl commands."""

    def test_all_namespaces_and_namespace_mutually_exclusive(self, console: MockConsole):
        """Test --all-namespaces and --namespace are mutually exclusive."""
        from aclaf.validation.command import MutuallyExclusive

        app = App("kubectl", console=console)

        @app.handler()
        def kubectl(namespace: Annotated[str | None, "-n"] = None):  # pyright: ignore[reportUnusedFunction]
            if namespace:
                console.print(f"[kubectl] namespace={namespace}")

        @app.command()
        def get(
            resource_type: str,
            all_namespaces: Annotated[bool, "-A"] = False,
            namespace: Annotated[str | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[get] resource_type={resource_type}")
            if all_namespaces:
                console.print("[get] all_namespaces=True")
            if namespace:
                console.print(f"[get] namespace={namespace}")

        # Add validation to the command instance
        get.validate(MutuallyExclusive(parameter_names=("all_namespaces", "namespace")))

        with pytest.raises(ValidationError) as exc_info:
            app(["get", "pods", "--all-namespaces", "--namespace", "kube-system"])

        assert "mutually exclusive" in str(exc_info.value).lower()

    @pytest.mark.skip(
        reason="Command validators don't support boolean flags (False is considered 'provided')"
    )
    def test_exec_interactive_tty_requires_both(self, console: MockConsole):
        """Test exec -it requires both -i and -t together."""
        from aclaf.metadata import Flag
        from aclaf.validation.command import AtLeastOneOf

        app = App("kubectl", console=console)

        @app.command()
        def exec(
            pod_name: str,
            interactive: Annotated[bool, Flag("-i")] = False,
            tty: Annotated[bool, Flag("-t")] = False,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[exec] pod_name={pod_name}")
            if interactive:
                console.print("[exec] interactive=True")
            if tty:
                console.print("[exec] tty=True")

        # Add validation to the command instance - at least one of -i or -t must be provided
        # NOTE: This tests validator functionality, though real kubectl allows -i alone
        exec.validate(AtLeastOneOf(parameter_names=("interactive", "tty")))

        # Test that providing neither flag raises validation error
        with pytest.raises(ValidationError) as exc_info:
            app(["exec", "my-pod"])

        assert "at least one" in str(exc_info.value).lower()

    def test_scale_requires_replicas(self, console: MockConsole):
        """Test scale requires --replicas to be specified."""
        from aclaf.validation.command import AtLeastOneOf

        app = App("kubectl", console=console)

        @app.command()
        def scale(
            resource_type: str,
            resource_name: str,
            replicas: Annotated[ReplicaCount | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[scale] resource_type={resource_type}")
            console.print(f"[scale] resource_name={resource_name}")
            if replicas is not None:
                console.print(f"[scale] replicas={replicas}")

        # Add validation to the command instance
        scale.validate(AtLeastOneOf(parameter_names=("replicas",)))

        with pytest.raises(ValidationError) as exc_info:
            app(["scale", "deployment", "my-app"])

        assert "at least one" in str(exc_info.value).lower()

    def test_resource_name_pattern_validation(self, console: MockConsole):
        """Test resource name DNS-1123 pattern validation."""
        from aclaf.validation.parameter import Pattern

        app = App("kubectl", console=console)

        DNS1123Name = Annotated[str, Pattern(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")]

        @app.command()
        def create(
            resource_type: str,
            resource_name: DNS1123Name,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[create] resource_type={resource_type}")
            console.print(f"[create] resource_name={resource_name}")

        with pytest.raises(ValidationError) as exc_info:
            app(["create", "deployment", "Invalid-Name!"])

        assert "pattern" in str(exc_info.value).lower()


class TestComplexKubectlScenarios:
    def test_complete_kubectl_cli(self, console: MockConsole):
        # Inline CLI construction - comprehensive multi-command test
        app = App("kubectl", console=console)

        @app.handler()
        def kubectl(  # pyright: ignore[reportUnusedFunction]
            namespace: Annotated[str | None, "-n"] = None,
            context: Annotated[str | None, Opt()] = None,
            kubeconfig: Annotated[str | None, Opt()] = None,
        ):
            if namespace:
                console.print(f"[kubectl] namespace={namespace}")
            if context:
                console.print(f"[kubectl] context={context}")
            if kubeconfig:
                console.print(f"[kubectl] kubeconfig={kubeconfig}")

        @app.command()
        def get(  # pyright: ignore[reportUnusedFunction]
            resource_type: str,
            resource_names: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            output: Annotated[str | None, "-o"] = None,
            watch: Annotated[bool, "-w"] = False,
            all_namespaces: Annotated[bool, "-A"] = False,
        ):
            console.print(f"[get] resource_type={resource_type}")
            if resource_names:
                console.print(f"[get] resource_names={resource_names!r}")
            if output:
                console.print(f"[get] output={output}")
            if watch:
                console.print("[get] watch=True")
            if all_namespaces:
                console.print("[get] all_namespaces=True")

        @app.command()
        def describe(resource_type: str, resource_name: str):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[describe] resource_type={resource_type}")
            console.print(f"[describe] resource_name={resource_name}")

        @app.command()
        def delete(  # pyright: ignore[reportUnusedFunction]
            resource_type: str, resource_names: Annotated[tuple[str, ...], AtLeastOne()]
        ):
            console.print(f"[delete] resource_type={resource_type}")
            console.print(f"[delete] resource_names={resource_names!r}")

        @app.command()
        def apply(filename: Annotated[tuple[str, ...], "-f", Collect()]):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[apply] filename={filename!r}")

        @app.command()
        def logs(pod_name: str, follow: Annotated[bool, "-f"] = False):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[logs] pod_name={pod_name}")
            if follow:
                console.print("[logs] follow=True")

        @app.command()
        def exec(  # pyright: ignore[reportUnusedFunction]
            pod_name: str,
            command: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            interactive: Annotated[bool, "-i"] = False,
            tty: Annotated[bool, "-t"] = False,
            container: Annotated[str | None, "-c"] = None,
        ):
            console.print(f"[exec] pod_name={pod_name}")
            if interactive:
                console.print("[exec] interactive=True")
            if tty:
                console.print("[exec] tty=True")
            if container:
                console.print(f"[exec] container={container}")
            if command:
                console.print(f"[exec] command={command!r}")

        # Test get with global namespace flag
        app(["-n", "kube-system", "get", "pods"])
        output1 = console.get_output()
        assert "[kubectl] namespace=kube-system" in output1
        assert "[get] resource_type=pods" in output1

        # Clear console between invocations to test commands independently
        console.clear()
        app(["get", "pod", "my-pod", "-o", "yaml"])
        output2 = console.get_output()
        assert "[get] output=yaml" in output2
        assert "[get] resource_names=('my-pod',)" in output2

        console.clear()
        app(["describe", "pod", "my-pod"])
        output3 = console.get_output()
        assert "[describe] resource_type=pod" in output3
        assert "[describe] resource_name=my-pod" in output3

        console.clear()
        app(["delete", "pod", "my-pod"])
        output4 = console.get_output()
        assert "[delete] resource_type=pod" in output4
        assert "[delete] resource_names=('my-pod',)" in output4

        console.clear()
        app(["apply", "-f", "manifest.yaml"])
        output5 = console.get_output()
        assert "[apply] filename=('manifest.yaml',)" in output5

        console.clear()
        app(["logs", "my-pod", "-f"])
        output6 = console.get_output()
        assert "[logs] pod_name=my-pod" in output6
        assert "[logs] follow=True" in output6

        console.clear()
        app(["exec", "-it", "my-pod", "/bin/bash"])
        output7 = console.get_output()
        assert "[exec] pod_name=my-pod" in output7
        assert "[exec] interactive=True" in output7
        assert "[exec] tty=True" in output7
        assert "[exec] command=('/bin/bash',)" in output7

    def test_get_all_namespaces_with_output(self, console: MockConsole):
        # Inline CLI construction - testing combination of multiple flags on get command
        app = App("kubectl", console=console)

        @app.command()
        def get(  # pyright: ignore[reportUnusedFunction]
            resource_type: str,
            all_namespaces: Annotated[bool, "-A"] = False,
            output: Annotated[str | None, "-o"] = None,
        ):
            console.print(f"[get] resource_type={resource_type}")
            if all_namespaces:
                console.print("[get] all_namespaces=True")
            if output:
                console.print(f"[get] output={output}")

        app(["get", "pods", "--all-namespaces", "-o", "wide"])

        output = console.get_output()
        assert "[get] all_namespaces=True" in output
        assert "[get] output=wide" in output

    def test_exec_complex_command(self, console: MockConsole):
        # Inline CLI construction - exec with complex command arguments
        # Options must come before variadic positionals to avoid ambiguity
        app = App("kubectl", console=console)

        @app.command()
        def exec(  # pyright: ignore[reportUnusedFunction]
            pod_name: str,
            command: Annotated[tuple[str, ...], ZeroOrMore()] = (),
            interactive: Annotated[bool, "-i"] = False,
            tty: Annotated[bool, "-t"] = False,
            container: Annotated[str | None, "-c"] = None,
        ):
            console.print(f"[exec] pod_name={pod_name}")
            if interactive:
                console.print("[exec] interactive=True")
            if tty:
                console.print("[exec] tty=True")
            if container:
                console.print(f"[exec] container={container}")
            if command:
                console.print(f"[exec] command={command!r}")

        app(
            [
                "exec",
                "-it",
                "-c",
                "sidecar",
                "my-pod",
                "sh",
                "echo",
                "hello",
            ]
        )

        output = console.get_output()
        assert "[exec] interactive=True" in output
        assert "[exec] tty=True" in output
        assert "[exec] container=sidecar" in output
        assert "[exec] pod_name=my-pod" in output
        assert "[exec] command=('sh', 'echo', 'hello')" in output

    def test_global_and_local_flags_together(self, console: MockConsole):
        # Inline CLI construction - global and local flag interaction
        app = App("kubectl", console=console)

        @app.handler()
        def kubectl(namespace: Annotated[str | None, "-n"] = None):  # pyright: ignore[reportUnusedFunction]
            if namespace:
                console.print(f"[kubectl] namespace={namespace}")

        @app.command()
        def get(  # pyright: ignore[reportUnusedFunction]
            resource_type: str,
            output: Annotated[str | None, "-o"] = None,
            watch: Annotated[bool, "-w"] = False,
        ):
            console.print(f"[get] resource_type={resource_type}")
            if output:
                console.print(f"[get] output={output}")
            if watch:
                console.print("[get] watch=True")

        app(["-n", "production", "get", "pods", "-o", "json", "--watch"])

        output = console.get_output()
        assert "[kubectl] namespace=production" in output
        assert "[get] output=json" in output
        assert "[get] watch=True" in output
        assert "[get] resource_type=pods" in output


class TestKubectlScaleCommand:
    def test_scale_with_replicas_valid(
        self, console: MockConsole):
        """Test scaling with valid replica count."""
        app = App("kubectl", console=console)

        @app.command()
        def scale(
            resource_type: NonEmptyResourceName,
            resource_name: NonEmptyResourceName,
            replicas: Annotated[ReplicaCount, Opt()],
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[scale] resource_type={resource_type}")
            console.print(f"[scale] resource_name={resource_name}")
            console.print(f"[scale] replicas={replicas}")

        app(["scale", "deployment", "my-app", "--replicas", "3"])

        output = console.get_output()
        assert "[scale] resource_type=deployment" in output
        assert "[scale] resource_name=my-app" in output
        assert "[scale] replicas=3" in output

class TestKubectlWaitCommand:
    def test_wait_with_timeout_valid(
        self, console: MockConsole):
        """Test wait command with valid timeout."""
        app = App("kubectl", console=console)

        @app.command()
        def wait(
            resource_type: NonEmptyResourceName,
            resource_name: NonEmptyResourceName,
            for_condition: Annotated[str, "--for"],
            timeout: Annotated[TimeoutSeconds | None, Opt()] = None,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print(f"[wait] resource_type={resource_type}")
            console.print(f"[wait] resource_name={resource_name}")
            console.print(f"[wait] for_condition={for_condition}")
            if timeout:
                console.print(f"[wait] timeout={timeout}")

        app([
            "wait",
            "pod",
            "my-pod",
            "--for",
            "condition=Ready",
            "--timeout",
            "300",
        ])

        output = console.get_output()
        assert "[wait] resource_type=pod" in output
        assert "[wait] resource_name=my-pod" in output
        assert "[wait] for_condition=condition=Ready" in output
        assert "[wait] timeout=300" in output

class TestKubectlTopCommand:
    def test_top_pods_with_validated_names(
        self, console: MockConsole):
        """Test top command with validated resource names."""
        app = App("kubectl", console=console)

        @app.command()
        def top():
            console.print("[top] invoked")

        @top.command()
        def pods(
            pod_names: Annotated[tuple[NonEmptyResourceName, ...], ZeroOrMore()] = (),
            containers: Annotated[bool, Opt()] = False,
        ):  # pyright: ignore[reportUnusedFunction]
            console.print("[top pods] invoked")
            if pod_names:
                console.print(f"[top pods] pod_names={pod_names!r}")
            if containers:
                console.print("[top pods] containers=True")

        app(["top", "pods", "pod1", "pod2", "--containers"])

        output = console.get_output()
        assert "[top] invoked" in output
        assert "[top pods] invoked" in output
        assert "[top pods] pod_names=('pod1', 'pod2')" in output
        assert "[top pods] containers=True" in output
