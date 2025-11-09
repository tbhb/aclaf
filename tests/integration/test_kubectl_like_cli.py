"""Integration tests for kubectl-like CLI patterns.

This module tests realistic kubectl-style command structures with resource
management, global flags, output formatting, namespace handling, and exec
patterns with trailing args.
"""

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import (
    EXACTLY_ONE_ARITY,
    ONE_OR_MORE_ARITY,
    ZERO_ARITY,
    ZERO_OR_MORE_ARITY,
    AccumulationMode,
)


class TestKubectlGetCommand:
    """Test kubectl get command patterns."""

    def test_get_pods(self):
        """Test kubectl get with resource type only.

        Verifies the basic kubectl get pattern where a resource type is provided
        without specific resource names. Tests required positional for resource type
        and optional positional for names with no values.

        Tests:
        - Required positional (resource_type)
        - Optional positional with no values (resource_names)
        - List-all-resources pattern

        CLI: kubectl get pods
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="get",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_names", arity=ZERO_OR_MORE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["get", "pods"])
        assert result.subcommand is not None
        assert result.subcommand.command == "get"
        assert result.subcommand.positionals["resource_type"].value == "pods"
        assert result.subcommand.positionals["resource_names"].value == ()

    def test_get_specific_pod(self):
        """Test kubectl get with resource type and specific name.

        Verifies the pattern where both resource type and a specific resource name
        are provided to retrieve details for a single resource. Tests two positionals
        with one required and one optional receiving a value.

        Tests:
        - Required positional (resource_type)
        - Optional positional with one value (resource_names)
        - Get-specific-resource pattern

        CLI: kubectl get pod my-pod
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="get",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_names", arity=ZERO_OR_MORE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["get", "pod", "my-pod"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["resource_type"].value == "pod"
        assert result.subcommand.positionals["resource_names"].value == ("my-pod",)

    def test_get_multiple_pods(self):
        """Test kubectl get with resource type and multiple names.

        Verifies the pattern where multiple specific resource names are provided
        to retrieve details for several resources. Tests zero-or-more arity positional
        receiving multiple values.

        Tests:
        - Required positional (resource_type)
        - Optional positional with multiple values
        - Multi-resource get pattern

        CLI: kubectl get pods pod1 pod2 pod3
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="get",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_names", arity=ZERO_OR_MORE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["get", "pods", "pod1", "pod2", "pod3"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["resource_type"].value == "pods"
        assert result.subcommand.positionals["resource_names"].value == (
            "pod1",
            "pod2",
            "pod3",
        )

    def test_get_with_output_format(self):
        """Test kubectl get with output format option.

        Verifies the pattern where an output format flag controls the display format
        (yaml, json, wide, etc.). Common kubectl pattern for customizing output.
        Tests value-taking option with subcommand positional.

        Tests:
        - Short option with value (-o)
        - Output format specification
        - Option-positional interaction

        CLI: kubectl get pods -o yaml
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="get",
                    options=[
                        OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY)
                    ],
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["get", "pods", "-o", "yaml"])
        assert result.subcommand is not None
        assert result.subcommand.options["output"].value == "yaml"
        assert result.subcommand.positionals["resource_type"].value == "pods"

    def test_get_with_watch(self):
        """Test kubectl get with watch mode flag.

        Verifies the pattern where a boolean flag enables continuous watching of
        resource changes. Common kubectl pattern for monitoring resources. Tests
        long zero-arity option with positional.

        Tests:
        - Long zero-arity option (--watch)
        - Short alias support (-w)
        - Watch mode pattern

        CLI: kubectl get pods --watch
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="get",
                    options=[
                        OptionSpec("watch", short=["w"], arity=ZERO_ARITY),
                    ],
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["get", "pods", "--watch"])
        assert result.subcommand is not None
        assert result.subcommand.options["watch"].value is True

    def test_get_with_all_namespaces(self):
        """Test kubectl get with all-namespaces scope flag.

        Verifies the pattern where a flag expands the query scope to all namespaces
        instead of the current one. Tests long option with uppercase short alias.
        Common kubectl pattern for cluster-wide resource viewing.

        Tests:
        - Long zero-arity option (--all-namespaces)
        - Uppercase short alias (-A)
        - Namespace scope control

        CLI: kubectl get pods --all-namespaces
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="get",
                    options=[
                        OptionSpec("all-namespaces", short=["A"], arity=ZERO_ARITY),
                    ],
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["get", "pods", "--all-namespaces"])
        assert result.subcommand is not None
        assert result.subcommand.options["all-namespaces"].value is True

        # Test short form
        result = parser.parse(["get", "pods", "-A"])
        assert result.subcommand is not None
        assert result.subcommand.options["all-namespaces"].value is True


class TestKubectlDescribeCommand:
    """Test kubectl describe command patterns."""

    def test_describe_pod(self):
        """Test kubectl describe with resource type and name.

        Verifies the describe pattern requiring both resource type and specific name.
        Tests two required positionals for detailed resource information retrieval.

        Tests:
        - Two required positionals
        - Exact arity matching (1, 1)
        - Describe command pattern

        CLI: kubectl describe pod my-pod
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="describe",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_name", arity=EXACTLY_ONE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["describe", "pod", "my-pod"])
        assert result.subcommand is not None
        assert result.subcommand.command == "describe"
        assert result.subcommand.positionals["resource_type"].value == "pod"
        assert result.subcommand.positionals["resource_name"].value == "my-pod"

    def test_describe_deployment(self):
        """Test kubectl describe with deployment resource type.

        Verifies the describe pattern works for different resource types (deployment
        instead of pod). Tests parser flexibility with same command structure but
        different resource types.

        Tests:
        - Two required positionals
        - Different resource type
        - Same pattern, different values

        CLI: kubectl describe deployment my-app
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="describe",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_name", arity=EXACTLY_ONE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["describe", "deployment", "my-app"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["resource_type"].value == "deployment"
        assert result.subcommand.positionals["resource_name"].value == "my-app"


class TestKubectlDeleteCommand:
    """Test kubectl delete command patterns."""

    def test_delete_pod(self):
        """Test kubectl delete with resource type and single name.

        Verifies the delete pattern with one resource name. Tests one-or-more arity
        positional receiving exactly one value, ensuring at least one resource is
        specified for deletion.

        Tests:
        - Required positional (resource_type)
        - One-or-more arity positional with one value
        - Single resource deletion

        CLI: kubectl delete pod my-pod
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="delete",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_names", arity=ONE_OR_MORE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["delete", "pod", "my-pod"])
        assert result.subcommand is not None
        assert result.subcommand.command == "delete"
        assert result.subcommand.positionals["resource_type"].value == "pod"
        assert result.subcommand.positionals["resource_names"].value == ("my-pod",)

    def test_delete_multiple_pods(self):
        """Test kubectl delete with multiple resource names.

        Verifies the delete pattern with multiple resource names for batch deletion.
        Tests one-or-more arity positional receiving multiple values to delete
        several resources at once.

        Tests:
        - One-or-more arity with multiple values
        - Batch deletion pattern
        - Multiple required positional values

        CLI: kubectl delete pods pod1 pod2
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="delete",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_names", arity=ONE_OR_MORE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["delete", "pods", "pod1", "pod2"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["resource_names"].value == ("pod1", "pod2")

    def test_delete_deployment(self):
        """Test kubectl delete with deployment resource type.

        Verifies delete works for different resource types (deployment). Tests
        pattern consistency across different resource types with same command structure.

        Tests:
        - One-or-more arity positional
        - Different resource type
        - Delete pattern flexibility

        CLI: kubectl delete deployment my-app
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="delete",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_names", arity=ONE_OR_MORE_ARITY),
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["delete", "deployment", "my-app"])
        assert result.subcommand is not None
        assert result.subcommand.positionals["resource_type"].value == "deployment"
        assert result.subcommand.positionals["resource_names"].value == ("my-app",)


class TestKubectlApplyCommand:
    """Test kubectl apply command patterns."""

    def test_apply_with_file(self):
        """Test kubectl apply with filename option.

        Verifies the apply pattern where configuration is loaded from a file via
        the -f flag. Uses COLLECT mode to support multiple files. Tests value-taking
        option with accumulation.

        Tests:
        - Short option with value (-f)
        - COLLECT accumulation mode
        - File-based configuration pattern

        CLI: kubectl apply -f manifest.yaml
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="apply",
                    options=[
                        OptionSpec(
                            "filename",
                            short=["f"],
                            arity=EXACTLY_ONE_ARITY,
                            accumulation_mode=AccumulationMode.COLLECT,
                        )
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["apply", "-f", "manifest.yaml"])
        assert result.subcommand is not None
        assert result.subcommand.command == "apply"
        assert result.subcommand.options["filename"].value == ("manifest.yaml",)

    def test_apply_multiple_files(self):
        """Test kubectl apply with multiple filename options.

        Verifies the pattern of repeated -f flags to apply multiple configuration
        files. Uses COLLECT accumulation to gather all file paths. Common for
        applying related configurations together.

        Tests:
        - Repeated value-taking option (-f)
        - COLLECT accumulation mode
        - Multiple file application
        - Value collection tuple

        CLI: kubectl apply -f file1.yaml -f file2.yaml
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="apply",
                    options=[
                        OptionSpec(
                            "filename",
                            short=["f"],
                            arity=EXACTLY_ONE_ARITY,
                            accumulation_mode=AccumulationMode.COLLECT,
                        )
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["apply", "-f", "file1.yaml", "-f", "file2.yaml"])
        assert result.subcommand is not None
        assert result.subcommand.options["filename"].value == (
            "file1.yaml",
            "file2.yaml",
        )


class TestKubectlLogsCommand:
    """Test kubectl logs command patterns."""

    def test_logs_basic(self):
        """Test kubectl logs with pod name only.

        Verifies the basic logs pattern with just a pod name to retrieve logs.
        Tests required positional for pod name in logs subcommand.

        Tests:
        - Single required positional
        - Exact arity (one)
        - Basic logs retrieval

        CLI: kubectl logs my-pod
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="logs",
                    positionals=[PositionalSpec("pod_name", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["logs", "my-pod"])
        assert result.subcommand is not None
        assert result.subcommand.command == "logs"
        assert result.subcommand.positionals["pod_name"].value == "my-pod"

    def test_logs_with_follow(self):
        """Test kubectl logs with follow mode for streaming.

        Verifies the pattern where --follow flag enables continuous log streaming.
        Common kubectl pattern for watching logs in real-time. Tests zero-arity
        option with short alias support.

        Tests:
        - Long zero-arity option (--follow)
        - Short alias (-f)
        - Streaming mode pattern
        - Option with required positional

        CLI: kubectl logs my-pod --follow
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="logs",
                    options=[OptionSpec("follow", short=["f"], arity=ZERO_ARITY)],
                    positionals=[PositionalSpec("pod_name", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["logs", "my-pod", "--follow"])
        assert result.subcommand is not None
        assert result.subcommand.options["follow"].value is True
        assert result.subcommand.positionals["pod_name"].value == "my-pod"

        # Test short form
        result = parser.parse(["logs", "my-pod", "-f"])
        assert result.subcommand is not None
        assert result.subcommand.options["follow"].value is True


class TestKubectlExecCommand:
    """Test kubectl exec command patterns with trailing args."""

    def test_exec_basic(self):
        """Test kubectl exec with trailing args separator.

        Verifies the exec pattern with -- separator to pass commands to the container.
        Tests trailing args feature where arguments after -- are passed through
        without parsing. Common for executing commands in pods.

        Tests:
        - Required positional (pod_name)
        - Trailing args separator (--)
        - Extra args passthrough
        - Command execution pattern

        CLI: kubectl exec my-pod -- ls -la
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="exec",
                    positionals=[PositionalSpec("pod_name", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["exec", "my-pod", "--", "ls", "-la"])
        assert result.subcommand is not None
        assert result.subcommand.command == "exec"
        assert result.subcommand.positionals["pod_name"].value == "my-pod"
        assert result.subcommand.extra_args == ("ls", "-la")

    def test_exec_interactive(self):
        """Test kubectl exec with interactive flags and trailing command.

        Verifies the exec pattern with clustered -it flags for interactive sessions
        combined with trailing args for the container command. Tests option clustering
        with trailing args separator.

        Tests:
        - Clustered zero-arity options (-it)
        - Required positional (pod_name)
        - Trailing args separator (--)
        - Interactive exec pattern

        CLI: kubectl exec my-pod -it -- /bin/bash
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="exec",
                    options=[
                        OptionSpec("interactive", short=["i"], arity=ZERO_ARITY),
                        OptionSpec("tty", short=["t"], arity=ZERO_ARITY),
                    ],
                    positionals=[PositionalSpec("pod_name", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["exec", "my-pod", "-it", "--", "/bin/bash"])
        assert result.subcommand is not None
        assert result.subcommand.options["interactive"].value is True
        assert result.subcommand.options["tty"].value is True
        assert result.subcommand.positionals["pod_name"].value == "my-pod"
        assert result.subcommand.extra_args == ("/bin/bash",)

    def test_exec_with_container_flag(self):
        """Test kubectl exec with container selection option.

        Verifies the pattern where -c flag specifies which container in a multi-
        container pod to execute commands in. Tests value-taking option with
        positional and trailing args.

        Tests:
        - Short option with value (-c)
        - Required positional (pod_name)
        - Trailing args separator (--)
        - Container selection pattern

        CLI: kubectl exec my-pod -c container-name -- env
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="exec",
                    options=[
                        OptionSpec("container", short=["c"], arity=EXACTLY_ONE_ARITY),
                    ],
                    positionals=[PositionalSpec("pod_name", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["exec", "my-pod", "-c", "container-name", "--", "env"])
        assert result.subcommand is not None
        assert result.subcommand.options["container"].value == "container-name"
        assert result.subcommand.positionals["pod_name"].value == "my-pod"
        assert result.subcommand.extra_args == ("env",)


class TestKubectlGlobalFlags:
    """Test kubectl global flags that work across all commands."""

    def test_namespace_flag(self):
        """Test kubectl global namespace flag before subcommand.

        Verifies the pattern where global --namespace flag appears before the
        subcommand to set the operation context. Tests global option scope and
        precedence over default namespace. Common kubectl pattern for targeting.

        Tests:
        - Global option before subcommand
        - Long option with value (--namespace)
        - Short alias (-n)
        - Global-local option scoping

        CLI: kubectl get pods --namespace kube-system
        """
        spec = CommandSpec(
            name="kubectl",
            options=[
                OptionSpec("namespace", short=["n"], arity=EXACTLY_ONE_ARITY),
            ],
            subcommands=[
                CommandSpec(
                    name="get",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--namespace", "kube-system", "get", "pods"])
        assert result.options["namespace"].value == "kube-system"
        assert result.subcommand is not None
        assert result.subcommand.command == "get"
        assert result.subcommand.positionals["resource_type"].value == "pods"

        # Test short form
        result = parser.parse(["-n", "kube-system", "get", "pods"])
        assert result.options["namespace"].value == "kube-system"

    def test_context_flag(self):
        """Test kubectl global context flag for cluster selection.

        Verifies the pattern where global --context flag selects which cluster to
        operate on. Tests global option appearing before subcommand for cluster
        targeting. Essential kubectl pattern for multi-cluster management.

        Tests:
        - Global option before subcommand
        - Long option with value (--context)
        - Cluster selection pattern
        - Global option scope

        CLI: kubectl --context production get pods
        """
        spec = CommandSpec(
            name="kubectl",
            options=[
                OptionSpec("context", arity=EXACTLY_ONE_ARITY),
            ],
            subcommands=[
                CommandSpec(
                    name="get",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--context", "production", "get", "pods"])
        assert result.options["context"].value == "production"
        assert result.subcommand is not None
        assert result.subcommand.command == "get"

    def test_kubeconfig_flag(self):
        """Test kubectl global kubeconfig path flag.

        Verifies the pattern where global --kubeconfig flag specifies a custom
        configuration file path. Tests global option for overriding default config
        location. Common for managing multiple kubectl configurations.

        Tests:
        - Global option before subcommand
        - Long option with path value
        - Config file specification
        - Path as option value

        CLI: kubectl --kubeconfig ~/.kube/custom-config get pods
        """
        spec = CommandSpec(
            name="kubectl",
            options=[
                OptionSpec("kubeconfig", arity=EXACTLY_ONE_ARITY),
            ],
            subcommands=[
                CommandSpec(
                    name="get",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["--kubeconfig", "~/.kube/custom-config", "get", "pods"])
        assert result.options["kubeconfig"].value == "~/.kube/custom-config"

    def test_multiple_global_flags(self):
        """Test kubectl with multiple global flags and subcommand options.

        Verifies the pattern where multiple global flags (namespace, context) appear
        before the subcommand, followed by subcommand-specific options (-o). Tests
        complex option scoping and precedence with both global and local options.

        Tests:
        - Multiple global options before subcommand
        - Global-local option separation
        - Option scope management
        - Complex option interaction

        CLI: kubectl --namespace kube-system --context production get pods -o yaml
        """
        spec = CommandSpec(
            name="kubectl",
            options=[
                OptionSpec("namespace", short=["n"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("context", arity=EXACTLY_ONE_ARITY),
            ],
            subcommands=[
                CommandSpec(
                    name="get",
                    options=[
                        OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY)
                    ],
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
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
        assert result.options["namespace"].value == "kube-system"
        assert result.options["context"].value == "production"
        assert result.subcommand is not None
        assert result.subcommand.options["output"].value == "yaml"


class TestComplexKubectlScenarios:
    """Test complex multi-feature kubectl scenarios."""

    def test_complete_kubectl_cli(self):
        """Test comprehensive kubectl CLI with full subcommand suite.

        Verifies a realistic complete kubectl CLI specification with global options
        and all major subcommands (get, describe, delete, apply, logs, exec). Tests
        parser stability across diverse command patterns and comprehensive coverage
        of kubectl features.

        Tests:
        - Multiple complex subcommands
        - Global vs subcommand options
        - Trailing args in exec
        - Parser reuse across varied commands
        - Complete CLI integration

        CLI: Multiple commands tested (get, describe, delete, apply, logs, exec)
        """
        spec = CommandSpec(
            name="kubectl",
            options=[
                OptionSpec("namespace", short=["n"], arity=EXACTLY_ONE_ARITY),
                OptionSpec("context", arity=EXACTLY_ONE_ARITY),
                OptionSpec("kubeconfig", arity=EXACTLY_ONE_ARITY),
            ],
            subcommands=[
                CommandSpec(
                    name="get",
                    options=[
                        OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("watch", short=["w"], arity=ZERO_ARITY),
                        OptionSpec("all-namespaces", short=["A"], arity=ZERO_ARITY),
                    ],
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_names", arity=ZERO_OR_MORE_ARITY),
                    ],
                ),
                CommandSpec(
                    name="describe",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_name", arity=EXACTLY_ONE_ARITY),
                    ],
                ),
                CommandSpec(
                    name="delete",
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY),
                        PositionalSpec("resource_names", arity=ONE_OR_MORE_ARITY),
                    ],
                ),
                CommandSpec(
                    name="apply",
                    options=[
                        OptionSpec(
                            "filename",
                            short=["f"],
                            arity=EXACTLY_ONE_ARITY,
                            accumulation_mode=AccumulationMode.COLLECT,
                        )
                    ],
                ),
                CommandSpec(
                    name="logs",
                    options=[OptionSpec("follow", short=["f"], arity=ZERO_ARITY)],
                    positionals=[PositionalSpec("pod_name", arity=EXACTLY_ONE_ARITY)],
                ),
                CommandSpec(
                    name="exec",
                    options=[
                        OptionSpec("interactive", short=["i"], arity=ZERO_ARITY),
                        OptionSpec("tty", short=["t"], arity=ZERO_ARITY),
                        OptionSpec("container", short=["c"], arity=EXACTLY_ONE_ARITY),
                    ],
                    positionals=[PositionalSpec("pod_name", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        # Test get with global namespace flag
        result1 = parser.parse(["-n", "kube-system", "get", "pods"])
        assert result1.options["namespace"].value == "kube-system"
        assert result1.subcommand is not None
        assert result1.subcommand.command == "get"
        assert result1.subcommand.positionals["resource_type"].value == "pods"

        # Test get with output format
        result2 = parser.parse(["get", "pod", "my-pod", "-o", "yaml"])
        assert result2.subcommand is not None
        assert result2.subcommand.options["output"].value == "yaml"
        assert result2.subcommand.positionals["resource_names"].value == ("my-pod",)

        # Test describe
        result3 = parser.parse(["describe", "pod", "my-pod"])
        assert result3.subcommand is not None
        assert result3.subcommand.command == "describe"
        assert result3.subcommand.positionals["resource_name"].value == "my-pod"

        # Test delete
        result4 = parser.parse(["delete", "pod", "my-pod"])
        assert result4.subcommand is not None
        assert result4.subcommand.command == "delete"

        # Test apply
        result5 = parser.parse(["apply", "-f", "manifest.yaml"])
        assert result5.subcommand is not None
        assert result5.subcommand.command == "apply"
        assert result5.subcommand.options["filename"].value == ("manifest.yaml",)

        # Test logs with follow
        result6 = parser.parse(["logs", "my-pod", "-f"])
        assert result6.subcommand is not None
        assert result6.subcommand.command == "logs"
        assert result6.subcommand.options["follow"].value is True

        # Test exec with interactive
        result7 = parser.parse(["exec", "my-pod", "-it", "--", "/bin/bash"])
        assert result7.subcommand is not None
        assert result7.subcommand.command == "exec"
        assert result7.subcommand.options["interactive"].value is True
        assert result7.subcommand.options["tty"].value is True
        assert result7.subcommand.extra_args == ("/bin/bash",)

    def test_get_all_namespaces_with_output(self):
        """Test kubectl get with combined scope and output options.

        Verifies the pattern combining namespace scope flag (--all-namespaces) with
        output format option (-o). Tests multiple subcommand options working together
        for cluster-wide formatted output.

        Tests:
        - Multiple subcommand options
        - Long and short option combination
        - Scope and format control together
        - Option interaction

        CLI: kubectl get pods --all-namespaces -o wide
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="get",
                    options=[
                        OptionSpec("all-namespaces", short=["A"], arity=ZERO_ARITY),
                        OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
                    ],
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(["get", "pods", "--all-namespaces", "-o", "wide"])
        assert result.subcommand is not None
        assert result.subcommand.options["all-namespaces"].value is True
        assert result.subcommand.options["output"].value == "wide"

    def test_exec_complex_command(self):
        """Test kubectl exec with complex option combination and shell command.

        Verifies realistic complex exec with clustered flags (-it), container selection
        (-c), and shell command with arguments in trailing args. Tests comprehensive
        option-positional-trailing-args interaction.

        Tests:
        - Clustered zero-arity options (-it)
        - Value-taking option (-c)
        - Required positional (pod_name)
        - Complex trailing args (shell command)
        - Real-world exec complexity

        CLI: kubectl exec -it my-pod -c sidecar -- sh -c 'echo $VAR'
        """
        spec = CommandSpec(
            name="kubectl",
            subcommands=[
                CommandSpec(
                    name="exec",
                    options=[
                        OptionSpec("interactive", short=["i"], arity=ZERO_ARITY),
                        OptionSpec("tty", short=["t"], arity=ZERO_ARITY),
                        OptionSpec("container", short=["c"], arity=EXACTLY_ONE_ARITY),
                    ],
                    positionals=[PositionalSpec("pod_name", arity=EXACTLY_ONE_ARITY)],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            [
                "exec",
                "-it",
                "my-pod",
                "-c",
                "sidecar",
                "--",
                "sh",
                "-c",
                "echo $VAR",
            ]
        )
        assert result.subcommand is not None
        assert result.subcommand.options["interactive"].value is True
        assert result.subcommand.options["tty"].value is True
        assert result.subcommand.options["container"].value == "sidecar"
        assert result.subcommand.positionals["pod_name"].value == "my-pod"
        assert result.subcommand.extra_args == ("sh", "-c", "echo $VAR")

    def test_global_and_local_flags_together(self):
        """Test kubectl with global and local flags in single command.

        Verifies the complex pattern where global namespace flag precedes the
        subcommand, followed by multiple subcommand-specific options (output format
        and watch mode). Tests comprehensive global-local option scoping.

        Tests:
        - Global option before subcommand (-n)
        - Multiple subcommand options (-o, --watch)
        - Global-local option separation
        - Complex option scoping
        - Real-world combined usage

        CLI: kubectl -n production get pods -o json --watch
        """
        spec = CommandSpec(
            name="kubectl",
            options=[
                OptionSpec("namespace", short=["n"], arity=EXACTLY_ONE_ARITY),
            ],
            subcommands=[
                CommandSpec(
                    name="get",
                    options=[
                        OptionSpec("output", short=["o"], arity=EXACTLY_ONE_ARITY),
                        OptionSpec("watch", short=["w"], arity=ZERO_ARITY),
                    ],
                    positionals=[
                        PositionalSpec("resource_type", arity=EXACTLY_ONE_ARITY)
                    ],
                ),
            ],
        )
        parser = Parser(spec)

        result = parser.parse(
            ["-n", "production", "get", "pods", "-o", "json", "--watch"]
        )
        assert result.options["namespace"].value == "production"
        assert result.subcommand is not None
        assert result.subcommand.options["output"].value == "json"
        assert result.subcommand.options["watch"].value is True
        assert result.subcommand.positionals["resource_type"].value == "pods"
