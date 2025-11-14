# Roadmap

!!! Note ""
    This roadmap provides transparency into Aclaf's development priorities and progress. If you're evaluating the framework or considering contributing, this shows what I'm building, what's complete, and where I'm focusing effort. The roadmap is a living document that evolves as the project matures. Nothing here represents a commitment or timeline—priorities shift based on implementation discoveries, real-world usage patterns, and architectural insights. This is about making development visible, not making promises.

I'm building Aclaf as a modern Python CLI framework that prioritizes developer experience, end-user experience, and accessibility. The roadmap communicates current development priorities and provides visibility into where the project heads. Rather than promising concrete dates or feature ordering, this roadmap makes the work transparent so you can track progress and understand the project's direction.

Since Aclaf is still in early development, I expect and encourage breaking changes when they improve design, API quality, or implementation correctness. Nothing in this roadmap represents a commitment or promise. Development priorities shift based on real-world usage, technical discoveries, and architectural insights as understanding of the problem space deepens.

I'm building Aclaf's core capabilities as a vertically integrated CLI framework, which means controlling the entire stack from argument parsing to terminal output to interactive prompts. This vertical integration enables rethinking all aspects of the developer experience for CLI authors and the user experience for CLI end-users. By designing every core feature to work together cohesively, the framework delivers a comprehensive solution where the parser understands command structure, type conversion integrates with validation, and console output coordinates with error reporting. This integration enables features and optimizations that wouldn't be possible when assembling disparate libraries: shared configuration propagates seamlessly, error messages reference the full context from parsing through execution, and terminal capabilities influence behavior across all components. The result is a framework where everything fits together naturally rather than requiring CLI authors to orchestrate multiple independent tools.

For more details on Aclaf's design principles and philosophy, see the [vision](vision.md).

## Foundation

This section describes the capabilities that form Aclaf's minimal viable CLI framework. These are the essential features needed to build functional command-line applications: parsing arguments, routing to commands, converting types, displaying output, handling errors, and testing. Together, these capabilities enable developers to create real CLI tools while maintaining the framework's commitments to type safety, accessibility, and developer experience.

Developer experience, end-user experience, and accessibility serve as first-class architectural constraints that shape how I design and build foundational capabilities. For developers, the framework reduces friction through type-driven behavior, testable architectures, and cross-platform abstractions. For end users, foundation capabilities enable clear output, structured errors, and terminal capability detection that adapts gracefully. For accessibility, these features separate semantic meaning from visual presentation, ensure screen reader compatibility, and structure all information hierarchically. These concerns influence every architectural decision: error context flows from parsing through reporting with semantic structure, type conversion provides clear failure messages, console output works without color dependency, and testing utilities validate accessible behavior. These capabilities establish the architectural patterns and infrastructure that more sophisticated features in Next up build upon, ensuring that advanced feature inherits the same commitment to developer experience, user experience, and accessibility from the start.

Capabilities in this section have either reached completion and stability, or represent critical work in progress that I must finish before I can consider the framework feature-complete for an initial release. As each capability stabilizes, it becomes the bedrock on which I'll build other framework features. Releases while foundation work continues will use 0.x versioning, with the completion of foundational capabilities marking readiness for production use. The 1.0 release will come once I complete the enhancements described in Next up, representing a comprehensive, mature CLI framework.

### Parser

The parser is Aclaf's argument parsing engine, responsible for transforming raw command-line argument strings into structured data representations. It handles the syntactic analysis of command-line arguments without performing semantic interpretation, validation, or type conversion.

Built from first principles rather than wrapping existing libraries like argparse, this feature-complete implementation serves as the foundation for all other framework features. This approach manifests in comprehensive type safety using modern Python features, immutability for thread safety and predictability, property-based testing for discovering edge cases, and minimal dependencies through extensive standard library usage.

Structured parse results emerge as pure data without awareness of type conversion, validation, default values, or application semantics. This clear separation of concerns enables thorough independent testing of the parsing logic in isolation and makes the architecture easier to understand and maintain.

#### Key goals

- [x] **Long option support**—Parse GNU-style long options with both `--option value` and `--option=value` syntax forms including abbreviation matching
- [x] **Short option handling**—Process POSIX-style short options with `-o value` syntax and `-abc` clustering for flag combinations
- [x] **Positional argument parsing**—Handle positional arguments with flexible ordering and clear separation from options
- [x] **Option termination delimiter**—Support `--` separator to distinguish options from positional values that might look like options
- [x] **Parsing mode flexibility**—Enable both POSIX-strict ordering and GNU-style options-anywhere approaches with 15+ configuration flags for case sensitivity, abbreviation matching, underscore-to-dash conversion, and behavioral customization
- [x] **Option and subcommand aliases**—Support multiple names for options and subcommands with configurable alias resolution
- [x] **Negative number parsing**—Disambiguate negative numeric values from short options with configurable pattern matching
- [x] **Comprehensive arity control**—Specify precise value counts from zero to many with validation for options and positionals
- [x] **Accumulation strategies**—Handle repeated options through configurable modes including last-wins, first-wins, collect-all, count, and error-on-duplicate
- [x] **Flag negation**—Support negation prefixes for boolean flags enabling patterns like `--no-verbose`
- [x] **Subcommand nesting**—Support arbitrary command hierarchy depth with independent option and positional contexts at each level
- [x] **Detailed exception hierarchy**—Distinguish parsing failures through structured exception types for unknown options, missing values, invalid arity, ambiguous abbreviations, and other specific error conditions
- [x] **Type-agnostic output**—Produce pure structured data without semantic interpretation enabling flexible downstream processing
- [x] **Performance optimization**—Achieve efficient parsing through single-pass algorithm, cached resolution, and immutable structures

### Commands and routing

The framework's command system maps parsed arguments to executable Python functions, handling the routing from user input to application logic. It must be able to support both simple single-command tools and complex hierarchical command trees like Git or Docker.

The command system bridges the gap between the parser's structured output and application code. It handles command registration through decorators, maintains command hierarchies for subcommand support, manages command lifecycle and invocation, and provides infrastructure for help generation. The core command system includes basic dependency injection for framework-provided services through signature-based parameter recognition, enabling commands to declare dependencies like `context: Context` and `console: Console` and receive injected instances automatically.

#### Key goals

- [ ] **Decorator-based registration**—Enable intuitive command definition through function decorators with minimal boilerplate
- [ ] **Signature-based parameter mapping**—Extract CLI arguments directly from function signatures using type hints, parameter types (positional-only, keyword-only, variadic), and Annotated metadata for rich parameter definitions
- [ ] **Structured parameter groups**—Support Dataclasses and TypedDict for grouping related parameters, with Unpack for kwargs-style parameter expansion, enabling parameter reuse across commands and reducing duplication in multi-command applications
- [ ] **Hierarchical command trees**—Support arbitrary command nesting with independent parameter contexts at each level
- [ ] **Mounting commands from other modules**—Enable importing and integrating commands defined in other modules into the application's command tree
- [ ] **Lazy command loading**—Defer command import and initialization until invoked, reducing startup time for large command trees with many subcommands
- [ ] **Application invocation and routing**—Orchestrate the complete execution flow from raw argv through parsing, command matching, type conversion, validation, dependency injection, and command invocation with proper error handling at each stage
- [ ] **Lifecycle management**—Handle command initialization, execution, and cleanup with proper error propagation
- [ ] **Basic help generation**—Automatically extract help text from docstrings and type hints for in-terminal help displays
- [ ] **Automatic version support**—Provide automatic `--version` flag and optional version subcommand with configurable display formats, integration with package metadata (pyproject.toml, `__version__` attributes), and customizable output ranging from simple version strings to detailed build information
- [ ] **Framework service injection**—Automatically inject framework-provided dependencies like `Context` and `Console` through type-annotated parameters without requiring explicit `Depends()` markers
- [ ] **Async command support**—Support both sync and async def command functions with proper event loop management
- [ ] **Accessible help output**—Generate help text with semantic structure, clear hierarchy, and logical reading order that works well with screen readers

### Type conversion and coercion

Type conversion transforms the parser's string values into Python objects based on type hints, turning raw parse results into strongly typed data ready for command logic. Command-line arguments arrive as strings but represent structured data: a parameter annotated as `count: int` receives an actual integer, `path: Path` receives a validated Path object, and `enabled: bool` handles common boolean representations automatically.

Drawing inspiration from Pydantic's [approach to type coercion](https://docs.pydantic.dev/latest/concepts/types/), this component uses Python type annotations as the single source of truth for automatic conversion. Type hints drive conversion with minimal boilerplate, enabling seamless transformation from CLI strings to rich Python objects. The conversion system focuses on transformation semantics: how strings become integers, how paths receive normalization, how the system matches enum values, and how custom types define their own coercion logic.

#### Key goals

- [ ] **Type-hint-driven conversion**—Automatically transform string arguments into typed Python objects based on function annotations
- [ ] **Comprehensive standard library support**—Handle built-in types, collections, unions, `Optional` types, dataclasses, and `TypedDict` natively
- [ ] **Default values and factories**—Support static default values for optional parameters and default factories for dynamic defaults, ensuring defaults undergo type conversion and preventing common pitfalls like mutable defaults
- [ ] **Custom converter extensibility**—Enable domain-specific type conversion for specialized types with consistent transformation behavior
- [ ] **Collection and union handling**—Support `List`, `Set`, `Dict`, and `Union` types with proper element-wise conversion and type narrowing
- [ ] **Clear conversion errors**—Report type conversion failures with semantic structure showing which parameter failed, which value the user provided, and which type the system expected
- [ ] **Path handling and normalization**—Convert path arguments to Path objects with automatic normalization, platform-appropriate separators, and traversal attack protection

### Basic validation

Basic validation ensures that converted values meet fundamental constraints and establishes the validation architecture that more advanced features build upon. This component handles required versus optional parameters, simple value constraints that appear frequently in CLI applications, and defines the validation error types and reporting structure that other components depend on.

The validation infrastructure provides the foundation for error reporting, establishes patterns for validation failures, and enables commands to express basic constraints. I'll defer more sophisticated declarative constraint systems and parameter relationship validation to the [advanced validation](#advanced-validation-and-constraints) capabilities.

#### Key goals

- [ ] **Required and optional handling**—Validate that the user provides required parameters and handle optional parameters with `None` values appropriately
- [ ] **Basic value constraints**—Support common simple constraints including numeric ranges, string length limits, choice/enum validation, and path existence checks
- [ ] **Validation error types**—Define structured exception types for validation failures that error handling can catch and format appropriately
- [ ] **Error context propagation**—Include parameter names, field paths, violated constraints, and provided values in validation errors
- [ ] **Integration with type conversion**—Coordinate validation with type conversion to provide clear errors when values fail either conversion or validation
- [ ] **Accessible validation structure**—Establish semantic structure for validation errors that screen readers can convey meaningfully

### Console output

The framework's console abstraction provides the output capabilities that CLI applications need to communicate with users. This foundational implementation focuses on essential output patterns: printing text, basic styling, and detecting terminal capabilities. Given the popularity and features in [Rich](https://rich.readthedocs.io), Aclaf will initially use it as the primary output engine alongside a basic console implementation. Commands need to display results, show status, and communicate effectively regardless of terminal environment.

This capability integrates accessibility from the start by separating semantic meaning from visual presentation. Output works equally well for visual and auditory presentation, functions without color dependency, and adapts to varying terminal capabilities. The console automatically detects what the terminal supports and adjusts accordingly.

#### Key goals

- [ ] **Basic text output**—Print styled text with color and formatting that degrades gracefully in limited terminals
- [ ] **Terminal capability detection**—Detect color support, Unicode rendering, screen reader presence, and interactive capabilities with appropriate fallbacks
- [ ] **Semantic output structure**—Separate visual presentation from semantic meaning so information remains clear without color or formatting
- [ ] **Async output support**—Support async operations for console output in async commands
- [ ] **Accessible by default**—Ensure all output works with screen readers through semantic structure, meaningful text without color dependency, and clear information hierarchy
- [ ] **NO_COLOR standard support**—Respect the `NO_COLOR` environment variable convention for disabling color output across all CLI tools
- [ ] **Graceful capability degradation**—Automatically fall back from advanced features to simpler alternatives when the terminal limits capabilities, such as 24-bit color to 256-color to 16-color to monochrome, or Unicode box-drawing to ASCII equivalents
- [ ] **Structured output modes**—Support JSON and YAML output formats for scripting and automation through command-line flags, enabling programmatic consumption of CLI results

### Error handling and reporting

Clear, actionable error messages distinguish professional CLI tools from frustrating ones. The error handling capability catches parsing errors, validation failures, and application exceptions, then formats them into messages that explain what went wrong and suggest corrections.

Error reporting respects terminal capabilities and maintains accessibility. Error messages guide users toward solutions with clear context rather than just documenting failures. This capability establishes the patterns that all framework errors follow, ensuring consistency across parsing, validation, command execution, and application logic.

#### Key goals

- [ ] **Contextual error messages**—Include full context from parsing through execution with specific parameter paths and positions
- [ ] **Actionable suggestions**—Recommend corrections based on common mistakes and available alternatives ("did you mean?")
- [ ] **Accessible error presentation**—Structure error messages with semantic hierarchy that screen readers can convey effectively, ensuring clarity without color or formatting dependencies
- [ ] **Error message standards**—Define consistent patterns for error organization including problem identification, context explanation, and suggested corrections
- [ ] **Crash handling**—Capture unhandled exceptions with diagnostic information including stack traces and environment state, writing sanitized crash reports while preserving user privacy

### Help generation and display

Help generation transforms command definitions into discoverable, accessible documentation that users can access directly from the terminal. Every CLI application needs clear help text explaining available commands, options, and usage patterns. This capability automatically generates comprehensive help from command structure, type hints, and docstrings, ensuring documentation stays synchronized with implementation.

Help sits at the intersection of multiple framework components. It depends on the command registration system to understand application structure, uses the console abstraction for formatted output, and follows the same accessibility patterns as error reporting. The help system must work across simple single-command tools and complex nested command hierarchies, adapting its output to context while maintaining consistency.

Accessibility shapes every aspect of help generation. Help text uses semantic structure that screen readers can navigate effectively, organizes information hierarchically with clear headings and sections, and remains comprehensible without color or formatting. The help system ensures users can discover capabilities regardless of how they interact with the terminal.

#### Key goals

- [ ] **Automatic help flag registration**—Provide `-h` and `--help` flags automatically for all commands without requiring explicit configuration
- [ ] **Docstring extraction**—Extract help text from command function docstrings with support for common documentation formats
- [ ] **Usage line generation**—Generate accurate usage syntax summaries showing command structure, required and optional parameters, and positional ordering
- [ ] **Parameter documentation**—Document each option and positional argument with descriptions extracted from docstrings, type information, default values, and constraints
- [ ] **Subcommand help hierarchy**—Display help for nested command structures with appropriate context at each level, showing available subcommands and their purposes
- [ ] **Section organization**—Structure help output into logical sections including synopsis, description, commands, options, and examples with clear visual hierarchy
- [ ] **Type-driven parameter display**—Show parameter types, choices, and constraints automatically based on type hints and validation rules
- [ ] **Usage examples**—Support inline examples in help text showing common usage patterns and option combinations
- [ ] **Help customization hooks**—Enable developers to override or extend generated help for specific commands or sections when automatic generation is insufficient
- [ ] **Accessible help structure**—Generate help with semantic markup, clear headings, logical reading order, and information hierarchy that works effectively with screen readers
- [ ] **Help text formatting**—Format help output with appropriate styling, alignment, and wrapping that adapts to terminal width and capability
- [ ] **Context-aware help**—Show relevant help based on where users invoke `--help` in command hierarchy, displaying only pertinent options and subcommands

### Testing utilities

First-class testing utilities provided by the framework help developers build reliable CLI applications. This foundational capability provides essential test helpers for command invocation, output capture, and basic mocking. Testing utilities make it straightforward to write thorough test suites without fighting the framework.

The testing infrastructure aligns with Aclaf's own testing approach and demonstrates patterns that CLI application developers can follow in their own test suites.

#### Key goals

- [ ] **Command invocation helpers**—Provide test fixtures for calling commands with captured output and controlled environments
- [ ] **Output capture utilities**—Enable assertions on `stdout`, `stderr`, and `console` formatting without complex mocking
- [ ] **Async test support**—Provide utilities for testing async commands and async operations

### Shell completion

Shell completion is a required feature for modern CLI frameworks, helping users discover available commands and options while reducing typing. This capability generates completion scripts for major shells that understand command hierarchies, option names, and parameter types.

The completion system integrates with the command registration and type system to automatically generate appropriate completions. Commands defined through decorators with type hints automatically gain completion support without extra developer effort.

#### Key goals

- [ ] **Multi-shell support**—Generate completion scripts for Bash, Zsh, Fish, and PowerShell with command hierarchy awareness
- [ ] **Command and option completion**—Complete command names, subcommands, long options, and short options based on registered commands
- [ ] **Type-aware value completion**—Provide appropriate completions for typed parameters including enums, choices, booleans, and file paths
- [ ] **Automatic generation**—Generate completion scripts from command definitions without requiring manual completion code
- [ ] **Installation helpers**—Provide utilities to install completion scripts in appropriate shell configuration locations

## Next up

This section organizes well-defined enhancements that build on the foundational framework. These features make Aclaf more powerful, polished, and comprehensive while remaining focused on concrete, implementable capabilities. Items here have clear goals and implementation approaches I understand, distinguishing them from the more exploratory work in the [Future](#future) section.

Where Aclaf's foundational capabilities establish the architectural patterns for developer experience, user experience, and accessibility, this section extends those patterns with capabilities that truly differentiate the framework.

### Advanced validation and constraints

Building on the basic validation infrastructure in foundation, this feature provides declarative constraint specification and parameter relationship validation. It enables complex business rules, cross-field dependencies, and declarative constraint patterns that reduce boilerplate in applications with complex validation requirements.

Drawing inspiration from Pydantic's [approach](https://docs.pydantic.dev/latest/concepts/fields/#field-constraints), this component enables metadata-driven constraint specification, custom validator functions, and parameter-level rules. Commands can express that parameters have complex interdependencies, that certain option combinations are mutually exclusive, or that validation logic requires examining more than one parameter together.

#### Key goals

- [ ] **Declarative constraint specification**—Define advanced validation rules through metadata, annotations, and parameter-level constraints with minimal boilerplate
- [ ] **Parameter relationship constraints**—Declare inter-parameter relationships including mutual exclusion, dependencies, and group constraints (exactly one of, at least one of) through declarative specification
- [ ] **Custom validator support**—Enable application-specific validation logic for complex business rules and cross-field dependencies
- [ ] **Parameter-level constraint composition**—Combine multiple constraints on single parameters with logical operators (all of, any of, none of)
- [ ] **Validation middleware**—Support validator chains and validation hooks that can change or transform values during validation
- [ ] **Rich contextual error messages**—Extend basic validation errors with more context including multiple constraint violations, suggested corrections, and relationships between parameters

### Rich console output

Rich terminal output creates polished, accessible command-line experiences beyond basic text printing. This feature extends the foundational console capabilities with formatted tables, progress indicators, box drawing, and sophisticated styling while maintaining accessibility.

This feature focuses on standard output patterns that CLI tools need: tabular data, progress feedback, visual hierarchy through borders and sections, and clear status communication. It will not attempt to be a full-screen TUI framework; that domain is well-served by tools like Textual.

#### Key goals

- [ ] **Formatted tables**—Render structured data as aligned tables with customizable borders, column alignment, and styling
- [ ] **Progress indicators**—Provide progress bars, spinners, and status updates for long-running operations
- [ ] **Box drawing and panels**—Unicode box-drawing characters for bordered sections, panels, and layout containers with ASCII fallback for limited terminals
- [ ] **Advanced styling**—Support sophisticated text styling with colors, emphasis, and visual hierarchy
- [ ] **Async progress support**—Handle progress updates in async operations
- [ ] **Universal accessibility**—Ensure all rich output works with screen readers through semantic markup, alternative text for visual elements, keyboard-only interaction where relevant, and graceful degradation

### Interactive prompts

Prompts enable interactive data collection when command-line arguments aren't enough. This feature provides specific interactive widgets that temporarily take over the terminal for input before returning to normal CLI flow. Each widget handles a common interaction pattern with appropriate keyboard controls and accessible feedback.

Prompts build in accessibility from the start and work well with diverse terminal environments and assistive technologies. Like other output features, they separate semantic meaning from visual presentation.

#### Key goals

- [ ] **Text input**—Single-line and multi-line text input with validation, default values, and placeholder text
- [ ] **Select**—Single selection from a list of options with keyboard navigation and filtering
- [ ] **Checkboxes**—Multi-select from a list of options with toggle controls and select-all/none shortcuts
- [ ] **Confirmation**—Yes/no prompts with customizable default values and clear display of choice
- [ ] **Search**—Fuzzy-searchable selection with real-time filtering and match highlighting
- [ ] **Password/secret**—Masked input for sensitive data with configurable masking characters and optional reveal
- [ ] **Editor launch**—Launch external editor (respecting $EDITOR) and capture returned content with validation
- [ ] **Type-safe input collection**—Integrate with type conversion system to validate interactive inputs with same rigor as arguments
- [ ] **Keyboard navigation**—Support intuitive keyboard controls and shortcuts for efficient interaction
- [ ] **Async prompt support**—Enable prompts in async command contexts
- [ ] **Universal accessibility**—Support screen readers with clear state announcements and context, enable keyboard-only navigation with discoverable shortcuts, provide alternative text for visual indicators, ensure clarity without visual styling, and handle diverse terminal capabilities

### Dependency injection

While the Commands component provides basic dependency injection for framework services through signature recognition, this component adds [FastAPI-inspired DI capabilities](https://fastapi.tiangolo.com/tutorial/dependencies/) for application-specific services. This enables testable, modular CLI applications where business logic services integrate cleanly with framework infrastructure.

This builds on the command system's foundation by adding explicit dependency declaration through `Depends()` markers, custom service registration and resolution, lifecycle management, and nested dependency graphs for complex applications.

#### Key goals

- [ ] **Explicit dependency markers**—Introduce `Depends()` for declaring injectable dependencies with custom factories, lifecycle scopes, and resolution behavior
- [ ] **Custom service registration**—Enable application-specific service registration in a DI container with type-based resolution
- [ ] **Advanced lifecycle control**—Manage dependency scopes including singleton (application lifetime), transient (per-invocation), and custom scopes with proper initialization and cleanup
- [ ] **Nested dependency resolution**—Support dependency graphs where services depend on other services with automatic recursive resolution
- [ ] **Testing and mocking integration**—Provide utilities for dependency replacement, mocking, and test isolation without modifying command code
- [ ] **Async dependency support**—Handle async factories, context managers, and initialization in dependency resolution

### Configuration management

CLI applications often need configuration from many sources: command-line arguments, environment variables, configuration files, and system defaults. This feature handles loading, merging, and precedence rules across these sources while maintaining type safety and validation.

This system supports common configuration file formats, provides clear precedence rules, and integrates seamlessly with type conversion and validation to ensure configuration values meet the same standards as command-line inputs.

#### Key goals

- [ ] **Multi-source loading**—Merge configuration from arguments, environment variables, files, and defaults with clear precedence
- [ ] **Format flexibility**—Support common configuration formats including TOML, JSON, YAML, and INI with minimal dependencies
- [ ] **Type-safe validation**—Apply same type conversion and validation to configuration as command-line arguments
- [ ] **Override transparency**—Make precedence rules explicit and provide visibility into which sources override others
- [ ] **Accessible configuration errors**—Report configuration issues with clear structure, full context, and actionable guidance

### Advanced testing utilities

Beyond the foundational testing utilities, this feature provides sophisticated testing capabilities including property-based testing, comprehensive fixtures, and specialized assertions. These tools help developers build thorough test suites that discover edge cases and maintain high confidence in CLI application behavior.

The advanced testing infrastructure aligns with Aclaf's own testing approach, demonstrating property-based testing patterns and sophisticated testing strategies.

#### Key goals

- [ ] **Comprehensive fixtures**—Provide sophisticated test fixtures for complex scenarios including multi-command applications, configuration variations, and error injection
- [ ] **Specialized assertions**—Enable detailed assertions on command output, error messages, and application state
- [ ] **Performance testing**—Include utilities for benchmarking and performance regression testing
- [ ] **Snapshot testing support**—Enable capturing and comparing terminal output snapshots with human-readable diff formats and normalization rules
- [ ] **Input simulation for interactive prompts**—Enable scripted keyboard input, form filling, and prompt responses for testing interactive commands, with timing controls, keyboard combinations, and scripted interaction sequences
- [ ] **Mock file system with advanced features**—Extend basic file system mocking with permission simulation, symbolic links, and platform-specific behaviors

### Accessibility infrastructure

This infrastructure provides comprehensive capabilities for framework-wide accessibility, building on the basic accessibility considerations integrated throughout foundation. While foundational features include essential accessibility support, this section delivers advanced tooling, validation, testing frameworks, and guidelines that ensure accessibility excellence.

The accessibility infrastructure establishes technical tools and APIs that framework features and CLI applications can leverage. Console output uses semantic markup APIs. Error reporting leverages structured message formats. Interactive prompts integrate keyboard navigation and screen reader support. Documentation generation produces hierarchically organized content. Testing utilities check accessible behavior automatically.

#### Key goals

- [ ] **Accessibility API primitives**—Provide core abstractions for accessible output including semantic markup for structure such as headings, lists, and emphasis, alternative text for visual elements, progressive disclosure patterns for complex information, and ARIA-compatible patterns for interactive elements
- [ ] **Screen reader testing infrastructure**—Enable automated validation of screen reader compatibility including output linearization testing, semantic structure verification, and assistive technology integration testing
- [ ] **Advanced capability detection**—Detect nuanced terminal capabilities beyond basic foundation support, enabling sophisticated adaptive behavior
- [ ] **Accessible output guidelines**—Document comprehensive patterns for creating accessible terminal output including semantic structure over visual styling, meaningful text without color dependency, keyboard-navigable interactions, and clear information hierarchy
- [ ] **Accessibility validation tooling**—Provide linters and validators that check for common accessibility issues including color-only information, missing alternative text, unclear structure, and inaccessible interactive patterns
- [ ] **Cross-component accessibility contracts**—Define interfaces that features must use to maintain accessibility including error context propagation, semantic message structure, alternative representations, and capability-aware rendering
- [ ] **Accessibility testing support**—Include test utilities for validating accessible output including screen reader simulation, semantic structure assertions, and capability degradation testing

## Future

This section outlines capabilities that matter for the framework's long-term vision but that I'll defer beyond the initial release. These features represent natural extensions of Aclaf's core capabilities that I'll explore once the foundational components stabilize and prove themselves in real-world applications.

Items here don't have detailed implementation plans or timelines. I include them to provide visibility into the project's direction and to show areas where the architecture leaves room for future growth. Priorities may shift based on community feedback, real-world usage patterns, and emerging needs in the CLI development ecosystem. Some capabilities may move from Future into Next up as I explore implementation approaches and deepen my understanding of requirements.

### Cross-platform abstractions

A comprehensive abstraction layer that eliminates platform-specific code from CLI applications. This includes unified signal and interrupt handling across Windows and Unix, automatic text encoding and line ending normalization, environment variable path list parsing (semicolon vs colon delimiters), and argument syntax normalization (accepting both `--option` and `/option` styles). The goal is making applications work identically across platforms without developers needing to check `platform.system()` or handle platform differences explicitly.

### Standalone documentation generation

Beyond the in-terminal help, future work will explore automatic generation of standalone documentation in multiple formats. This includes generating manpages, command references, usage guides, example galleries, and other documentation that CLI authors can publish to websites or distribute with packages.

Documentation generation would work with the type system, command structure, and validation rules to create thorough, accurate documentation that stays synchronized with code as it evolves. I'll determine the specific formats, generation approaches, and integration points based on real-world documentation needs.

### Plugin and extension system

Future work will explore infrastructure that enables CLI applications built with Aclaf to implement plugin systems allowing users to extend capabilities. This would provide discovery, loading, and lifecycle management capabilities that CLI developers could use to add secure, type-safe plugin support to their applications.

Plugin discovery through entry points and explicit module imports creates inherent security risks since plugins execute arbitrary code within the application's process and security context. Malicious or compromised plugins can access the same resources and privileges as the host application, exfiltrate sensitive data, change application behavior, or exploit vulnerabilities in the plugin loading mechanism itself. Aclaf will make it easy for CLI authors to implement mitigations like plugin signature verification and trust chains to ensure plugins come from verified sources, explicit permission models requiring plugins to declare needed capabilities with user approval, and safe loading mechanisms that validate plugin structure and dependencies before execution. The framework will provide clear guidance on secure plugin system architecture, help developers implement defense-in-depth strategies, and make secure plugin patterns easier to implement than insecure ones. Security will be a first-class architectural constraint in plugin system design, not an afterthought.

### Distribution and packaging tools and integrations

Infrastructure for distributing CLI applications to end users. This encompasses generating standalone executables for multiple platforms, integrating with platform package managers (Homebrew, apt, WinGet), creating installation scripts with automatic dependency handling, implementing self-update mechanisms with integrity verification, and managing the complete software lifecycle from installation through updates to removal. While the framework focuses on building applications, distribution tooling bridges the gap between working code and deployed tools that users can actually install and maintain.

### Security abstractions

Patterns and utilities for building secure CLI applications. This includes protection against path traversal attacks in file operations, safe subprocess execution that prevents command injection, secret management for credentials and API keys with secure storage and rotation, and audit logging for security-sensitive operations. The framework would provide guidance and helpers for common security concerns while leaving security-critical decisions in application code where they can be explicitly reviewed.
