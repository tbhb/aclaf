"""Performance benchmarks for the ACLAF parser.

This module contains comprehensive performance tests to measure the parser's
efficiency across various scenarios.
"""

import contextlib
import timeit
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aclaf.parser import CommandSpec, OptionSpec, Parser, PositionalSpec
from aclaf.parser.types import ZERO_OR_MORE_ARITY, AccumulationMode, Arity

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    name: str
    description: str
    iterations: int
    total_time: float
    avg_time_ms: float
    ops_per_sec: float


def run_benchmark(
    name: str,
    description: str,
    fn: "Callable[[], object]",
    iterations: int = 10000,
) -> BenchmarkResult:
    """Run a benchmark and return results."""
    total_time = timeit.timeit(fn, number=iterations)
    avg_time_ms = (total_time / iterations) * 1000
    ops_per_sec = iterations / total_time

    return BenchmarkResult(
        name=name,
        description=description,
        iterations=iterations,
        total_time=total_time,
        avg_time_ms=avg_time_ms,
        ops_per_sec=ops_per_sec,
    )


def benchmark_simple_parsing():
    """Baseline: simple command with a few options."""
    spec = CommandSpec(
        "test",
        options=[
            OptionSpec("verbose", short="v", is_flag=True),
            OptionSpec("output", short="o"),
        ],
    )
    parser = Parser(spec)

    def parse():
        _ = parser.parse(["-v", "-o", "file.txt"])

    return run_benchmark(
        "simple_parsing",
        "Parse simple command with 2 options",
        parse,
    )


def benchmark_combined_short_options():
    """Test combined short option parsing (-xvf)."""
    spec = CommandSpec(
        "test",
        options=[
            OptionSpec("x", is_flag=True),
            OptionSpec("v", is_flag=True),
            OptionSpec("f", is_flag=True),
            OptionSpec("z", is_flag=True),
            OptionSpec("a", is_flag=True),
        ],
    )
    parser = Parser(spec)

    def parse():
        _ = parser.parse(["-xvfza"])

    return run_benchmark(
        "combined_short_options",
        "Parse 5 combined short flags (-xvfza)",
        parse,
    )


def benchmark_many_options():
    """Test parsing many separate options."""
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
        options=[OptionSpec(name, is_flag=True) for name in option_names],
    )
    parser = Parser(spec)
    args = [f"--{name}" for name in option_names]

    def parse():
        _ = parser.parse(args)

    return run_benchmark(
        "many_options",
        "Parse 20 separate long options",
        parse,
    )


def benchmark_positional_grouping_few():
    """Test positional grouping with few specs (baseline)."""
    spec = CommandSpec(
        "test",
        positionals=[
            PositionalSpec("source", arity=Arity(1, 1)),
            PositionalSpec("dest", arity=Arity(1, 1)),
            PositionalSpec("extras", arity=ZERO_OR_MORE_ARITY),
        ],
    )
    parser = Parser(spec)
    args = ["file1.txt", "file2.txt", "extra1", "extra2", "extra3"]

    def parse():
        _ = parser.parse(args)

    return run_benchmark(
        "positional_grouping_few",
        "Group 5 positionals across 3 specs",
        parse,
    )


def benchmark_positional_grouping_many():
    """Test positional grouping with many specs (O(s²) test)."""
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
        positionals=[PositionalSpec(name, arity=Arity(1, 1)) for name in pos_names],
    )
    parser = Parser(spec)
    args = [f"value-{name}" for name in pos_names]

    def parse():
        _ = parser.parse(args)

    return run_benchmark(
        "positional_grouping_many",
        "Group 10 positionals across 10 specs (tests O(s²))",
        parse,
    )


def benchmark_positional_grouping_very_many():
    """Test positional grouping with very many specs."""
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
        positionals=[PositionalSpec(name, arity=Arity(1, 1)) for name in pos_names],
    )
    parser = Parser(spec)
    args = [f"value-{name}" for name in pos_names]

    def parse():
        _ = parser.parse(args)

    return run_benchmark(
        "positional_grouping_very_many",
        "Group 20 positionals across 20 specs (tests O(s²))",
        parse,
        iterations=5000,  # Reduce iterations for slower test
    )


def benchmark_option_accumulation_collect():
    """Test option accumulation with COLLECT mode (tuple concatenation)."""
    spec = CommandSpec(
        "test",
        options=[
            OptionSpec(
                "include",
                short="i",
                accumulation_mode=AccumulationMode.COLLECT,
            )
        ],
    )
    parser = Parser(spec)
    # Test with 10 occurrences
    args: list[str] = []
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
    val: str
    for val in values:
        args.extend(["-i", val])

    def parse():
        _ = parser.parse(args)

    return run_benchmark(
        "option_accumulation_collect_10",
        "Accumulate 10 option occurrences with COLLECT mode",
        parse,
    )


def benchmark_option_accumulation_collect_many():
    """Test option accumulation with many occurrences."""
    spec = CommandSpec(
        "test",
        options=[
            OptionSpec(
                "include",
                short="i",
                accumulation_mode=AccumulationMode.COLLECT,
            )
        ],
    )
    parser = Parser(spec)
    # Test with 50 occurrences
    args: list[str] = []
    i: int
    for i in range(50):
        args.extend(["-i", f"val-{chr(65 + i % 26)}-{i // 26}"])

    def parse():
        _ = parser.parse(args)

    return run_benchmark(
        "option_accumulation_collect_50",
        "Accumulate 50 option occurrences (tests tuple concatenation)",
        parse,
        iterations=5000,
    )


def benchmark_option_accumulation_count():
    """Test option accumulation with COUNT mode."""
    spec = CommandSpec(
        "test",
        options=[
            OptionSpec(
                "verbose",
                short="v",
                is_flag=True,
                accumulation_mode=AccumulationMode.COUNT,
            )
        ],
    )
    parser = Parser(spec)
    args = ["-v"] * 20

    def parse():
        _ = parser.parse(args)

    return run_benchmark(
        "option_accumulation_count",
        "Count 20 flag occurrences",
        parse,
    )


def benchmark_subcommand_resolution():
    """Test subcommand resolution."""
    subcommand = CommandSpec(
        "sub",
        options=[OptionSpec("flag", short="f", is_flag=True)],
    )
    spec = CommandSpec("test", subcommands=[subcommand])
    parser = Parser(spec)

    def parse():
        _ = parser.parse(["sub", "-f"])

    return run_benchmark(
        "subcommand_resolution",
        "Parse command with subcommand",
        parse,
    )


def benchmark_deep_subcommand_nesting():
    """Test deep subcommand nesting."""
    # Create nested subcommands: cmd > sub1 > sub2 > sub3
    sub3 = CommandSpec("sub3", options=[OptionSpec("opt", is_flag=True)])
    sub2 = CommandSpec("sub2", subcommands=[sub3])
    sub1 = CommandSpec("sub1", subcommands=[sub2])
    spec = CommandSpec("test", subcommands=[sub1])
    parser = Parser(spec)

    def parse():
        _ = parser.parse(["sub1", "sub2", "sub3", "--opt"])

    return run_benchmark(
        "deep_subcommand_nesting",
        "Parse 3-level nested subcommands",
        parse,
    )


def benchmark_complex_realistic():
    """Realistic complex command with mixed features."""
    spec = CommandSpec(
        "git",
        options=[
            OptionSpec(
                "verbose",
                short="v",
                is_flag=True,
                accumulation_mode=AccumulationMode.COUNT,
            ),
            OptionSpec("quiet", short="q", is_flag=True),
        ],
        subcommands=[
            CommandSpec(
                "commit",
                options=[
                    OptionSpec("message", short="m"),
                    OptionSpec("all", short="a", is_flag=True),
                    OptionSpec("amend", is_flag=True),
                ],
                positionals=[
                    PositionalSpec("files", arity=ZERO_OR_MORE_ARITY),
                ],
            ),
        ],
    )
    parser = Parser(spec)

    def parse():
        _ = parser.parse(["-vv", "commit", "-am", "Initial commit", "--amend"])

    return run_benchmark(
        "complex_realistic",
        "Realistic git-like command with options and subcommand",
        parse,
    )


def benchmark_abbreviation_matching():
    """Test abbreviated option matching."""
    spec = CommandSpec(
        "test",
        options=[
            OptionSpec("verbose", is_flag=True),
            OptionSpec("version", is_flag=True),
            OptionSpec("verify", is_flag=True),
        ],
    )
    parser = Parser(spec, allow_abbreviated_options=True)

    def parse():
        _ = parser.parse(["--verb"])  # Ambiguous, will fail but still tests resolution

    # This will error, so we catch it
    def safe_parse():
        with contextlib.suppress(Exception):
            parse()

    return run_benchmark(
        "abbreviation_matching",
        "Test abbreviated option matching (with caching)",
        safe_parse,
    )


def benchmark_option_value_consumption():
    """Test option value consumption from arguments."""
    spec = CommandSpec(
        "test",
        options=[
            OptionSpec("files", short="f", arity=Arity(1, 5)),
        ],
    )
    parser = Parser(spec)

    def parse():
        _ = parser.parse(["-f", "file1", "file2", "file3", "file4", "file5"])

    return run_benchmark(
        "option_value_consumption",
        "Consume 5 values for an option",
        parse,
    )


def run_all_benchmarks() -> list[BenchmarkResult]:
    """Run all benchmarks and return results."""
    benchmarks = [
        benchmark_simple_parsing,
        benchmark_combined_short_options,
        benchmark_many_options,
        benchmark_positional_grouping_few,
        benchmark_positional_grouping_many,
        benchmark_positional_grouping_very_many,
        benchmark_option_accumulation_collect,
        benchmark_option_accumulation_collect_many,
        benchmark_option_accumulation_count,
        benchmark_subcommand_resolution,
        benchmark_deep_subcommand_nesting,
        benchmark_complex_realistic,
        benchmark_abbreviation_matching,
        benchmark_option_value_consumption,
    ]

    results: list[BenchmarkResult] = []
    _i: int
    benchmark_fn: Callable[[], BenchmarkResult]
    for _i, benchmark_fn in enumerate(benchmarks, 1):
        result = benchmark_fn()
        results.append(result)

    return results


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results in a formatted table."""

    for _result in results:
        pass

    # Performance analysis

    # Find slowest benchmarks
    sorted_by_time = sorted(results, key=lambda r: r.avg_time_ms, reverse=True)
    for _i, _result in enumerate(sorted_by_time[:5], 1):
        pass

    # Find fastest benchmarks
    sorted_by_time_asc = sorted(results, key=lambda r: r.avg_time_ms)
    for _i, _result in enumerate(sorted_by_time_asc[:5], 1):
        pass

    # Scaling analysis

    # Compare positional grouping with different sizes
    pos_few = next(r for r in results if r.name == "positional_grouping_few")
    _ = next(r for r in results if r.name == "positional_grouping_many")
    _ = next(r for r in results if r.name == "positional_grouping_very_many")

    _ = pos_few.avg_time_ms * (10 / 3) ** 2
    _ = pos_few.avg_time_ms * (10 / 3)

    # Compare option accumulation
    acc_10 = next(r for r in results if r.name == "option_accumulation_collect_10")
    _ = next(r for r in results if r.name == "option_accumulation_collect_50")

    _ = acc_10.avg_time_ms * (50 / 10) ** 2
    _ = acc_10.avg_time_ms * (50 / 10)


if __name__ == "__main__":
    results = run_all_benchmarks()
    print_results(results)
