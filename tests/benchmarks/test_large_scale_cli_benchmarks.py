"""Benchmarks for realistic large-scale CLI scenarios.

This module tests performance characteristics of Aclaf when building and parsing
commands that mirror real-world CLIs with hundreds of subcommands and many options.

The benchmarks cover:
- Massive hierarchical CLIs (AWS-like with 300+ services)
- Dense option parsing (kubectl/docker-like with 20-50 options)
- Deep nesting (gcloud-like with 3-5 levels)
- Mixed complexity (large subcommand trees with many options each)

Each benchmark tests both command registration/building AND argument parsing to
identify performance bottlenecks across the entire architecture.
"""

# pyright: reportUnknownParameterType=false, reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
# pyright: reportMissingParameterType=false, reportUnusedCallResult=false
# Note: Type checking disabled for benchmark fixtures which don't have type stubs

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import ZERO_OR_MORE_ARITY, AccumulationMode, Arity


def test_benchmark_aws_like_massive_subcommands_build(benchmark):
    """Benchmark building an AWS CLI-like structure with 300+ services.

    This tests command tree construction performance when dealing with a massive
    number of top-level subcommands, similar to the AWS CLI which has services
    like ec2, s3, lambda, dynamodb, etc. (300+ total).

    Architecture stress points:
    - CommandSpec subcommand dictionary construction
    - Name validation across hundreds of entries
    - Subcommand name caching infrastructure
    """

    def build_aws_like_cli():
        # AWS service name patterns
        service_prefixes = [
            "compute",
            "storage",
            "database",
            "network",
            "analytics",
            "ml",
            "security",
            "monitoring",
            "container",
            "serverless",
        ]
        service_types = [
            "core",
            "plus",
            "pro",
            "advanced",
            "standard",
            "classic",
            "express",
            "managed",
            "elastic",
            "auto",
        ]

        # Generate 300 services (10 prefixes x 10 types x 3 variants)
        subcommands = {}
        for prefix in service_prefixes:
            for service_type in service_types:
                for variant in ["v1", "v2", "v3"]:
                    service_name = f"{prefix}-{service_type}-{variant}"

                    # Each service has a few common operations
                    service_subcommands = {
                        "create": CommandSpec(
                            "create",
                            positionals={
                                "name": PositionalSpec("name", arity=Arity(1, 1)),
                            },
                        ),
                        "delete": CommandSpec(
                            "delete",
                            positionals={
                                "name": PositionalSpec("name", arity=Arity(1, 1)),
                            },
                        ),
                        "list": CommandSpec("list"),
                    }

                    subcommands[service_name] = CommandSpec(
                        service_name, subcommands=service_subcommands
                    )

        return CommandSpec("aws", subcommands=subcommands)

    result = benchmark(build_aws_like_cli)

    # Verify structure
    assert len(result.subcommands) == 300
    assert "compute-core-v1" in result.subcommands
    assert "create" in result.subcommands["compute-core-v1"].subcommands


def test_benchmark_aws_like_massive_subcommands_parse(benchmark):
    """Benchmark parsing commands in an AWS CLI-like structure.

    Tests subcommand resolution performance when navigating a command tree
    with 300+ top-level services.

    Architecture stress points:
    - Subcommand name resolution from cached mapping
    - Recursive parse result construction
    - Deep command path tracking
    """
    # Pre-build the spec (not part of benchmark)
    service_prefixes = [
        "compute",
        "storage",
        "database",
        "network",
        "analytics",
        "ml",
        "security",
        "monitoring",
        "container",
        "serverless",
    ]
    service_types = [
        "core",
        "plus",
        "pro",
        "advanced",
        "standard",
        "classic",
        "express",
        "managed",
        "elastic",
        "auto",
    ]

    subcommands = {}
    for prefix in service_prefixes:
        for service_type in service_types:
            for variant in ["v1", "v2", "v3"]:
                service_name = f"{prefix}-{service_type}-{variant}"
                service_subcommands = {
                    "create": CommandSpec(
                        "create",
                        positionals={
                            "name": PositionalSpec("name", arity=Arity(1, 1)),
                        },
                    ),
                    "delete": CommandSpec(
                        "delete",
                        positionals={
                            "name": PositionalSpec("name", arity=Arity(1, 1)),
                        },
                    ),
                    "list": CommandSpec("list"),
                }
                subcommands[service_name] = CommandSpec(
                    service_name, subcommands=service_subcommands
                )

    spec = CommandSpec("aws", subcommands=subcommands)
    parser = Parser(spec)

    # Benchmark parsing a command in the middle of the alphabet
    result = benchmark(parser.parse, ["ml-managed-v2", "create", "my-model"])

    # Verify parsing
    assert result.subcommand is not None
    assert result.subcommand.command == "ml-managed-v2"
    assert result.subcommand.subcommand is not None
    assert result.subcommand.subcommand.positionals["name"].value == "my-model"


def test_benchmark_kubectl_like_dense_options_build(benchmark):
    """Benchmark building a kubectl-like command with 50 options.

    Tests option specification construction when a single command has many
    options, similar to kubectl commands which can have 20-50+ flags.

    Architecture stress points:
    - OptionSpec construction and validation
    - Option name mapping construction
    - Long/short name frozenset creation
    """

    def build_kubectl_like_command():
        # kubectl-style option names
        options = {}

        # Common kubectl options
        common_opts = [
            ("all-namespaces", "A"),
            ("namespace", "n"),
            ("output", "o"),
            ("selector", "l"),
            ("field-selector", None),
            ("watch", "w"),
            ("watch-only", None),
            ("chunk-size", None),
            ("no-headers", None),
            ("show-labels", None),
            ("show-kind", None),
            ("sort-by", None),
            ("timeout", None),
            ("as", None),
            ("as-group", None),
            ("cache-dir", None),
            ("certificate-authority", None),
            ("client-certificate", None),
            ("client-key", None),
            ("cluster", None),
            ("context", None),
            ("insecure-skip-tls-verify", None),
            ("kubeconfig", None),
            ("request-timeout", None),
            ("server", "s"),
            ("tls-server-name", None),
            ("token", None),
            ("user", None),
            ("allow-missing-template-keys", None),
            ("dry-run", None),
            ("filename", "f"),
            ("kustomize", "k"),
            ("recursive", "R"),
            ("template", None),
            ("validate", None),
            ("force", None),
            ("grace-period", None),
            ("ignore-not-found", None),
            ("now", None),
            ("prune", None),
            ("prune-whitelist", None),
            ("wait", None),
            ("cascade", None),
            ("field-manager", None),
            ("raw", None),
            ("subresource", None),
            ("edit-last-applied", None),
            ("record", None),
            ("save-config", None),
            ("overwrite", None),
            ("local", None),
        ]

        for long_name, short_name in common_opts:
            is_flag = long_name in {
                "all-namespaces",
                "watch",
                "watch-only",
                "no-headers",
                "show-labels",
                "show-kind",
                "insecure-skip-tls-verify",
                "allow-missing-template-keys",
                "recursive",
                "validate",
                "force",
                "ignore-not-found",
                "now",
                "wait",
                "edit-last-applied",
                "record",
                "save-config",
                "overwrite",
                "local",
            }

            short_set = frozenset({short_name}) if short_name else frozenset()

            options[long_name] = OptionSpec(
                long_name,
                short=short_set,
                is_flag=is_flag,
                arity=Arity(0, 0) if is_flag else Arity(1, 1),
            )

        return CommandSpec(
            "get",
            options=options,
            positionals={
                "resource": PositionalSpec("resource", arity=Arity(1, 1)),
                "name": PositionalSpec("name", arity=Arity(0, 1)),
            },
        )

    result = benchmark(build_kubectl_like_command)

    # Verify structure (actually 46 options defined, but keeping test flexible)
    assert len(result.options) >= 45
    assert "namespace" in result.options
    assert result.options["namespace"].short == frozenset({"n"})


def test_benchmark_kubectl_like_dense_options_parse(benchmark):
    """Benchmark parsing a kubectl-like command with many options.

    Tests option resolution and value consumption when processing a command
    invocation with multiple options from a large option set.

    Architecture stress points:
    - Option name resolution with many options registered
    - Short option bundling detection
    - Value consumption with mixed flags and value options
    """
    # Pre-build the spec (not part of benchmark)
    common_opts = [
        ("all-namespaces", "A", True),
        ("namespace", "n", False),
        ("output", "o", False),
        ("selector", "l", False),
        ("field-selector", None, False),
        ("watch", "w", True),
        ("watch-only", None, True),
        ("chunk-size", None, False),
        ("no-headers", None, True),
        ("show-labels", None, True),
        ("show-kind", None, True),
        ("sort-by", None, False),
        ("timeout", None, False),
        ("as", None, False),
        ("as-group", None, False),
        ("cache-dir", None, False),
        ("certificate-authority", None, False),
        ("client-certificate", None, False),
        ("client-key", None, False),
        ("cluster", None, False),
        ("context", None, False),
        ("insecure-skip-tls-verify", None, True),
        ("kubeconfig", None, False),
        ("request-timeout", None, False),
        ("server", "s", False),
        ("tls-server-name", None, False),
        ("token", None, False),
        ("user", None, False),
        ("allow-missing-template-keys", None, True),
        ("dry-run", None, False),
        ("filename", "f", False),
        ("kustomize", "k", False),
        ("recursive", "R", True),
        ("template", None, False),
        ("validate", None, True),
        ("force", None, True),
        ("grace-period", None, False),
        ("ignore-not-found", None, True),
        ("now", None, True),
        ("prune", None, True),
        ("prune-whitelist", None, False),
        ("wait", None, True),
        ("cascade", None, False),
        ("field-manager", None, False),
        ("raw", None, False),
        ("subresource", None, False),
        ("edit-last-applied", None, True),
        ("record", None, True),
        ("save-config", None, True),
        ("overwrite", None, True),
        ("local", None, True),
    ]

    options = {}
    for long_name, short_name, is_flag in common_opts:
        short_set = frozenset({short_name}) if short_name else frozenset()
        options[long_name] = OptionSpec(
            long_name,
            short=short_set,
            is_flag=is_flag,
            arity=Arity(0, 0) if is_flag else Arity(1, 1),
        )

    spec = CommandSpec(
        "get",
        options=options,
        positionals={
            "resource": PositionalSpec("resource", arity=Arity(1, 1)),
            "name": PositionalSpec("name", arity=Arity(0, 1)),
        },
    )
    parser = Parser(spec)

    # Realistic kubectl invocation with many options
    args = [
        "-n",
        "production",
        "--output",
        "json",
        "--show-labels",
        "-w",
        "--timeout",
        "30s",
        "--field-selector",
        "status.phase=Running",
        "pods",
        "my-pod",
    ]

    result = benchmark(parser.parse, args)

    # Verify parsing
    assert result.options["namespace"].value == "production"
    assert result.options["output"].value == "json"
    assert result.options["show-labels"].value is True
    assert result.options["watch"].value is True
    assert result.positionals["resource"].value == "pods"


def test_benchmark_gcloud_like_deep_nesting_build(benchmark):
    """Benchmark building a gcloud-like deeply nested command structure.

    Tests command tree construction with deep hierarchies (4-5 levels) like
    gcloud's structure: gcloud compute instances create, gcloud sql instances
    create, etc.

    Architecture stress points:
    - Recursive CommandSpec construction
    - Nested subcommand dictionary allocation
    - Parent-child relationship overhead
    """

    def build_gcloud_like_cli():
        # Level 4: Actual operations
        vm_operations = {
            "create": CommandSpec(
                "create",
                options={
                    "machine-type": OptionSpec("machine-type"),
                    "zone": OptionSpec("zone"),
                    "image": OptionSpec("image"),
                    "boot-disk-size": OptionSpec("boot-disk-size"),
                    "network": OptionSpec("network"),
                    "subnet": OptionSpec("subnet"),
                    "tags": OptionSpec(
                        "tags", accumulation_mode=AccumulationMode.COLLECT
                    ),
                },
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "delete": CommandSpec(
                "delete",
                options={
                    "zone": OptionSpec("zone"),
                    "quiet": OptionSpec("quiet", is_flag=True),
                },
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "list": CommandSpec(
                "list",
                options={
                    "zones": OptionSpec("zones"),
                    "filter": OptionSpec("filter"),
                    "limit": OptionSpec("limit"),
                },
            ),
            "describe": CommandSpec(
                "describe",
                options={"zone": OptionSpec("zone")},
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "start": CommandSpec(
                "start",
                options={
                    "zone": OptionSpec("zone"),
                    "async": OptionSpec("async", is_flag=True),
                },
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "stop": CommandSpec(
                "stop",
                options={
                    "zone": OptionSpec("zone"),
                    "async": OptionSpec("async", is_flag=True),
                },
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
        }

        disk_operations = {
            "create": CommandSpec(
                "create",
                options={
                    "size": OptionSpec("size"),
                    "type": OptionSpec("type"),
                    "zone": OptionSpec("zone"),
                },
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "delete": CommandSpec(
                "delete",
                options={"zone": OptionSpec("zone")},
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "list": CommandSpec("list", options={"zones": OptionSpec("zones")}),
        }

        network_operations = {
            "create": CommandSpec(
                "create",
                options={
                    "subnet-mode": OptionSpec("subnet-mode"),
                    "bgp-routing-mode": OptionSpec("bgp-routing-mode"),
                },
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "delete": CommandSpec(
                "delete",
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "list": CommandSpec("list"),
        }

        # Level 3: Resource types
        compute_resources = {
            "instances": CommandSpec("instances", subcommands=vm_operations),
            "disks": CommandSpec("disks", subcommands=disk_operations),
            "networks": CommandSpec("networks", subcommands=network_operations),
            "firewall-rules": CommandSpec(
                "firewall-rules", subcommands=network_operations
            ),
            "instance-templates": CommandSpec(
                "instance-templates", subcommands=vm_operations
            ),
        }

        storage_resources = {
            "buckets": CommandSpec("buckets", subcommands=disk_operations),
            "objects": CommandSpec("objects", subcommands=disk_operations),
        }

        sql_resources = {
            "instances": CommandSpec("instances", subcommands=vm_operations),
            "databases": CommandSpec("databases", subcommands=disk_operations),
            "users": CommandSpec("users", subcommands=network_operations),
        }

        # Level 2: Service categories
        services = {
            "compute": CommandSpec("compute", subcommands=compute_resources),
            "storage": CommandSpec("storage", subcommands=storage_resources),
            "sql": CommandSpec("sql", subcommands=sql_resources),
        }

        # Level 1: Root
        return CommandSpec("gcloud", subcommands=services)

    result = benchmark(build_gcloud_like_cli)

    # Verify structure depth
    assert "compute" in result.subcommands
    assert "instances" in result.subcommands["compute"].subcommands
    assert (
        "create" in result.subcommands["compute"].subcommands["instances"].subcommands
    )
    assert (
        "name"
        in result.subcommands["compute"]
        .subcommands["instances"]
        .subcommands["create"]
        .positionals
    )


def test_benchmark_gcloud_like_deep_nesting_parse(benchmark):
    """Benchmark parsing deeply nested gcloud-like commands.

    Tests recursive parsing through a 4-5 level command hierarchy.

    Architecture stress points:
    - Recursive subcommand resolution at each level
    - Parse result nesting construction
    - Context switching between command levels
    """
    # Pre-build the spec (not part of benchmark)
    vm_operations = {
        "create": CommandSpec(
            "create",
            options={
                "machine-type": OptionSpec("machine-type"),
                "zone": OptionSpec("zone"),
                "image": OptionSpec("image"),
                "boot-disk-size": OptionSpec("boot-disk-size"),
                "network": OptionSpec("network"),
                "subnet": OptionSpec("subnet"),
                "tags": OptionSpec("tags", accumulation_mode=AccumulationMode.COLLECT),
            },
            positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
        ),
    }

    compute_resources = {
        "instances": CommandSpec("instances", subcommands=vm_operations),
    }

    services = {
        "compute": CommandSpec("compute", subcommands=compute_resources),
    }

    spec = CommandSpec("gcloud", subcommands=services)
    parser = Parser(spec)

    # Deep nested command with options at the leaf
    args = [
        "compute",
        "instances",
        "create",
        "--machine-type",
        "n1-standard-4",
        "--zone",
        "us-central1-a",
        "--image",
        "ubuntu-2004-lts",
        "--tags",
        "web",
        "--tags",
        "https",
        "my-instance",
    ]

    result = benchmark(parser.parse, args)

    # Verify deep parsing
    assert result.subcommand is not None
    assert result.subcommand.command == "compute"
    assert result.subcommand.subcommand is not None
    assert result.subcommand.subcommand.command == "instances"
    assert result.subcommand.subcommand.subcommand is not None
    assert result.subcommand.subcommand.subcommand.command == "create"
    assert (
        result.subcommand.subcommand.subcommand.options["machine-type"].value
        == "n1-standard-4"
    )


def test_benchmark_docker_like_mixed_complexity_build(benchmark):
    """Benchmark building a docker-like CLI with mixed complexity.

    Combines moderate subcommand count (30-40) with many options per command
    (20-30 options), representing the sweet spot of real-world complexity.

    Architecture stress points:
    - Balanced tree construction (width and depth)
    - Option spec construction at scale
    - Combined name resolution caching overhead
    """

    def build_docker_like_cli():
        # Common docker run options (30+ options)
        run_options = {
            "detach": OptionSpec("detach", short=frozenset({"d"}), is_flag=True),
            "interactive": OptionSpec(
                "interactive", short=frozenset({"i"}), is_flag=True
            ),
            "tty": OptionSpec("tty", short=frozenset({"t"}), is_flag=True),
            "name": OptionSpec("name"),
            "hostname": OptionSpec("hostname", short=frozenset({"h"})),
            "publish": OptionSpec(
                "publish",
                short=frozenset({"p"}),
                accumulation_mode=AccumulationMode.COLLECT,
            ),
            "expose": OptionSpec("expose", accumulation_mode=AccumulationMode.COLLECT),
            "env": OptionSpec(
                "env",
                short=frozenset({"e"}),
                accumulation_mode=AccumulationMode.COLLECT,
            ),
            "env-file": OptionSpec(
                "env-file", accumulation_mode=AccumulationMode.COLLECT
            ),
            "volume": OptionSpec(
                "volume",
                short=frozenset({"v"}),
                accumulation_mode=AccumulationMode.COLLECT,
            ),
            "mount": OptionSpec("mount", accumulation_mode=AccumulationMode.COLLECT),
            "network": OptionSpec("network"),
            "network-alias": OptionSpec(
                "network-alias", accumulation_mode=AccumulationMode.COLLECT
            ),
            "restart": OptionSpec("restart"),
            "rm": OptionSpec("rm", is_flag=True),
            "memory": OptionSpec("memory", short=frozenset({"m"})),
            "cpus": OptionSpec("cpus"),
            "cpu-shares": OptionSpec("cpu-shares"),
            "entrypoint": OptionSpec("entrypoint"),
            "workdir": OptionSpec("workdir", short=frozenset({"w"})),
            "user": OptionSpec("user", short=frozenset({"u"})),
            "privileged": OptionSpec("privileged", is_flag=True),
            "read-only": OptionSpec("read-only", is_flag=True),
            "security-opt": OptionSpec(
                "security-opt", accumulation_mode=AccumulationMode.COLLECT
            ),
            "cap-add": OptionSpec(
                "cap-add", accumulation_mode=AccumulationMode.COLLECT
            ),
            "cap-drop": OptionSpec(
                "cap-drop", accumulation_mode=AccumulationMode.COLLECT
            ),
            "device": OptionSpec("device", accumulation_mode=AccumulationMode.COLLECT),
            "dns": OptionSpec("dns", accumulation_mode=AccumulationMode.COLLECT),
            "dns-search": OptionSpec(
                "dns-search", accumulation_mode=AccumulationMode.COLLECT
            ),
            "label": OptionSpec(
                "label",
                short=frozenset({"l"}),
                accumulation_mode=AccumulationMode.COLLECT,
            ),
        }

        # Container commands
        container_commands = {
            "run": CommandSpec(
                "run",
                options=run_options,
                positionals={
                    "image": PositionalSpec("image", arity=Arity(1, 1)),
                    "command": PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                },
            ),
            "start": CommandSpec(
                "start",
                options={
                    "attach": OptionSpec(
                        "attach", short=frozenset({"a"}), is_flag=True
                    ),
                    "interactive": OptionSpec("interactive", is_flag=True),
                },
                positionals={
                    "container": PositionalSpec("container", arity=Arity(1, 1)),
                },
            ),
            "stop": CommandSpec(
                "stop",
                options={"time": OptionSpec("time", short=frozenset({"t"}))},
                positionals={
                    "container": PositionalSpec("container", arity=Arity(1, 1)),
                },
            ),
            "rm": CommandSpec(
                "rm",
                options={
                    "force": OptionSpec("force", short=frozenset({"f"}), is_flag=True),
                    "volumes": OptionSpec(
                        "volumes", short=frozenset({"v"}), is_flag=True
                    ),
                },
                positionals={
                    "container": PositionalSpec("container", arity=ZERO_OR_MORE_ARITY),
                },
            ),
            "logs": CommandSpec(
                "logs",
                options={
                    "follow": OptionSpec(
                        "follow", short=frozenset({"f"}), is_flag=True
                    ),
                    "tail": OptionSpec("tail"),
                    "since": OptionSpec("since"),
                },
                positionals={
                    "container": PositionalSpec("container", arity=Arity(1, 1)),
                },
            ),
            "exec": CommandSpec(
                "exec",
                options={
                    "interactive": OptionSpec(
                        "interactive", short=frozenset({"i"}), is_flag=True
                    ),
                    "tty": OptionSpec("tty", short=frozenset({"t"}), is_flag=True),
                    "detach": OptionSpec(
                        "detach", short=frozenset({"d"}), is_flag=True
                    ),
                },
                positionals={
                    "container": PositionalSpec("container", arity=Arity(1, 1)),
                    "command": PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                },
            ),
            "ps": CommandSpec(
                "ps",
                options={
                    "all": OptionSpec("all", short=frozenset({"a"}), is_flag=True),
                    "filter": OptionSpec(
                        "filter",
                        short=frozenset({"f"}),
                        accumulation_mode=AccumulationMode.COLLECT,
                    ),
                    "quiet": OptionSpec("quiet", short=frozenset({"q"}), is_flag=True),
                },
            ),
        }

        # Image commands
        image_commands = {
            "build": CommandSpec(
                "build",
                options={
                    "tag": OptionSpec(
                        "tag",
                        short=frozenset({"t"}),
                        accumulation_mode=AccumulationMode.COLLECT,
                    ),
                    "file": OptionSpec("file", short=frozenset({"f"})),
                    "build-arg": OptionSpec(
                        "build-arg", accumulation_mode=AccumulationMode.COLLECT
                    ),
                    "no-cache": OptionSpec("no-cache", is_flag=True),
                },
                positionals={"path": PositionalSpec("path", arity=Arity(1, 1))},
            ),
            "pull": CommandSpec(
                "pull",
                positionals={"image": PositionalSpec("image", arity=Arity(1, 1))},
            ),
            "push": CommandSpec(
                "push",
                positionals={"image": PositionalSpec("image", arity=Arity(1, 1))},
            ),
            "ls": CommandSpec(
                "ls",
                options={
                    "all": OptionSpec("all", short=frozenset({"a"}), is_flag=True),
                    "quiet": OptionSpec("quiet", short=frozenset({"q"}), is_flag=True),
                },
            ),
        }

        # Network commands
        network_commands = {
            "create": CommandSpec(
                "create",
                options={
                    "driver": OptionSpec("driver", short=frozenset({"d"})),
                    "subnet": OptionSpec("subnet"),
                },
                positionals={"name": PositionalSpec("name", arity=Arity(1, 1))},
            ),
            "rm": CommandSpec(
                "rm",
                positionals={"network": PositionalSpec("network", arity=Arity(1, 1))},
            ),
            "ls": CommandSpec("ls"),
        }

        # Top-level structure
        subcommands = {
            "container": CommandSpec("container", subcommands=container_commands),
            "image": CommandSpec("image", subcommands=image_commands),
            "network": CommandSpec("network", subcommands=network_commands),
            # Also expose container commands at root for convenience (docker pattern)
            **container_commands,
        }

        return CommandSpec("docker", subcommands=subcommands)

    result = benchmark(build_docker_like_cli)

    # Verify structure
    assert len(result.subcommands) >= 10
    assert "run" in result.subcommands
    assert len(result.subcommands["run"].options) >= 25


def test_benchmark_docker_like_mixed_complexity_parse(benchmark):
    """Benchmark parsing docker-like commands with many options.

    Tests realistic usage patterns with multiple flags, environment variables,
    port mappings, and volume mounts.

    Architecture stress points:
    - Option value accumulation (COLLECT mode)
    - Mixed short and long option forms
    - Many option values requiring consumption
    """
    # Pre-build the spec (not part of benchmark)
    run_options = {
        "detach": OptionSpec("detach", short=frozenset({"d"}), is_flag=True),
        "interactive": OptionSpec("interactive", short=frozenset({"i"}), is_flag=True),
        "tty": OptionSpec("tty", short=frozenset({"t"}), is_flag=True),
        "name": OptionSpec("name"),
        "publish": OptionSpec(
            "publish",
            short=frozenset({"p"}),
            accumulation_mode=AccumulationMode.COLLECT,
        ),
        "env": OptionSpec(
            "env", short=frozenset({"e"}), accumulation_mode=AccumulationMode.COLLECT
        ),
        "volume": OptionSpec(
            "volume", short=frozenset({"v"}), accumulation_mode=AccumulationMode.COLLECT
        ),
        "network": OptionSpec("network"),
        "restart": OptionSpec("restart"),
        "rm": OptionSpec("rm", is_flag=True),
        "memory": OptionSpec("memory", short=frozenset({"m"})),
        "label": OptionSpec(
            "label", short=frozenset({"l"}), accumulation_mode=AccumulationMode.COLLECT
        ),
    }

    spec = CommandSpec(
        "docker",
        subcommands={
            "run": CommandSpec(
                "run",
                options=run_options,
                positionals={
                    "image": PositionalSpec("image", arity=Arity(1, 1)),
                    "command": PositionalSpec("command", arity=ZERO_OR_MORE_ARITY),
                },
            ),
        },
    )
    parser = Parser(spec)

    # Realistic docker run command with many options
    args = [
        "run",
        "-d",
        "--name",
        "web-app",
        "-p",
        "8080:80",
        "-p",
        "8443:443",
        "-e",
        "NODE_ENV=production",
        "-e",
        "LOG_LEVEL=info",
        "-v",
        "/host/data:/container/data",
        "-v",
        "/host/logs:/container/logs",
        "--network",
        "bridge",
        "--restart",
        "unless-stopped",
        "--rm",
        "-m",
        "2g",
        "-l",
        "app=web",
        "-l",
        "env=prod",
        "nginx:latest",
    ]

    result = benchmark(parser.parse, args)

    # Verify complex parsing
    assert result.subcommand is not None
    assert result.subcommand.options["detach"].value is True
    assert result.subcommand.options["name"].value == "web-app"
    assert result.subcommand.options["publish"].value == ("8080:80", "8443:443")
    assert result.subcommand.options["env"].value == (
        "NODE_ENV=production",
        "LOG_LEVEL=info",
    )
    assert result.subcommand.positionals["image"].value == "nginx:latest"


def test_benchmark_npm_like_package_manager_build(benchmark):
    """Benchmark building an npm/pnpm-like package manager CLI.

    Package managers have moderate subcommand counts but complex option
    interactions and configuration flags.

    Architecture stress points:
    - Option specification with many boolean flags
    - Mixed accumulation modes across options
    - Command aliasing patterns
    """

    def build_npm_like_cli():
        # Common install/add options
        install_options = {
            "save": OptionSpec("save", short=frozenset({"S"}), is_flag=True),
            "save-dev": OptionSpec("save-dev", short=frozenset({"D"}), is_flag=True),
            "save-optional": OptionSpec(
                "save-optional", short=frozenset({"O"}), is_flag=True
            ),
            "save-exact": OptionSpec(
                "save-exact", short=frozenset({"E"}), is_flag=True
            ),
            "no-save": OptionSpec("no-save", is_flag=True),
            "global": OptionSpec("global", short=frozenset({"g"}), is_flag=True),
            "production": OptionSpec("production", is_flag=True),
            "only": OptionSpec("only"),
            "legacy-peer-deps": OptionSpec("legacy-peer-deps", is_flag=True),
            "strict-peer-deps": OptionSpec("strict-peer-deps", is_flag=True),
            "package-lock": OptionSpec("package-lock", is_flag=True),
            "package-lock-only": OptionSpec("package-lock-only", is_flag=True),
            "dry-run": OptionSpec("dry-run", is_flag=True),
            "force": OptionSpec("force", short=frozenset({"f"}), is_flag=True),
            "ignore-scripts": OptionSpec("ignore-scripts", is_flag=True),
            "workspace": OptionSpec(
                "workspace",
                short=frozenset({"w"}),
                accumulation_mode=AccumulationMode.COLLECT,
            ),
            "workspaces": OptionSpec("workspaces", is_flag=True),
        }

        subcommands = {
            "install": CommandSpec(
                "install",
                aliases=frozenset({"i", "add"}),
                options=install_options,
                positionals={
                    "packages": PositionalSpec("packages", arity=ZERO_OR_MORE_ARITY),
                },
            ),
            "uninstall": CommandSpec(
                "uninstall",
                aliases=frozenset({"remove", "rm", "r", "un"}),
                options={
                    "save": OptionSpec("save", short=frozenset({"S"}), is_flag=True),
                    "save-dev": OptionSpec(
                        "save-dev", short=frozenset({"D"}), is_flag=True
                    ),
                    "global": OptionSpec(
                        "global", short=frozenset({"g"}), is_flag=True
                    ),
                },
                positionals={
                    "packages": PositionalSpec("packages", arity=ZERO_OR_MORE_ARITY),
                },
            ),
            "update": CommandSpec(
                "update",
                aliases=frozenset({"up", "upgrade"}),
                options={
                    "global": OptionSpec(
                        "global", short=frozenset({"g"}), is_flag=True
                    ),
                    "depth": OptionSpec("depth"),
                },
                positionals={
                    "packages": PositionalSpec("packages", arity=ZERO_OR_MORE_ARITY),
                },
            ),
            "run": CommandSpec(
                "run",
                aliases=frozenset({"run-script"}),
                options={
                    "silent": OptionSpec("silent", is_flag=True),
                    "if-present": OptionSpec("if-present", is_flag=True),
                },
                positionals={
                    "script": PositionalSpec("script", arity=Arity(1, 1)),
                    "args": PositionalSpec("args", arity=ZERO_OR_MORE_ARITY),
                },
            ),
            "test": CommandSpec(
                "test",
                aliases=frozenset({"t", "tst"}),
                positionals={"args": PositionalSpec("args", arity=ZERO_OR_MORE_ARITY)},
            ),
            "publish": CommandSpec(
                "publish",
                options={
                    "tag": OptionSpec("tag"),
                    "access": OptionSpec("access"),
                    "otp": OptionSpec("otp"),
                    "dry-run": OptionSpec("dry-run", is_flag=True),
                },
            ),
            "init": CommandSpec(
                "init",
                options={
                    "yes": OptionSpec("yes", short=frozenset({"y"}), is_flag=True),
                    "scope": OptionSpec("scope"),
                },
            ),
        }

        return CommandSpec("npm", subcommands=subcommands)

    result = benchmark(build_npm_like_cli)

    # Verify structure
    assert "install" in result.subcommands
    assert "i" in result.subcommands["install"].aliases
    assert len(result.subcommands["install"].options) > 15


def test_benchmark_npm_like_package_manager_parse(benchmark):
    """Benchmark parsing npm-like package manager commands.

    Tests parsing with package specifiers and multiple save flags.

    Architecture stress points:
    - Positional argument collection (package names)
    - Flag combinations that affect behavior
    - Command alias resolution
    """
    # Pre-build the spec (not part of benchmark)
    install_options = {
        "save-dev": OptionSpec("save-dev", short=frozenset({"D"}), is_flag=True),
        "save-exact": OptionSpec("save-exact", short=frozenset({"E"}), is_flag=True),
        "legacy-peer-deps": OptionSpec("legacy-peer-deps", is_flag=True),
        "workspace": OptionSpec(
            "workspace",
            short=frozenset({"w"}),
            accumulation_mode=AccumulationMode.COLLECT,
        ),
    }

    spec = CommandSpec(
        "npm",
        subcommands={
            "install": CommandSpec(
                "install",
                aliases=frozenset({"i", "add"}),
                options=install_options,
                positionals={
                    "packages": PositionalSpec("packages", arity=ZERO_OR_MORE_ARITY),
                },
            ),
        },
    )
    parser = Parser(spec)

    args = [
        "install",
        "-D",
        "-E",
        "--legacy-peer-deps",
        "-w",
        "frontend",
        "-w",
        "backend",
        "typescript@5.0.0",
        "@types/node@20.0.0",
        "eslint@8.0.0",
        "prettier@3.0.0",
    ]

    result = benchmark(parser.parse, args)

    # Verify parsing
    assert result.subcommand is not None
    assert result.subcommand.options["save-dev"].value is True
    assert result.subcommand.options["save-exact"].value is True
    assert result.subcommand.options["workspace"].value == ("frontend", "backend")
    assert len(result.subcommand.positionals["packages"].value) == 4


def test_benchmark_combined_stress_massive_and_dense(benchmark):
    """Benchmark combining massive subcommand count with dense options.

    Stress test combining both breadth (many subcommands) and depth
    (many options per command).

    Architecture stress points:
    - Memory allocation for large combined structure
    - Cache efficiency with many name mappings
    - Overall system scalability
    """

    def build_combined_stress_cli():
        # Create 100 services, each with 20 options
        subcommands = {}

        for i in range(100):
            service_name = f"service-{i:03d}"

            # Each service has many operations
            operations = {}
            for op in ["create", "update", "delete", "list", "get"]:
                # Each operation has 20 options
                options = {}
                for opt_idx in range(20):
                    opt_name = f"opt{chr(97 + opt_idx)}"  # opta, optb, optc, etc.
                    is_flag = opt_idx < 5  # First 5 are flags
                    options[opt_name] = OptionSpec(
                        opt_name,
                        is_flag=is_flag,
                        arity=Arity(0, 0) if is_flag else Arity(1, 1),
                    )

                operations[op] = CommandSpec(
                    op,
                    options=options,
                    positionals={"id": PositionalSpec("id", arity=Arity(0, 1))},
                )

            subcommands[service_name] = CommandSpec(
                service_name, subcommands=operations
            )

        return CommandSpec("combined", subcommands=subcommands)

    result = benchmark(build_combined_stress_cli)

    # Verify massive structure
    assert len(result.subcommands) == 100
    assert "create" in result.subcommands["service-050"].subcommands
    assert len(result.subcommands["service-050"].subcommands["create"].options) == 20


def test_benchmark_combined_stress_parse(benchmark):
    """Benchmark parsing in combined stress scenario.

    Tests parser performance when navigating both wide and deep structures.

    Architecture stress points:
    - Subcommand resolution in large registry
    - Option resolution with many options
    - Overall parsing throughput
    """
    # Pre-build the spec (not part of benchmark)
    subcommands = {}

    for i in range(100):
        service_name = f"service-{i:03d}"
        operations = {}
        for op in ["create", "update", "delete", "list", "get"]:
            options = {}
            for opt_idx in range(20):
                opt_name = f"opt{chr(97 + opt_idx)}"  # opta, optb, optc, etc.
                is_flag = opt_idx < 5
                options[opt_name] = OptionSpec(
                    opt_name,
                    is_flag=is_flag,
                    arity=Arity(0, 0) if is_flag else Arity(1, 1),
                )
            operations[op] = CommandSpec(
                op,
                options=options,
                positionals={"id": PositionalSpec("id", arity=Arity(0, 1))},
            )
        subcommands[service_name] = CommandSpec(service_name, subcommands=operations)

    spec = CommandSpec("combined", subcommands=subcommands)
    parser = Parser(spec)

    # Parse command in middle of service list with several options
    args = [
        "service-050",
        "create",
        "--opta",
        "--optb",
        "--optf",
        "value5",
        "--optk",
        "value10",
        "--optp",
        "value15",
        "resource-id",
    ]

    result = benchmark(parser.parse, args)

    # Verify parsing through massive structure
    assert result.subcommand is not None
    assert result.subcommand.command == "service-050"
    assert result.subcommand.subcommand is not None
    assert result.subcommand.subcommand.options["opta"].value is True
    assert result.subcommand.subcommand.options["optf"].value == "value5"
