# Vision

!!! Note ""
    This document describes the vision and principles guiding the framework's development. If you're a Python developer building command-line tools and frustrated with existing solutions, this explains what Aclaf aims to become and why I'm building it this way. The framework is nascent and actively evolving. This vision represents current thinking but will change as I learn from implementation and feedback. If something here resonates or raises questions, I'd welcome hearing about it.

Aclaf is a new command-line framework that brings modern Python practices to CLI development. I'm building the tool I've wanted for years: something that's fast, type-safe, and gets out of your way while helping you build polished, accessible command-line applications.

## Why I'm building this

I've spent years writing command-line tools in Python and other languages, hitting the same problems repeatedly. Good user experience means writing lots of boilerplate and stringing libraries together. Too often, tools work only if you can see the screen, use a mouse, or run on specific platforms.

Modern Python has evolved and brings sophisticated typing, powerful testing tools, and better abstractions. I want to explore what's possible starting fresh with modern Python and a clear vision.

I've learned that security and accessibility need to be design principles from the start, not features you add later, and that's what this framework reflects. I'm building this for developers who value both the developer and end-user experience, maintainability, and modern Python practices, whether they're making simple utilities or complex multi-command applications.

## Core principles

### Developer experience

Building command-line tools should feel productive. The framework aims to reduce friction and provide fast feedback so developers can focus on application logic rather than framework mechanics. Type-annotated functions become commands without extensive decoration, and things work the way their names and type signatures suggest they should.

Type annotations catch errors during development, drive automatic argument conversion, and enable IDE autocompletion that makes the development experience faster and more confident. Simple cases stay simple while complexity appears only when needed, with sensible defaults making basic commands trivial and advanced capabilities remaining accessible but optional.

CLI applications are often difficult to test because global state, terminal I/O, subprocess execution, and signal handling create friction. The framework treats testability as a core design concern rather than an afterthought. Commands are functions that tests can invoke directly, tests can capture and inspect terminal state, and interfaces abstract external dependencies so tests can mock them. The goal is making CLI application testing feel as natural as testing web applications, with the framework providing infrastructure so tests can focus on verifying behavior.

Cross-platform support presents another common friction point. CLI tools run everywhere including developer laptops, CI servers, production VMs, and personal computers across Windows, macOS, Linux, and BSD. Elegant command implementations shouldn't become littered with platform checks, each one creating cognitive overhead and potential bugs when behavior differs subtly between branches. Most platform differences aren't fundamental to what an application does but merely accidents of how different systems express the same concepts. The framework aims to make these differences disappear where they're not meaningful, expressing them as capabilities rather than platform identities when they do matter. Applications can ask "does this terminal support color?" instead of "am I on Windows?," and abstractions handle platform translation invisibly while application logic stays clean and portable.

### Modern CLI user experience

Command-line tools have evolved far beyond plain text output. Users expect beautiful formatting, colors, progress indicators, tables, and interactive prompts. Modern CLI tools also need to integrate with automation and other tools through structured, machine-readable output formats. A well-designed framework should be able to deliver all of this together.

The framework aims to make it easy to build CLIs that are both beautiful and functional. Rich visual elements like styled text, formatted tables, and progress bars enhance the interactive experience when humans are watching. Structured output formats like JSON, YAML, or custom formats enable integration with scripts, pipelines, and other tools. These capabilities can coexist naturally: a command shows a formatted table to interactive users but emits JSON when the user redirects output or specifies a flag.

The goal for accessibility is for it to be a first-class feature and not an afterthought in the framework. CLIs have a [unique set of accessibility considerations](https://dl.acm.org/doi/pdf/10.1145/3411764.3445544). Screen reader users hear garbled output when colors and ANSI codes convey critical information without textual alternatives. Users who can't distinguish colors miss important status indicators. Keyboard navigation is often missing or inconsistent. These problems stem from treating accessibility as optional rather than fundamental, and they become expensive to retrofit after building around visual assumptions.

Aclaf's approach is to separate visual presentation from semantic meaning. The framework should have a paved road of accessible defaults where color enhances rather than replaces textual information, so red doesn't mean "error" without the word "error" also appearing. Interactive elements work with keyboard navigation and provide appropriate feedback for screen readers. Progress indicators communicate progress textually, not just visually. When these principles guide the framework's out-of-the-box experience, accessible output is natural rather than extra work, and everyone benefits from clear, well-structured information whether they see it or hear it.

The framework should provide rich components out of the box including formatted tables, progress bars, interactive prompts, and styled output, with accessibility built into each component rather than requiring developers to implement it separately. Beautiful defaults that degrade gracefully when advanced terminal features aren't available, with automatic detection of capabilities and appropriate fallbacks.

### Streamlined distribution

Python's distribution story has a complicated history, and solving challenges like multi-platform distribution and supply chain security comprehensively would be a massive undertaking. The modern ecosystem has mature tools and frameworks that exist that the framework can build on and integrate like [PyInstaller](https://pyinstaller.org/) to create standalone executables, and [pipx](https://pipx.pypa.io/)  and [uv](https://docs.astral.sh/uv/guides/tools/) to provide isolated, user-friendly installation of Python applications. [The Update Framework (TUF)](https://theupdateframework.com/) offers a framework for securing software update systems. Aclaf can provide integration points for these existing solutions rather than reinventing everything.

Over time, I want to explore deeper integrations like generating [Homebrew formulas](https://docs.brew.sh/Python-for-Formula-Authors#applications) automatically from project metadata and providing TUF-based update checking for self-updates. This is a longer-term aspiration that will evolve based on what proves practical and valuable. The goal is to make it easier to leverage existing tools effectively so good CLI applications reach their users without excessive friction.

### Security by default

Security vulnerabilities in CLI tools follow predictable patterns: developers parse user input, forget to validate it, and pass it to something dangerous like a shell command or path. Security checklists help only when humans remember to check them. The goal is an architecture that makes insecure code harder to write than secure code and uses typing to catch security mistakes the same way it catches passing a string to a function expecting an integer.

This is an ambitious goal that requires sophisticated architectural solutions. I'm currently exploring mechanisms like type-based trust boundaries where user input carries markers that prevent it from reaching dangerous operations without explicit validation, shell-free command execution that eliminates injection vulnerabilities by default, and secure path types that prevent traversal attacks through construction rather than runtime checks.

The goal is for framework to guide developers toward secure patterns by making them the easiest path forward. This isn't about eliminating all security concerns, but about reducing common vulnerability classes through architectural choices while making remaining security decisions explicit and visible in code. Achieving this vision will require sustained effort and evolution, but I'm confident that these approaches can work in practice.

## Design tradeoffs

Aclaf makes deliberate tradeoffs that shape what the framework will and won't be.

The framework targets Python 3.10 and later, providing broad compatibility across all actively supported Python versions while retiring support as versions reach end-of-life. This approach balances wide compatibility with modern capabilities,  with `typing-extensions` used to leverage typing features from newer Python versions.

Aclaf maintains minimal dependencies. The framework avoids heavy libraries like rich to keep installations lean and startup fast. This means implementing more capabilities directly, which requires more framework code and development effort but gives finer control over behavior and performance characteristics. Applications needing the extensive feature sets of rich or similar libraries might find other frameworks more convenient, though Aclaf's architecture won't prevent using such libraries alongside it when their benefits outweigh startup cost concerns.

Type safety is a core value. The framework pushes toward patterns where types catch errors at development time rather than runtime. This sometimes requires more explicit code than dynamic approaches would allow. Operations that might be convenient but type-unsafe will require more steps or type assertions to express intent. Developers preferring maximally dynamic APIs may find this philosophy constraining, though the benefits of catching errors before code runs tend to outweigh the slight verbosity for many use cases.

Security-first design means some operations require more ceremony than in frameworks where security is optional. Executing shell commands, handling file paths from user input, or accepting user-provided code will require explicit acknowledgment of trust boundaries. This trades some convenience for safer defaults. Applications that need maximum flexibility in these areas can still achieve it, but the framework makes the safer patterns easier and the dangerous ones visible.

## Position in the ecosystem

Aclaf builds on lessons from the entire CLI framework landscape while making different choices.

[Cyclopts](https://cyclopts.readthedocs.io/en/stable/) and [Typer](https://typer.tiangolo.com/) are probably Aclaf's closest relatives. All three embrace type-driven CLI development with sophisticated type system integration. Aclaf maintains minimal dependencies where Typer builds on top of Click. It also treats accessibility and security as core architectural, developer experience, and end-user experience concerns rather than features to add later, incorporating them into foundational abstractions like semantic content separation. The distribution integration approach is also distinct, focusing on making existing tools like Homebrew and PyInstaller easier to integrate rather than building alternatives.

Compared to [argparse](https://docs.python.org/3/library/argparse.html) and [Click](https://click.palletsprojects.com/), Aclaf reduces ceremony through type-driven automation and higher-level abstractions. argparse focuses on parser construction mechanics and Click drives parameter definition through decorators, while Aclaf follows a typing-first approach where function signatures and docstrings define command interfaces. This enables more concise command definitions for typical cases while still providing explicit control when needed.

I've also drawn a lot of inspiration from frameworks beyond Python like [Cobra](https://cobra.dev/) and [clap](https://docs.rs/clap/latest/clap/), particularly around command structure, help generation, and shell completion patterns.

## Long-term vision

I want Aclaf to become a mature, stable framework that makes building command-line tools feel natural and productive. The goal is well-chosen abstractions that make common tasks straightforward while keeping uncommon tasks achievable, where framework opinions empower work rather than constrain it.

This is a CLI framework focused on command-line applications, not full-screen terminal UIs (use Textual for that) or interactive shell environments like REPLs (use prompt-toolkit for those). The sweet spot is tools invoked as commands that parse arguments, do work, and exit, whether that's a simple utility with a single command or a complex application with nested subcommands and rich output. I'm building the tool I want to use for my own CLI projects, and I think other Python developers building command-line tools might want it too.

---

*Last updated: 2025-11-13*
