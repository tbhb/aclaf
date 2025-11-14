# Security policy

## Project status

This project is currently in pre-release development (pre-1.0). A single developer maintains the project. While the project is not yet released to PyPI, I take security seriously during development to establish good practices from the start.

> [!Important]
> Pre-release software may contain undiscovered security vulnerabilities. I don't recommend using the project in production until version 1.0 releases. If you choose to use pre-release versions, do so with appropriate caution and security measures.

## Supported versions

As an unreleased project, there are no stable versions yet. I will apply security updates to the main development branch as I identify and resolve them.

Once the project reaches 1.0 and has stable releases, I will update this section with a clear support matrix indicating which versions receive security updates.

## Reporting a vulnerability

If you discover a security vulnerability in this project, please report it privately rather than opening a public issue. This allows time to assess the issue and prepare a fix before public disclosure.

### GitHub private vulnerability reporting

This repository has enabled GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) feature. You can report security vulnerabilities directly through GitHub:

1. Navigate to the repository's [Security tab](https://github.com/aclaf/aclaf/security)
2. Click ["Report a vulnerability"](https://github.com/aclaf/aclaf/security/advisories/new)
3. Fill out the security advisory form

This is the preferred method for security reports as it keeps the discussion private until a fix is ready.

### How to report

Send details to: **<security@aclaf.sh>**

If you don't receive an acknowledgment within 7 days, or if the email bounces, you can also:

- Open a [private security advisory](https://github.com/aclaf/aclaf/security/advisories/new) on GitHub
- Contact the maintainer directly through GitHub (only for security issues)

> **Note**: The maintainer monitors the `security@aclaf.sh` email address. Response times may vary based on availability.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce the issue, including any proof-of-concept code
- The version or commit hash where you identified the vulnerability
- Any suggested fixes or mitigations you've considered

**Example report structure:**

```text
Title: [Brief description of vulnerability]

Vulnerability Type: [e.g., Command injection, Path traversal]

Severity: [Your assessment: Critical/High/Medium/Low]

Description:
[Detailed explanation of the vulnerability]

Impact:
[What an attacker could achieve by exploiting this]

Reproduction Steps:
1. [Step by step instructions]
2. [Include code examples]
3. [Expected vs actual behavior]

Proof of Concept:
[Minimal code demonstrating the vulnerability]

Suggested Fix:
[If you have ideas for remediation]

Environment:
- Aclaf version/commit: [version or commit hash]
- Python version: [e.g., 3.14.0, 3.13.1, 3.12.5, 3.11.8, or 3.10.15]
- Operating system: [e.g., Ubuntu 24.04]
```

### Reporting language

Submit security reports in English to ensure clear communication and faster response times.

### What to expect

As a solo-maintained project, please understand the response timeline may vary based on the maintainer's availability:

- **Initial Response**: Within 7 days of your report, you'll receive acknowledgment that I received your report
- **Assessment**: Within 14 days, you'll receive an assessment of whether the issue qualifies as a security vulnerability and the planned response
- **Resolution Timeline**: Depending on severity and complexity, fixes may take anywhere from a few days to weeks
- **Coordinated Disclosure**: After a fix is available, I will make a coordinated disclosure through GitHub Security Advisories. Typically, disclosure occurs 7-14 days after I release the fix, allowing time for users to update. I will consult security researchers on disclosure timing. If I cannot develop a fix within 90 days, I will issue a public advisory with mitigation recommendations

### Severity guidelines

I rank vulnerabilities based on their potential impact:

- **Critical**: Remote code execution, authentication bypass, or exposure of sensitive credentials
- **High**: Privilege escalation, injection vulnerabilities, or significant data exposure
- **Medium**: Denial of service, information disclosure without sensitive data
- **Low**: Issues with limited impact or requiring significant user interaction

I give critical and high severity issues immediate attention.

## Security practices

This project follows these security practices during development:

- **Minimal dependencies**: The project maintains a minimal dependency footprint (currently only `typing-extensions` as a runtime dependency) to reduce supply chain risk
- **Dependency pinning**: The project pins all dependencies with cryptographic hashes in lock files (`uv.lock`)
- **Automated scanning**: Dependabot runs weekly to check for dependency vulnerabilities
- **Publishing**: Releases will use PyPI Trusted Publishing with automatic Sigstore attestations (once published)
- **Code Review**: All changes go through review before merging, even from the maintainer
- **Testing**: Security-relevant capabilities include dedicated test coverage
- **Supply Chain**: The project documents build and release processes to make them reproducible

### Security testing

The project employs these security testing approaches:

- **Property-based testing**: Uses Hypothesis to discover edge cases in argument parsing and input validation
- **Security-focused test cases**: Dedicated tests for injection prevention, path traversal protection, and input sanitization
- **Static analysis**: Ruff linter includes Bandit security checks (S-prefix rules) that flag common security issues
- **Type safety**: Comprehensive type checking with helps prevent classes of bugs that could lead to security issues
- **Code review**: All changes undergo review before merging, with security considerations in mind

## Scope

### In scope

I consider security issues in the following areas in scope for the framework itself:

- **Argument parsing vulnerabilities**: Injection attacks, escaping issues, or malformed input handling in the parser
- **Unsafe API design**: Framework APIs that make it easy for developers to introduce vulnerabilities in their applications
- **Path handling**: Path traversal vulnerabilities in framework-provided file operations (if any)
- **Terminal output**: Terminal control sequence injection or ANSI escape sequence vulnerabilities in framework code
- **Dependency vulnerabilities**: Security issues in direct dependencies that affect this framework
- **Unsafe defaults**: Framework configurations or behaviors that are insecure by default
- **Code execution paths**: Unintended code execution through framework capabilities
- **Memory safety**: Issues in any compiled extensions (if applicable)
- **Cryptographic usage**: Misuse of cryptography or weak random number generation in framework code

> [!NOTE]
> Vulnerabilities in applications built with this framework are generally out of scope unless they stem from a framework design flaw or insecure default.

### Out of scope

The following are generally not considered security vulnerabilities:

- Issues in third-party dependencies that don't affect this project's features
- Vulnerabilities requiring physical access to the user's machine
- Social engineering attacks against users
- Issues in user applications built with this framework (unless directly caused by framework bugs)
- Denial of service through resource exhaustion in user applications (unless caused by a framework bug that makes resource limits impossible to use)
- Terminal emulator-specific bugs not caused by this framework
- Issues requiring the user to explicitly run malicious code

## Bug bounty

This project does not offer a bug bounty program. I will publicly acknowledge security researchers who report valid vulnerabilities (unless they prefer to remain anonymous):

- **Security advisories**: Credited in the GitHub Security Advisory for the vulnerability
- **Release notes**: Mentioned in the release notes for the version containing the fix
- **Project documentation**: Listed in a "Security Acknowledgments" section in the project README

Acknowledgments will include the researcher's name and optionally a link to their website, GitHub profile, or social media (researcher's choice).

## Security updates

When I fix security issues:

1. **Fix development**: I will develop and test the fix on the main branch
2. **GitHub Security Advisory**: I will publish a security advisory with details about the vulnerability, affected versions, and the fix
3. **CVE assignment**: For high or critical severity issues, I will request a CVE through GitHub's CNA
4. **Disclosure**: After I merge and release the fix, I will make the security advisory public
5. **Notification**: GitHub will notify users watching the repository through the security advisory notification system

> [!NOTE]
> During pre-release development, I will apply security fixes to the main development branch. Once the project reaches 1.0 and has stable releases, I will apply security fixes to supported versions according to the version support policy.

## Questions

If you have questions about this security policy or want to discuss security practices for the project, you can:

- **Public discussions**: For general security questions, best practices, or policy clarifications, open a discussion in [GitHub Discussions](https://github.com/aclaf/aclaf/discussions)
- **Private contact**: For sensitive security concerns that don't constitute vulnerabilities, contact the maintainer directly at the preceding email address

> [!IMPORTANT]
> If you're unsure whether something is a vulnerability, err on the side of caution and report it privately.

## Policy updates

I may update this security policy as the project matures and I adopt new security practices. I will announce major changes to the policy in release notes.

---

*Last updated: 2025-11-11*
