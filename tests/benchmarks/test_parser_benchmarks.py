
# pyright: reportUnknownParameterType=false, reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
# pyright: reportMissingParameterType=false, reportUnusedCallResult=false
# Note: Type checking disabled for benchmark fixtures which don't have type stubs

import contextlib

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import ZERO_OR_MORE_ARITY, AccumulationMode, Arity


def test_benchmark_simple_parsing(benchmark):
    # Setup code runs once, not included in timing
    spec = CommandSpec(
        "test",
        options={
            "verbose": OptionSpec("verbose", short=frozenset({"v"}), is_flag=True),
            "output": OptionSpec("output", short=frozenset({"o"})),
        },
    )
    parser = Parser(spec)

    # Benchmark the parsing operation
    result = benchmark(parser.parse, ["-v", "-o", "file.txt"])

    # Verify correctness
    assert result.options["verbose"].value is True
    assert result.options["output"].value == "file.txt"


def test_benchmark_combined_short_options(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "x": OptionSpec("x", is_flag=True),
            "v": OptionSpec("v", is_flag=True),
            "f": OptionSpec("f", is_flag=True),
            "z": OptionSpec("z", is_flag=True),
            "a": OptionSpec("a", is_flag=True),
        },
    )
    parser = Parser(spec)

    result = benchmark(parser.parse, ["-xvfza"])

    # Verify correctness
    assert result.options["x"].value is True
    assert result.options["v"].value is True
    assert result.options["f"].value is True
    assert result.options["z"].value is True
    assert result.options["a"].value is True


def test_benchmark_many_options(benchmark):
    option_names = [
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "zeta",
        "eta",
        "theta",
        "iota",
        "kappa",
        "lambda",
        "mu",
        "nu",
        "xi",
        "omicron",
        "pi",
        "rho",
        "sigma",
        "tau",
        "upsilon",
    ]
    spec = CommandSpec(
        "test",
        options={name: OptionSpec(name, is_flag=True) for name in option_names},
    )
    parser = Parser(spec)
    args = [f"--{name}" for name in option_names]

    result = benchmark(parser.parse, args)

    # Verify all options are set
    assert all(result.options[name].value is True for name in option_names)


def test_benchmark_empty_args(benchmark):
    spec = CommandSpec("test")
    parser = Parser(spec)

    result = benchmark(parser.parse, [])

    # Verify empty result
    assert len(result.options) == 0
    # Note: Parser adds default 'args' positional, so check it's empty
    assert result.positionals["args"].value == ()


def test_benchmark_option_value_consumption(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "files": OptionSpec("files", short=frozenset({"f"}), arity=Arity(1, 5)),
        },
    )
    parser = Parser(spec)

    result = benchmark(
        parser.parse, ["-f", "file1", "file2", "file3", "file4", "file5"]
    )

    # Verify values consumed
    assert result.options["files"].value == (
        "file1",
        "file2",
        "file3",
        "file4",
        "file5",
    )


def test_benchmark_positional_grouping_few(benchmark):
    spec = CommandSpec(
        "test",
        positionals={
            "source": PositionalSpec("source", arity=Arity(1, 1)),
            "dest": PositionalSpec("dest", arity=Arity(1, 1)),
            "extras": PositionalSpec("extras", arity=ZERO_OR_MORE_ARITY),
        },
    )
    parser = Parser(spec)
    args = ["file1.txt", "file2.txt", "extra1", "extra2", "extra3"]

    result = benchmark(parser.parse, args)

    # Verify positionals grouped correctly
    assert result.positionals["source"].value == "file1.txt"
    assert result.positionals["dest"].value == "file2.txt"
    assert result.positionals["extras"].value == ("extra1", "extra2", "extra3")


def test_benchmark_positional_grouping_many(benchmark):
    # Create 10 positional specs
    pos_names = [
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
        "ninth",
        "tenth",
    ]
    spec = CommandSpec(
        "test",
        positionals={
            name: PositionalSpec(name, arity=Arity(1, 1)) for name in pos_names
        },
    )
    parser = Parser(spec)
    args = [f"value-{name}" for name in pos_names]

    result = benchmark(parser.parse, args)

    # Verify all positionals assigned
    assert all(result.positionals[name].value == f"value-{name}" for name in pos_names)


def test_benchmark_positional_grouping_very_many(benchmark):
    # Create 20 positional specs
    pos_names = [
        "arg-a",
        "arg-b",
        "arg-c",
        "arg-d",
        "arg-e",
        "arg-f",
        "arg-g",
        "arg-h",
        "arg-i",
        "arg-j",
        "arg-k",
        "arg-l",
        "arg-m",
        "arg-n",
        "arg-o",
        "arg-p",
        "arg-q",
        "arg-r",
        "arg-s",
        "arg-t",
    ]
    spec = CommandSpec(
        "test",
        positionals={
            name: PositionalSpec(name, arity=Arity(1, 1)) for name in pos_names
        },
    )
    parser = Parser(spec)
    args = [f"value-{name}" for name in pos_names]

    result = benchmark(parser.parse, args)

    # Verify all positionals assigned
    assert all(result.positionals[name].value == f"value-{name}" for name in pos_names)


def test_benchmark_option_accumulation_collect_10(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "include": OptionSpec(
                "include",
                short=frozenset({"i"}),
                accumulation_mode=AccumulationMode.COLLECT,
            )
        },
    )
    parser = Parser(spec)
    # Test with 10 occurrences
    values = [
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "zeta",
        "eta",
        "theta",
        "iota",
        "kappa",
    ]
    args: list[str] = []
    for val in values:
        args.extend(["-i", val])

    result = benchmark(parser.parse, args)

    # Verify collection
    assert result.options["include"].value == tuple(values)


def test_benchmark_option_accumulation_collect_50(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "include": OptionSpec(
                "include",
                short=frozenset({"i"}),
                accumulation_mode=AccumulationMode.COLLECT,
            )
        },
    )
    parser = Parser(spec)
    # Test with 50 occurrences
    args: list[str] = []
    expected_values = []
    for i in range(50):
        value = f"val-{chr(65 + i % 26)}-{i // 26}"
        args.extend(["-i", value])
        expected_values.append(value)

    result = benchmark(parser.parse, args)

    # Verify collection
    assert result.options["include"].value == tuple(expected_values)


def test_benchmark_option_accumulation_count(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "verbose": OptionSpec(
                "verbose",
                short=frozenset({"v"}),
                is_flag=True,
                accumulation_mode=AccumulationMode.COUNT,
            )
        },
    )
    parser = Parser(spec)
    args = ["-v"] * 20

    result = benchmark(parser.parse, args)

    # Verify count
    assert result.options["verbose"].value == 20


def test_benchmark_subcommand_resolution(benchmark):
    subcommand = CommandSpec(
        "sub",
        options={
            "flag": OptionSpec("flag", short=frozenset({"f"}), is_flag=True),
        },
    )
    spec = CommandSpec("test", subcommands={"sub": subcommand})
    parser = Parser(spec)

    result = benchmark(parser.parse, ["sub", "-f"])

    # Verify subcommand
    assert result.subcommand is not None
    assert result.subcommand.options["flag"].value is True


def test_benchmark_deep_subcommand_nesting(benchmark):
    # Create nested subcommands: cmd > sub1 > sub2 > sub3
    sub3 = CommandSpec(
        "sub3",
        options={"opt": OptionSpec("opt", is_flag=True)},
    )
    sub2 = CommandSpec("sub2", subcommands={"sub3": sub3})
    sub1 = CommandSpec("sub1", subcommands={"sub2": sub2})
    spec = CommandSpec("test", subcommands={"sub1": sub1})
    parser = Parser(spec)

    result = benchmark(parser.parse, ["sub1", "sub2", "sub3", "--opt"])

    # Verify deep nesting
    assert result.subcommand is not None
    assert result.subcommand.subcommand is not None
    assert result.subcommand.subcommand.subcommand is not None
    assert result.subcommand.subcommand.subcommand.options["opt"].value is True


def test_benchmark_complex_realistic(benchmark):
    spec = CommandSpec(
        "git",
        options={
            "verbose": OptionSpec(
                "verbose",
                short=frozenset({"v"}),
                is_flag=True,
                accumulation_mode=AccumulationMode.COUNT,
            ),
            "quiet": OptionSpec("quiet", short=frozenset({"q"}), is_flag=True),
        },
        subcommands={
            "commit": CommandSpec(
                "commit",
                options={
                    "message": OptionSpec("message", short=frozenset({"m"})),
                    "all": OptionSpec("all", short=frozenset({"a"}), is_flag=True),
                    "amend": OptionSpec("amend", is_flag=True),
                },
                positionals={
                    "files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY),
                },
            ),
        },
    )
    parser = Parser(spec)

    result = benchmark(
        parser.parse, ["-vv", "commit", "-am", "Initial commit", "--amend"]
    )

    # Verify complex parsing
    assert result.options["verbose"].value == 2
    assert result.subcommand is not None
    assert result.subcommand.options["all"].value is True
    assert result.subcommand.options["message"].value == "Initial commit"
    assert result.subcommand.options["amend"].value is True


def test_benchmark_abbreviation_matching_success(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "verbose": OptionSpec("verbose", is_flag=True),
            "output": OptionSpec("output", is_flag=True),
            "verify": OptionSpec("verify", is_flag=True),
        },
    )
    parser = Parser(spec, allow_abbreviated_options=True)

    result = benchmark(parser.parse, ["--verb", "--out", "--veri"])

    # Verify abbreviations matched
    assert result.options["verbose"].value is True
    assert result.options["output"].value is True
    assert result.options["verify"].value is True


def test_benchmark_abbreviation_matching_baseline(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "verbose": OptionSpec("verbose", is_flag=True),
            "output": OptionSpec("output", is_flag=True),
            "verify": OptionSpec("verify", is_flag=True),
        },
    )
    parser = Parser(spec, allow_abbreviated_options=False)

    result = benchmark(parser.parse, ["--verbose", "--output", "--verify"])

    # Verify full names matched
    assert result.options["verbose"].value is True
    assert result.options["output"].value is True
    assert result.options["verify"].value is True


def test_benchmark_validation_error_missing_required(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "required": OptionSpec("required", arity=Arity(1, 1)),
        },
    )
    parser = Parser(spec)

    # Create wrapper for error case
    def parse_with_error():
        with contextlib.suppress(Exception):
            parser.parse([])  # Missing required option

    # Benchmark the error path
    benchmark(parse_with_error)


def test_benchmark_validation_error_unknown_option(benchmark):
    spec = CommandSpec("test", options={})
    parser = Parser(spec)

    # Create wrapper for error case
    def parse_with_error():
        with contextlib.suppress(Exception):
            parser.parse(["--unknown"])

    # Benchmark the error path
    benchmark(parse_with_error)


def test_benchmark_realistic_mixed_all_features(benchmark):
    spec = CommandSpec(
        "app",
        options={
            "verbose": OptionSpec(
                "verbose",
                short=frozenset({"v"}),
                is_flag=True,
                accumulation_mode=AccumulationMode.COUNT,
            ),
            "config": OptionSpec("config", short=frozenset({"c"})),
            "include": OptionSpec(
                "include",
                short=frozenset({"i"}),
                accumulation_mode=AccumulationMode.COLLECT,
            ),
            "quiet": OptionSpec("quiet", short=frozenset({"q"}), is_flag=True),
        },
        positionals={
            "command": PositionalSpec("command", arity=Arity(1, 1)),
            "files": PositionalSpec("files", arity=ZERO_OR_MORE_ARITY),
        },
    )
    parser = Parser(spec)

    result = benchmark(
        parser.parse,
        [
            "-vv",
            "-c",
            "config.json",
            "-i",
            "*.py",
            "-i",
            "*.js",
            "build",
            "src/",
            "tests/",
            "docs/",
        ],
    )

    # Verify mixed features
    assert result.options["verbose"].value == 2
    assert result.options["config"].value == "config.json"
    assert result.options["include"].value == ("*.py", "*.js")
    assert result.positionals["command"].value == "build"
    assert result.positionals["files"].value == ("src/", "tests/", "docs/")


def test_benchmark_only_double_dash(benchmark):
    spec = CommandSpec(
        "test",
        positionals={
            "args": PositionalSpec("args", arity=ZERO_OR_MORE_ARITY),
        },
    )
    parser = Parser(spec)

    result = benchmark(parser.parse, ["--", "arg1", "arg2", "arg3"])

    # Verify trailing args after double-dash
    assert result.extra_args == ("arg1", "arg2", "arg3")


def test_benchmark_negative_numbers_as_positionals(benchmark):
    spec = CommandSpec(
        "test",
        positionals={
            "values": PositionalSpec("values", arity=ZERO_OR_MORE_ARITY),
        },
    )
    parser = Parser(spec, allow_negative_numbers=True)

    result = benchmark(parser.parse, ["-1", "-3.14", "-2.5e10", "-0"])

    # Verify negative numbers parsed correctly
    assert result.positionals["values"].value == ("-1", "-3.14", "-2.5e10", "-0")


def test_benchmark_negative_numbers_as_option_values(benchmark):
    spec = CommandSpec(
        "test",
        options={
            "min": OptionSpec("min", arity=Arity(1, 1)),
            "max": OptionSpec("max", arity=Arity(1, 1)),
            "threshold": OptionSpec("threshold", arity=Arity(1, 1)),
        },
    )
    parser = Parser(spec, allow_negative_numbers=True)

    result = benchmark(
        parser.parse, ["--min", "-100", "--max", "100", "--threshold", "-1.5e-10"]
    )

    # Verify negative option values
    assert result.options["min"].value == "-100"
    assert result.options["max"].value == "100"
    assert result.options["threshold"].value == "-1.5e-10"


def test_benchmark_mixed_positive_negative_numbers(benchmark):
    spec = CommandSpec(
        "test",
        positionals={
            "coords": PositionalSpec("coords", arity=ZERO_OR_MORE_ARITY),
        },
    )
    parser = Parser(spec, allow_negative_numbers=True)

    result = benchmark(
        parser.parse, ["5", "-3", "10.5", "-7.2", "0", "-0", "100", "-999"]
    )

    # Verify mixed values
    assert result.positionals["coords"].value == (
        "5",
        "-3",
        "10.5",
        "-7.2",
        "0",
        "-0",
        "100",
        "-999",
    )
