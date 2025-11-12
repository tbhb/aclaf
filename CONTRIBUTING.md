# Contributing to Aclaf

Thank you for your interest in Aclaf! I'm excited that you're considering contributing to this command line application framework for Python.

## Project status

**Important**: Aclaf is currently in pre-1.0 development and is maintained by a single developer. The project is **not yet accepting pull requests** at this time.

However, your contributions through **issues** and **discussions** are highly valued and welcome. These help shape the project's direction and identify areas for improvement before the initial release.

## How you can contribute right now

### Report bugs and issues

If you encounter a bug, unexpected behavior, or have identified a potential problem, please open an issue on GitHub. This is one of the most valuable contributions you can make during the pre-release phase.

**What makes a great bug report:**

- Clear, descriptive title summarizing the issue
- **Minimum reproducible example**: A minimal, complete code sample that demonstrates the issue (see below)
- Steps to reproduce the problem with the minimal example
- Expected behavior versus actual behavior
- Environment details (Python version, operating system, Aclaf version/commit)
- Stack traces or error messages (if applicable)

**Creating a minimum reproducible example:**

A minimum reproducible example (MRE) is crucial for quickly identifying and fixing bugs. A good MRE:

- Is **minimal**: Contains only the code necessary to reproduce the issue (remove unrelated features, options, or logic)
- Is **complete**: Includes all imports, setup, and code needed to run the example without modifications
- Is **reproducible**: Consistently demonstrates the problem when run

Example of a good MRE:

```python
from aclaf import App

@app
def greeter(name: str):
    print(f"Hello, {name}!")

greeter()
```

This is much more helpful than describing the issue without code or providing a large, complex application where the problem is hard to isolate.

**Example issue structure:**

```markdown
## Description
Brief summary of the bug

## Minimum reproducible example
[paste your minimal, complete code example here]

## Steps to reproduce
1. Install Aclaf from commit abc123
2. Save the above code as `example.py`
3. Run: `python example.py --verbose`
4. Observe unexpected behavior

## Expected behavior
The command should print "Verbose: True" when run with --verbose flag

## Actual behavior
The command prints "Verbose: False" even with --verbose flag

## Environment
- Python version: 3.12.5
- Operating system: Ubuntu 24.04
- Aclaf commit: abc123def456
```

### Start discussions

GitHub Discussions is the place for questions, ideas, and conversations about Aclaf. We welcome discussions on topics like:

- **Questions**: How something works, clarification on design decisions, usage questions
- **Ideas**: Suggestions for features, API improvements, or architectural changes
- **Design feedback**: Thoughts on the project's direction, philosophy, or implementation approach
- **Use cases**: Sharing what you're building or planning to build with Aclaf
- **General feedback**: Impressions, pain points, or observations about the framework

Discussions help identify what's working well and what needs improvement before the initial release.

### Security vulnerabilities

If you discover a security vulnerability, please report it privately rather than opening a public issue. See the [security policy](SECURITY.md) for detailed reporting instructions.

**Quick summary:**

- Use [GitHub's private vulnerability reporting](https://github.com/aclaf/aclaf/security/advisories/new), or
- Email: <security@aclaf.sh>

Security reports should include a description of the vulnerability, reproduction steps, and potential impact.

## Why no pull requests yet?

During pre-1.0 development, the project is in active flux as core architecture, APIs, and design patterns are being established. I need the freedom to make rapid, breaking changes without coordination overhead or concerns about backwards compatibility.

Accepting pull requests at this stage would create expectations around API stability and migration paths that would slow down development and prevent the project from reaching its quality goals.

## When will pull requests be accepted?

Pull requests will be welcomed once the project reaches a more stable state, likely around or after the initial 1.0 release. At that point:

- Core APIs will be more stable
- Contribution guidelines will be expanded with development setup, coding standards, and review processes
- A clearer roadmap will help guide contribution efforts
- The project will be ready to onboard contributors effectively

You can follow the project's progress by watching the repository or checking release announcements.

## Project values and philosophy

Understanding Aclaf's values helps frame useful discussions and issue reports:

### Modern Python practices

Aclaf embraces Python 3.12+ features and modern development practices:

- Comprehensive type hints checked during development with basedpyright and in CI with Mypy and Pyright
- Dataclasses with slots for efficient, immutable value objects
- Pattern matching (match/case statements) for clear control flow
- Property-based testing with Hypothesis to discover edge cases
- Greater than 95% test coverage requirement for all code

### Minimal dependencies

The project maintains an extremely minimal dependency footprint:

- **Single runtime dependency**: Currently only `typing-extensions` for modern typing features
- **Standard library first**: Functionality is implemented with Python's standard library whenever possible
- **Justified dependencies**: Every dependency must have strong justification

This philosophy reduces supply chain risk, simplifies installation, and keeps the framework lightweight.

### Quality over speed

Quality and correctness are prioritized over shipping quickly:

- All code passes strict linting (Ruff and other tools)
- Zero type errors (basedpyright in strict mode)
- Comprehensive test coverage (unit tests, property-based, integration, and performance tests)
- Security considerations built in from the start
- Documentation written alongside code

### Breaking changes are free (for now)

Since the project is unreleased, breaking changes are encouraged when they improve the design, API, or implementation quality. Migration paths and backwards compatibility are not concerns during pre-1.0 development.

If you're experimenting with Aclaf before 1.0, expect that things will change. Once 1.0 is released, stability and versioning policies will be established.

## Future contribution model

When pull requests are accepted, the contribution process will follow these general guidelines:

### Development workflow

- All changes will go through pull requests (no direct commits to main)
- CI checks must pass (linting, type checking, tests across Python versions and operating systems)
- Code must follow the project's style guidelines
- All public APIs must have comprehensive documentation
- Test coverage must remain above 95%
- Commit messages must follow conventional commits format

### Code quality expectations

- **Type safety**: Comprehensive type hints for all code
- **Testing**: Property-based tests with Hypothesis plus example-based unit tests and integration tests
- **Documentation**: Google-style docstrings for public APIs
- **Security**: Consider security implications and test for common vulnerabilities
- **Standard library preference**: Avoid adding dependencies when stdlib can solve the problem

### Review process

- All changes will be reviewed before merging
- Feedback will focus on design, correctness, test coverage, and alignment with project values
- Multiple rounds of review may be necessary for complex changes

## Getting familiar with the project

While pull requests aren't accepted yet, you can prepare for future contributions by:

1. **Exploring the codebase**: Clone the repository and browse the source code in `src/aclaf/`
2. **Reading the documentation**: Check out the docs at [https://aclaf.sh](https://aclaf.sh)
3. **Running the tests**: Install dependencies with `just install` and run `just test`
4. **Experimenting**: Build small CLI applications using Aclaf to understand the framework
5. **Following development**: Watch the repository for updates and read commit messages

## Development setup (for exploration)

If you want to explore the codebase and run tests locally:

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [just](https://github.com/casey/just) (command runner)
- [pnpm](https://pnpm.io/) (Node.js package manager, for documentation tools)

### Installation

```bash
# Clone the repository
git clone https://github.com/aclaf/aclaf.git
cd aclaf

# Install all dependencies
just install
```

### Running tests

```bash
# Run all tests
just test
```

### Running linters

```bash
# Run all linters
just lint
```

### Building documentation

```bash
# Build documentation site
just build-docs

# Serve documentation with live reload
just dev-docs
```

## Questions?

If you have questions about contributing, the project's direction, or anything else:

- **GitHub Discussions**: For general questions and conversations
- **Issues**: For bug reports and specific problems
- **Security email**: For security-related questions (see [SECURITY.md](SECURITY.md))

## Code of conduct

While the project doesn't have a formal code of conduct yet, I expect all interactions to be respectful, constructive, and professional. Harassment, discrimination, or abusive behavior will not be tolerated.

## Thank you

Your interest in Aclaf is appreciated. Even though pull requests aren't accepted yet, your feedback through issues and discussions helps make the project better. I look forward to welcoming code contributions in the future once the project reaches a more stable state.

---

*This document will be updated as the project's contribution model evolves. Check back for updates as Aclaf approaches the 1.0 release.*

*Last updated: 2025-11-11*
