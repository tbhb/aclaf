# Architecture and execution flow

This document explains how Aclaf processes commands from registration through execution. Understanding this flow helps when building applications with the framework, debugging unexpected behavior, or contributing to the framework itself. The architecture emphasizes immutability, type safety, and clear separation of concerns across distinct phases.

## Overview

Aclaf's architecture divides command processing into five distinct phases, each with specific responsibilities and data structures:

1. **Registration** - Commands are defined using decorators or direct construction, extracting metadata from function signatures and type annotations
2. **Specification conversion** - Mutable builder types transform into immutable runtime representations, then into parser specifications
3. **Parsing** - Command-line arguments are processed into structured parse results containing options, positionals, and subcommands
4. **Conversion and validation** - Parsed string values are converted to Python types and validated against constraints
5. **Execution** - Commands execute with converted parameters, injected dependencies, and context propagation

Each phase operates on different data structures optimized for its purpose. Registration uses mutable builders for flexibility during construction. Runtime uses immutable frozen dataclasses for thread safety and caching. The parser uses specialized specifications focused purely on argument parsing without conversion concerns. This separation means each component has exactly the information it needs without coupling to other phases.

The framework bridges these phases through well-defined integration points where data transforms from one representation to another. These transformation points are where the architecture's power becomes evident, converting developer-friendly decorators into efficient parsing specifications and type-safe function invocations.

## Command registration

Command registration is where applications define their command structure, parameters, and behavior. The framework provides two primary mechanisms: decorator-based registration for ergonomic command definition and manual construction for programmatic control.

### Decorator-based registration

The `@app()` decorator creates a command directly from a function signature:

```python
from typing import Annotated
from aclaf import app

@app(name="deploy-tool")
def main(verbose: Annotated[bool, "--verbose", "-v"] = False) -> None:
    """A deployment tool."""
    pass
```

When Python encounters this decorator, the framework extracts everything needed to build a command. It inspects the function signature using Python's `inspect` module to discover parameters, retrieves type annotations including metadata from `Annotated` types, identifies special parameters like `Context` that shouldn't be CLI arguments, and determines whether the function is async or sync. The result is an `App` instance, which is a specialized `Command` subclass representing the application root command.

The decorator approach minimizes boilerplate by deriving command structure from code that already exists. Function names become command names, parameters become CLI arguments, type hints drive automatic conversion, and docstrings provide help text. This aligns with modern Python practices where type annotations serve multiple purposes beyond static analysis.

### Manual construction

For programmatic control or when decorators are not suitable, commands can be constructed directly:

```python
from aclaf import Command, CommandParameter
from aclaf.parser import Arity, ParameterKind

cmd = Command(
    name="deploy",
    parameters={
        "env": CommandParameter(
            name="env",
            kind=ParameterKind.POSITIONAL,
            arity=Arity(1, 1),
            value_type=str,
        ),
        "verbose": CommandParameter(
            name="verbose",
            kind=ParameterKind.OPTION,
            long=("verbose",),
            short=("v",),
            is_flag=True,
            value_type=bool,
        ),
    },
    run_func=deploy_handler,
)
```

Direct construction exposes the full builder API, allowing precise control over every aspect of command configuration. This approach helps when generating commands dynamically, integrating with external configuration systems, or building higher-level abstractions on top of Aclaf.

### Subcommand registration

Complex applications often organize functionality into subcommands like `git commit` or `docker run`. Aclaf supports hierarchical command structures through subcommand registration.

The `@command()` decorator registers a function as a subcommand:

```python
@main.command(name="deploy")
def deploy(env: str, region: Annotated[str, "--region"] = "us-west-2") -> None:
    """Deploy to an environment."""
    pass
```

This creates a `Command` instance and registers it as a subcommand of `main`. The framework establishes parent-child relationships automatically, enabling context propagation and configuration inheritance. Parent commands cascade their converters, validators, and logger to subcommands, ensuring consistent behavior throughout the command hierarchy.

Commands can also mount after definition:

```python
external_cmd = load_command_from_plugin()
main.mount(external_cmd, name="plugin")
```

Mounting integrates externally defined commands into the hierarchy. The framework sets `is_mounted=True` to track mounted commands separately from decorated ones, which helps with debugging and introspection.

### Parameter extraction

Parameter extraction is where the framework translates Python function signatures into command specifications. This process involves multiple steps that happen automatically during command registration.

The framework starts with `inspect.signature()` to get the function's parameter structure. For each parameter, it retrieves type annotations separately using `get_annotations()`, which handles forward references and stringified annotations correctly. The framework then identifies special parameters that shouldn't be CLI arguments: parameters with type annotation `Context`, or parameters whose type annotation is an instance of `Console` or `Logger`.

For regular parameters, the framework examines their annotations to extract metadata. Python's `Annotated` type allows attaching metadata to type hints:

```python
verbose: Annotated[bool, "--verbose", "-v", "Enable verbose output"]
port: Annotated[int, "--port", Default(8080), Ge(1), Le(65535)]
files: Annotated[list[str], "--file", "*", Collect()]
```

The framework flattens this metadata from potentially nested `Annotated` types and processes each metadata object. Strings starting with `--` become long option names, strings starting with `-` become short option names, arity shortcuts like `"*"` or `"?"` define how many values the parameter accepts, and metadata objects like `Default()`, `Collect()`, or `Ge()` configure behavior and constraints.

The parameter kind (option vs. positional) is determined through a priority system. First, boolean parameters with defaults are immediately classified as flag options. Then, explicit `Opt()` or `Arg()` metadata takes precedence. If long or short names are specified with `--` or `-`, the parameter becomes an option. Boolean types without explicit kind configuration become flag options. Otherwise, the framework uses Python's parameter kind from the function signature, where `KEYWORD_ONLY` parameters become options and `POSITIONAL_OR_KEYWORD` parameters become positionals.

This metadata-driven approach means parameter configuration is declarative and type-checked. IDEs can autocomplete metadata objects, type checkers can verify metadata is used correctly, and the parameter's complete configuration is visible at its definition.

### Data structures for registration

The registration phase uses mutable dataclasses designed for building commands incrementally.

**Command** (`_command.py`) is the mutable builder for commands. It stores the command name, aliases, parameters as a dictionary, subcommands, the function to execute, converters for type conversion, validators for constraints, configuration like console and logger instances, and parser configuration. The class provides convenience methods for adding subcommands, registering converters, and configuring the command after construction.

**CommandParameter** (`_parameters.py`) is the mutable builder for parameters. It stores everything about a parameter: its kind (option or positional), name, arity specification, accumulation mode, long and short names, whether it's a flag, default values, the target type for conversion, custom converters and validators, and metadata for validation. Parameters can be built incrementally as metadata is discovered.

Both types are mutable during registration to support incremental construction, whether through decorators that build them piece by piece or manual construction that sets properties explicitly.

## Specification conversion

After registration completes, the framework converts mutable builders into immutable runtime representations. This conversion happens lazily on first invocation, transforming the command hierarchy into structures optimized for execution and parsing.

### Registration to runtime

The `to_runtime_command()` method on `Command` produces a `RuntimeCommand`:

```python
def to_runtime_command(self) -> RuntimeCommand:
    # Convert each command parameter to runtime parameter
    parameters = {
        name: param.to_runtime_parameter()
        for name, param in self.command_parameters.items()
    }

    # Recursively convert all subcommands
    subcommands = {
        name: cmd.to_runtime_command()
        for name, cmd in self.subcommands.items()
    }

    return RuntimeCommand(
        name=self.name,
        aliases=tuple(self.aliases),
        parameters=parameters,
        subcommands=subcommands,
        run_func=self.run_func,
        # ... additional configuration
    )
```

This transformation converts mutable types to immutable frozen dataclasses, replaces lists and dictionaries with tuples and mapping proxies, recursively converts the entire subcommand hierarchy, and excludes special parameters which are handled separately during execution.

**RuntimeCommand** is immutable with `@dataclass(slots=True, frozen=True)`, making instances thread-safe and usable as dictionary keys. All collections are immutable types like tuples and frozensets. The runtime command includes only what's needed for execution, dropping builder-specific concerns.

**RuntimeParameter** similarly freezes parameter configuration into an immutable representation with tuples and frozensets for collections.

### Runtime to parser specifications

Before parsing, runtime commands convert to parser specifications through `to_command_spec()`:

```python
def to_command_spec(self) -> CommandSpec:
    if self._cached_spec is None:
        spec = CommandSpec(
            name=self.name,
            aliases=frozenset(self.aliases),
            options={
                name: param.to_option_spec()
                for name, param in self.options.items()
            },
            positionals={
                name: param.to_positional_spec()
                for name, param in self.positionals.items()
            },
            subcommands={
                name: cmd.to_command_spec()
                for name, cmd in self.subcommands.items()
            }
        )
        object.__setattr__(self, "_cached_spec", spec)
    return self._cached_spec
```

Parser specifications are aggressively cached because they are expensive to build and never change. The conversion strips everything the parser does not need—converters, validators, and metadata disappear, leaving only names, arity specifications, accumulation modes, and flag configuration.

**OptionSpec** contains the parameter name, long and short name sets as frozensets for constant-time lookup, arity specification, accumulation mode, flag configuration including negation words and constant values, and value flattening preferences. Extensive validation in `__post_init__` ensures specification correctness before the parser ever sees it.

**PositionalSpec** is simpler with just a name and arity, since positionals have fewer configuration options than options.

**CommandSpec** brings these together with option and positional specs, subcommand specs recursively, parser configuration overrides, and cached name mappings for efficient option and subcommand resolution.

This multi-stage conversion (Command → RuntimeCommand → CommandSpec) separates concerns cleanly. The registration phase focuses on developer ergonomics, the runtime phase focuses on execution concerns, and the parser phase focuses purely on argument parsing without coupling to type conversion or validation.

## Parsing

The parser transforms command-line argument strings into structured data. It's a sophisticated single-pass, left-to-right implementation that handles options (both long and short forms), flags with various configurations, positional arguments with variable arity, subcommands with recursive parsing, and the `--` separator for trailing arguments.

### Parser architecture

The parser is built around `BaseParser`, an abstract base class defining the interface, and `Parser`, the concrete implementation. The parser is stateless and thread-safe—multiple threads can safely use the same parser instance since all state lives in the parse call, not the parser object.

Parser behavior is controlled by `ParserConfiguration`, which includes settings for abbreviation support, case sensitivity, strict option ordering, negative number handling, flag value support, and many other configurable behaviors. The default configuration provides sensible POSIX-like behavior while allowing customization when needed.

### Parsing algorithm

The parser's `parse()` method accepts a sequence of argument strings and returns a `ParseResult`. Internally, `_parse_argument_list()` implements the full parsing logic in a single monolithic method. While this might seem unwieldy, it keeps parsing state localized and makes the parse order explicit.

The parser maintains state during parsing: the current position in the argument list, accumulated options as they are parsed, positional arguments collected as strings, whether positionals have started (for strict mode), whether trailing mode is active (after `--`), and trailing arguments after the separator.

For each argument, the parser dispatches based on its form. After encountering `--`, all subsequent arguments are trailing arguments. The bare `--` token alone enters trailing mode. Arguments starting with `--` are long options, potentially with inline values like `--option=value`. Arguments starting with `-` but not followed by a digit are short options, which might be bundled like `-abc` or have inline values. Everything else is either a subcommand name or a positional argument.

### Option parsing

Long options are straightforward. The parser splits on `=` to separate the option name from any inline value, resolves the option name to an `OptionSpec` through the command spec's `resolve_option()` method, then parses the value based on the option's configuration.

Short options are more complex because they support bundling. The string `-abc` might be three separate flags or one option `-a` with value `bc`, depending on the specifications. The parser processes short options character by character, resolving each to an option spec, checking if it accepts values, and determining whether remaining characters are an inline value or additional options.

Option resolution handles normalization, converting underscores to dashes if configured, adjusting case for case-insensitive matching, and supporting abbreviations where `--verb` can match `--verbose` if unambiguous. The resolution logic checks for exact matches first, then tries abbreviations if enabled, validates minimum abbreviation length to prevent single-character accidents, and detects ambiguous abbreviations that match multiple options.

### Value parsing

Once an option is resolved, the parser must extract its values. The strategy depends on whether it's a flag, has an inline value, needs to consume following arguments, or some combination.

Flags are options with arity zero. Their presence sets a boolean value, typically `True`. Flags support negation words like `no`, so `--no-verbose` sets `verbose` to `False`. If configured with `allow_equals_for_flags=True`, flags can accept explicit values like `--verbose=yes` or `--verbose=false`. The parser checks these values against configured truthy and falsey sets.

Options with inline values consume those values immediately. For `--output=file.txt`, the value `file.txt` is attached to the option. Single-value options get scalar strings, while multi-value options get tuples.

Options without inline values consume following arguments. The parser calculates how many values are needed based on arity (minimum and maximum), advances through arguments consuming values, stops when it hits another option or subcommand, respects maximum arity if specified, and ensures minimum arity is satisfied or raises an error.

Negative numbers receive special handling. Normally `-1` looks like a short option, but with `allow_negative_numbers=True`, the parser checks if the string is a valid number before treating it as an option.

### Accumulation

When an option appears multiple times, accumulation mode determines the behavior. Last wins means each occurrence overwrites the previous value—the most recent wins. First wins means the first occurrence is kept and subsequent ones are ignored. Error mode raises `DuplicateOptionError` on duplicate occurrences. Collect mode gathers all values into a tuple, with structure depending on arity and value flattening. Count mode counts occurrences, useful for verbosity flags like `-vvv` meaning verbosity level 3.

The parser accumulates option values during parsing, then applies value flattening as a post-processing step for collected multi-value options when configured.

### Positional grouping

After consuming all options and subcommands, the parser groups positional strings according to positional specs. Each spec has an arity defining how many values it accepts. The parser validates that enough arguments exist to satisfy all minimum arity requirements, distributes arguments across specs respecting maximums, handles unbounded arity by consuming all remaining arguments except what is needed for subsequent positionals, and returns scalars for single-value positionals and tuples for multi-value.

If no positional specs exist, the parser creates an implicit `args` positional with unbounded arity, collecting all unused arguments. This implicit positional enables commands to accept arbitrary trailing arguments without explicit positional parameter definitions, useful for wrapper commands or pass-through scenarios.

### Subcommand parsing

When the parser encounters an argument that matches a subcommand name, it recursively parses the remainder. The parser resolves the subcommand name to a `CommandSpec`, recursively calls `_parse_argument_list()` with remaining arguments and the subcommand's spec, builds a `ParseResult` with the parent's options and positionals plus the nested subcommand result, and raises an internal `_SubcommandParsedError` exception containing the result.

This exception-based early exit might seem unusual, but it cleanly unwinds the parsing stack without complicated return value checking at every step. The top-level parse catches the exception and extracts the result.

### Parse result structure

The parser returns a `ParseResult`, a frozen immutable dataclass containing the command name that was executed, the alias used if any, options as a dictionary mapping parameter names to `ParsedOption` instances, positionals as a dictionary mapping parameter names to `ParsedPositional` instances, extra arguments after `--`, and a nested subcommand result if a subcommand was invoked.

`ParsedOption` and `ParsedPositional` wrap values with metadata about which alias was used and preserve the structure determined by arity and accumulation. Values are still strings or simple types like integers and booleans—type conversion happens in the next phase.

## Conversion and validation

The parser produces strings and simple types, but command functions expect domain types like `Path`, `datetime`, or custom classes. The conversion phase bridges this gap using a registry-based system that's both extensible and type-safe.

### Type conversion

The `_convert_parameters()` method walks through the parse result extracting option and positional values. For parameters missing from the parse result, if a default value or default factory exists, it's placed directly into the converted parameters dictionary without going through type conversion (defaults are assumed to already be the correct type). Each remaining value is then converted to its target type using converters.

Converters are functions that accept a parsed value and optional metadata, returning a converted Python value or raising `ConversionError`. The framework maintains a `ConverterRegistry` that maps types to converter functions with support for exact type matching, generic types like `list[str]`, union types, and protocol-based conversion.

Built-in converters handle common types. The string converter is essentially a pass-through operation, though it calls `str()` on non-string values for consistency. The integer converter uses `int()` with error handling, converting strings like `"42"` to integers. The float converter similarly wraps `float()`. The boolean converter is more sophisticated, recognizing truthy values like `"true"`, `"1"`, `"yes"`, and `"on"`, and falsey values like `"false"`, `"0"`, `"no"`, and `"off"`, all case-insensitively. Path conversion constructs `pathlib.Path` instances from strings.

For generic types, the converter recursively processes elements. Converting to `list[int]` means converting a tuple of strings to a list of integers by converting each element with the integer converter, then wrapping in a list. Nested generics like `dict[str, list[int]]` work recursively.

Custom converters can be registered for application-specific types:

```python
from datetime import datetime

def convert_timestamp(value: str, metadata) -> datetime:
    return datetime.fromisoformat(value)

app.converter(datetime)(convert_timestamp)
```

The converter registry checks the custom converter first before falling back to built-ins or generic converters. This allows applications to override default conversion behavior when needed.

### Validation

After conversion, the validation phase checks that values satisfy constraints. The framework uses a similar registry-based approach with `ParameterValidatorRegistry`.

Validators are functions that accept a value, all parameters, and metadata, returning `None` if validation passes or a tuple of error messages if it fails. This signature allows validators to perform cross-parameter validation when needed.

Built-in validators support common constraints from the `annotated-types` library. Numeric validators check `Gt` (greater than), `Ge` (greater than or equal), `Lt` (less than), and `Le` (less than or equal). The `MultipleOf` validator ensures values are divisible by a specified number. Length validators check `MinLen` and `MaxLen` for sequences and strings.

Validators are triggered by metadata in the type annotation:

```python
port: Annotated[int, Ge(1), Le(65535)]
name: Annotated[str, MinLen(1), MaxLen(100)]
```

Custom validators can be registered for application-specific constraints:

```python
from aclaf.metadata import BaseMetadata

class ValidEmail(BaseMetadata):
    pass

def validate_email(value: str, params, metadata: ValidEmail):
    if "@" not in value:
        return ("must be a valid email address",)
    return None

app.validator(ValidEmail)(validate_email)
```

The validator registry processes all metadata associated with a parameter, running each matching validator and collecting errors. If any validator fails, the parameter is marked with errors for later reporting.

### Error handling

Conversion and validation errors are collected rather than raised immediately. Conversion errors are collected in a dictionary mapping parameter names to error message strings during the `_convert_parameters()` method. These are then passed to `_validate_parameters()`, which adds validation errors (as tuples of error messages) to build a complete error picture. The framework can report all errors at once rather than stopping at the first failure—users see everything wrong with their input in one shot rather than fixing issues one at a time.

Error checking happens during dispatch. If the context contains errors and no subcommand was invoked (subcommands might override parent errors), the framework collects all errors into a `ValidationError` and raises it. This timing means parent commands can validate shared options while allowing subcommands to provide their own parameter validation.

## Execution

With parsed, converted, and validated parameters, the execution phase brings everything together to invoke command functions. This phase handles context creation, dependency injection, synchronous and asynchronous dispatch, and subcommand propagation.

### Context creation

The `Context` object encapsulates everything about the current execution. It is a frozen immutable dataclass containing the command name, command path as a tuple showing the full hierarchy like `("app", "deploy", "production")`, the parse result with raw parsed values, converted and validated parameters, validation errors if any, parameter sources tracking whether values came from CLI, defaults, or configuration files, a parent context for subcommands, async flag indicating whether async dispatch is needed, console and logger instances, and special parameter names for dependency injection.

Context creation happens in `invoke()` after parsing and conversion complete:

```python
context = Context(
    command=self.name,
    command_path=(self.name,),
    console=self.console or DefaultConsole(),
    errors=errors,
    is_async=self.check_async(parse_result),
    logger=self.logger,
    parameters=parameters,
    parse_result=parse_result,
)
```

The `is_async` flag is set by recursively checking whether the current command or any subcommand in the parse result is async. This allows the framework to use async dispatch if needed anywhere in the command hierarchy.

### Dispatch mechanisms

The `dispatch()` method orchestrates synchronous execution, checking for validation errors first, executing the command function, responding with the result through the response system, and dispatching subcommands if present.

The `dispatch_async()` method handles asynchronous execution similarly but awaits async command functions and async generators. The framework detects async functions automatically using `inspect.iscoroutinefunction()` during command registration, allowing mixed sync and async command hierarchies where a sync parent can have async subcommands.

Error checking happens at the start of dispatch. If errors exist and no subcommand was invoked, the framework raises `ValidationError` with all collected errors. The "no subcommand" check is important because parent command validation might fail while the subcommand's validation succeeds, and the subcommand should still execute.

### Function parameter binding

The `_make_run_parameters()` method constructs the keyword arguments for the command function. It starts with all converted CLI parameters from the context, then injects special parameters by name. If the command registered a context parameter name, it injects the context instance. If it registered a console parameter name, it injects the console. If it registered a logger parameter name, it injects the logger.

The result is a dictionary that's unpacked with `**` when calling the command function:

```python
def _execute_run_func(self, context: Context):
    return self.run_func(**self._make_run_parameters(context))
```

This approach means command functions receive parameters by name without caring about the framework's internals. A function declared as:

```python
def deploy(env: str, verbose: bool, context: Context, logger: Logger):
    pass
```

receives `env` and `verbose` from CLI arguments, and `context` and `logger` injected by the framework. The function signature is the contract—the framework fulfills it through parameter binding.

### Subcommand dispatch

When a subcommand exists in the parse result, the framework prepares subcommand dispatch by retrieving the subcommand from the command's subcommands mapping, converting and validating the subcommand's parameters from the nested parse result, creating a new context with the parent context linked, the command path extended, and the subcommand's parameters and errors.

The subcommand is then dispatched recursively, either through `dispatch()` or `dispatch_async()` depending on async detection. This recursive dispatch propagates context down the command hierarchy, allowing subcommands to access parent context and maintain the complete command path for debugging and help text.

## Key data structures

Understanding the major types helps when working with Aclaf's internals or debugging issues.

### Command types

**Command** is the mutable builder used during registration. It's a `@dataclass(slots=True)` with mutable attributes allowing incremental construction through decorators or manual building. Methods like `command()`, `mount()`, `converter()`, and `validator()` support fluent APIs for configuration.

**RuntimeCommand** is the immutable runtime representation created from `Command` via `to_runtime_command()`. It is a `@dataclass(slots=True, frozen=True)`, making it thread-safe and usable as a dictionary key. RuntimeCommand includes only execution concerns—special parameters are stored separately, converters and validators are registries, and the parser class and configuration are included for parser creation. It stores all parameters in a single `parameters` mapping and provides computed `options` and `positionals` properties that filter this mapping by kind.

**CommandSpec** is the parser specification created from `RuntimeCommand` via `to_command_spec()`. It is a `@dataclass(slots=True, frozen=True)` with aggressive caching of name lookups. CommandSpec contains only what the parser needs, stripping converters, validators, and metadata. Option and subcommand name mappings are cached for constant-time resolution.

### Parameter types

**CommandParameter** is the mutable parameter builder during registration, storing all parameter attributes with lists and plain tuples. It's `@dataclass(slots=True)` and mutable.

**RuntimeParameter** is the immutable runtime parameter from `CommandParameter.to_runtime_parameter()`. It's `@dataclass(slots=True, frozen=True)` with tuples and frozensets replacing mutable collections.

**OptionSpec** and **PositionalSpec** are parser specifications from `RuntimeParameter.to_option_spec()` and `to_positional_spec()`. Both are frozen with extensive validation and optimized for parser lookups.

### Result types

**ParseResult** is the parse tree from argument parsing. It is a `@dataclass(slots=True, frozen=True)` with the command name and alias, options and positionals as dictionaries, extra arguments after `--`, and a nested subcommand result forming a recursive tree structure. ParseResult values are primarily strings—conversion happens separately.

**ParsedOption** wraps an option value with the name and alias used, preserving which variant triggered the option.

**ParsedPositional** wraps a positional value with just the name since positionals have no aliases.

### Context type

**Context** is the execution context passed to command functions when requested. It is a `@dataclass(slots=True, frozen=True)` containing the command, command path, parse result, converted parameters, validation errors, parameter sources, parent context for subcommands, async flag, console and logger instances, and special parameter names.

## Integration points

The architecture's phases connect through well-defined integration points where data transforms between representations.

### Registration to runtime

`Command.to_runtime_command()` converts the mutable builder into an immutable runtime command. Parameters convert via `CommandParameter.to_runtime_parameter()`, subcommands convert recursively, mutable collections become tuples and mapping proxies, and async detection runs if not already determined. This produces a structure optimized for execution and thread safety.

### Runtime to parser

`RuntimeCommand.to_command_spec()` converts runtime commands into parser specifications. Parameters convert via `to_option_spec()` and `to_positional_spec()`, subcommands convert recursively, the result is cached for reuse, and everything the parser doesn't need is stripped away. This produces a structure optimized for parsing with minimal memory overhead.

### Parser to execution

`RuntimeCommand._convert_parameters()` bridges parsed strings to Python types. It extracts raw values from the parse result, applies default values for missing parameters, converts each value using converters with custom converters taking precedence over registry converters, and collects conversion errors without raising immediately.

### Context to function invocation

`RuntimeCommand._make_run_parameters()` builds the keyword arguments for the command function. CLI parameters come from `context.parameters`, special parameters are injected by name (context, console, logger), and the result is unpacked with `**` when calling the function. This keeps command functions decoupled from framework internals while providing everything they need.

## Example walk-through

Consider this complete example showing the end-to-end flow:

```python
from typing import Annotated
from aclaf import app, Context
from aclaf.metadata import Arg, Default

@app(name="deploy-tool")
def main(verbose: Annotated[bool, "--verbose", "-v"] = False) -> None:
    pass

@main.command()
def deploy(
    env: Annotated[str, Arg()],
    region: Annotated[str, "--region", Default("us-west-2")],
    context: Context,
) -> None:
    print(f"Deploying to {env} in {region}")
```

Invoked with: `deploy-tool deploy production --region us-east-1`

### Registration phase

At import time, the `@app()` decorator creates an `App` instance. It extracts `verbose` from `main()`'s signature, identifies it as an option with `is_flag=True` from the boolean type and `--verbose` metadata, stores `run_func=main`, and captures the function as the root command.

The `@main.command()` decorator creates a `Command("deploy")`. It extracts three parameters from `deploy()`'s signature. The `env` parameter has `Arg()` metadata making it explicitly positional. The `region` parameter has `"--region"` metadata making it an option with default `"us-west-2"`. The `context` parameter has type `Context`, marking it as a special parameter for injection. The decorator registers `deploy` as a subcommand of `main` and sets parent relationships.

### Specification conversion

On first invocation, `main()` calls `to_runtime_command()`. The `App` converts to `RuntimeCommand` with `parameters={"verbose": RuntimeParameter(...)}`, excluding the special context parameter. Subcommands convert recursively, so `deploy` becomes a `RuntimeCommand` with `parameters={"env": RuntimeParameter(...), "region": RuntimeParameter(...)}`.

Then `invoke()` calls `to_command_spec()`. The root spec includes `options={"verbose": OptionSpec(...)}` and `subcommands={"deploy": CommandSpec(...)}`. The deploy subcommand spec includes `options={"region": OptionSpec(...)}` and `positionals={"env": PositionalSpec(...)}`. These specs are cached for reuse.

### Parsing phase

The parser receives `["deploy", "production", "--region", "us-east-1"]`. At position 0, `"deploy"` resolves as a subcommand. The parser recursively parses `["production", "--region", "us-east-1"]` with the deploy subcommand's spec.

In the subcommand parse, `"production"` is not an option or subcommand, so it's collected as a positional. The `"--region"` at position 1 resolves as an option, consuming the next argument `"us-east-1"` as its value.

Positional grouping assigns `{"env": "production"}`. The parse result is:

```python
ParseResult(
    command="main",
    subcommand=ParseResult(
        command="deploy",
        options={"region": ParsedOption(name="region", value="us-east-1")},
        positionals={"env": ParsedPositional(name="env", value="production")},
    )
)
```

### Conversion and validation

The main command has no parameters to convert—`verbose` wasn't provided, so it uses its default `False`.

The deploy subcommand converts `"production"` (str) → `"production"` (str) for `env`, and `"us-east-1"` (str) → `"us-east-1"` (str) for `region`. Both target types are `str`, so conversion is trivial. The result is `{"env": "production", "region": "us-east-1"}`.

Validation checks that `env` is required and present (no error), and `region` is not required (no error). No metadata validators exist, so validation passes with `errors={}`.

### Execution

Context creation produces a main context with `command="main"`, `command_path=("main",)`, and `parameters={"verbose": False}`.

Dispatch executes `main()` with `verbose=False` from the default. Then it prepares subcommand dispatch by creating a subcommand context with `parent=main_context`, `command="deploy"`, `command_path=("main", "deploy")`, and `parameters={"env": "production", "region": "us-east-1"}`.

Function parameter binding for `deploy()` creates keyword arguments: `env="production"` from CLI, `region="us-east-1"` from CLI, and `context=<subcommand_context>` injected. The function executes with `run_func(**params)`, printing `"Deploying to production in us-east-1"`.

## Conclusion

Aclaf's architecture demonstrates careful separation of concerns across its five phases. Registration focuses on developer ergonomics through decorators and metadata. Specification conversion optimizes for execution and parsing through immutable representations. Parsing handles the complexity of CLI argument syntax. Conversion and validation bridge strings to domain types with extensible registries. Execution orchestrates invocation with dependency injection and context propagation.

Each phase operates on data structures optimized for its purpose, with well-defined integration points transforming data between phases. This design produces a framework that's simultaneously ergonomic for developers and correct in its behavior, with strong type safety and immutability guarantees throughout.

Understanding this architecture helps when building applications with Aclaf, debugging unexpected behavior, extending the framework with custom converters or validators, or contributing to the framework. The clean separation of concerns means each component can be understood and tested independently while composing into a cohesive system.
