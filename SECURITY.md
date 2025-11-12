# Security policy

## Project status

This project is currently in pre-release development (pre-1.0) and is maintained by a single developer. While the project is not yet released to PyPI, security is taken seriously during development to establish good practices from the start.

**Important**: Pre-release software may contain undiscovered security vulnerabilities. The project is not recommended for production use until version 1.0 is released. If you choose to use pre-release versions, do so with appropriate caution and security measures.

## Supported versions

As an unreleased project, there are no stable versions yet. Security updates will be applied to the main development branch as they are identified and resolved.

Once the project reaches 1.0 and has stable releases, this section will be updated with a clear support matrix indicating which versions receive security updates.

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

> **Note**: The `security@aclaf.sh` email address is monitored by the maintainer. Response times may vary based on availability.

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
- Python version: [e.g., 3.12.5]
- Operating system: [e.g., Ubuntu 24.04]
```

### Reporting language

Security reports should be submitted in English. This ensures clear communication and faster response times.

### What to expect

As a solo-maintained project, please understand the response timeline may vary based on the maintainer's availability:

- **Initial Response**: Within 7 days of your report, you'll receive acknowledgment that your report was received
- **Assessment**: Within 14 days, you'll receive an assessment of whether the issue qualifies as a security vulnerability and the planned response
- **Resolution Timeline**: Depending on severity and complexity, fixes may take anywhere from a few days to several weeks
- **Coordinated Disclosure**: After a fix is available, a coordinated disclosure will be made through GitHub Security Advisories. Typically, disclosure occurs 7-14 days after the fix is released, allowing time for users to update. Security researchers will be consulted on disclosure timing. If a fix cannot be developed within 90 days, a public advisory will be issued with mitigation recommendations

### Severity guidelines

Vulnerabilities will be prioritized based on their potential impact:

- **Critical**: Remote code execution, authentication bypass, or exposure of sensitive credentials
- **High**: Privilege escalation, injection vulnerabilities, or significant data exposure
- **Medium**: Denial of service, information disclosure without sensitive data
- **Low**: Issues with limited impact or requiring significant user interaction

Critical and high severity issues will be prioritized for immediate attention.

## Security practices

This project follows these security practices during development:

- **Minimal dependencies**: The project maintains a minimal dependency footprint (currently only `typing-extensions` as a runtime dependency) to reduce supply chain risk
- **Dependency pinning**: All dependencies are pinned with cryptographic hashes in lock files (`uv.lock`)
- **Automated scanning**: Dependabot runs weekly to check for dependency vulnerabilities
- **Publishing**: Releases will use PyPI Trusted Publishing with automatic Sigstore attestations (once published)
- **Code Review**: All changes go through review before merging, even from the maintainer
- **Testing**: Security-relevant functionality includes dedicated test coverage
- **Supply Chain**: Build and release processes are documented and reproducible

### Security testing

The project employs several security testing approaches:

- **Property-based testing**: Uses Hypothesis to discover edge cases in argument parsing and input validation
- **Security-focused test cases**: Dedicated tests for injection prevention, path traversal protection, and input sanitization
- **Static analysis**: Ruff linter includes Bandit security checks (S-prefix rules) that flag common security issues
- **Type safety**: Comprehensive type checking with helps prevent classes of bugs that could lead to security issues
- **Code review**: All changes undergo review before merging, with security considerations in mind

## Scope

### In scope

Security issues in the following areas are considered in scope for the framework itself:

- **Argument parsing vulnerabilities**: Injection attacks, escaping issues, or malformed input handling in the parser
- **Unsafe API design**: Framework APIs that make it easy for developers to introduce vulnerabilities in their applications
- **Path handling**: Path traversal vulnerabilities in framework-provided file operations (if any)
- **Terminal output**: Terminal control sequence injection or ANSI escape sequence vulnerabilities in framework code
- **Dependency vulnerabilities**: Security issues in direct dependencies that affect this framework
- **Unsafe defaults**: Framework configurations or behaviors that are insecure by default
- **Code execution paths**: Unintended code execution through framework functionality
- **Memory safety**: Issues in any compiled extensions (if applicable)
- **Cryptographic usage**: Misuse of cryptography or weak random number generation in framework code

Note: Vulnerabilities in applications built with this framework are generally out of scope unless they stem from a framework design flaw or insecure default.

### Out of scope

The following are generally not considered security vulnerabilities:

- Issues in third-party dependencies that don't affect this project's functionality
- Vulnerabilities requiring physical access to the user's machine
- Social engineering attacks against users
- Issues in user applications built with this framework (unless directly caused by framework bugs)
- Denial of service through resource exhaustion in user applications (unless caused by a framework bug that makes resource limits impossible to implement)
- Terminal emulator-specific bugs not caused by this framework
- Issues requiring the user to explicitly run malicious code

## Bug bounty

This project does not offer a bug bounty program. However, security researchers who report valid vulnerabilities will be publicly acknowledged (unless they prefer to remain anonymous):

- **Security advisories**: Credited in the GitHub Security Advisory for the vulnerability
- **Release notes**: Mentioned in the release notes for the version containing the fix
- **Project documentation**: Listed in a "Security Acknowledgments" section in the project README

Acknowledgments will include the researcher's name and optionally a link to their website, GitHub profile, or social media (researcher's choice).

## Security updates

When security issues are fixed:

1. **Fix development**: The fix will be developed and tested on the main branch
2. **GitHub Security Advisory**: A security advisory will be published with details about the vulnerability, affected versions, and the fix
3. **CVE assignment**: For high or critical severity issues, a CVE will be requested through GitHub's CNA
4. **Disclosure**: After the fix is merged and released, the security advisory will be made public
5. **Notification**: Users watching the repository will be notified through GitHub's security advisory notification system

**Note for pre-1.0 releases**: During pre-release development, security fixes will be applied to the main development branch. Once the project reaches 1.0 and has stable releases, security fixes will be backported according to the version support policy.

## Questions

If you have questions about this security policy or want to discuss security practices for the project, you can:

- **Public discussions**: For general security questions, best practices, or policy clarifications, open a discussion in [GitHub Discussions](https://github.com/aclaf/aclaf/discussions)
- **Private contact**: For sensitive security concerns that don't constitute vulnerabilities, contact the maintainer directly at the security email address above

**Important**: If you're unsure whether something is a vulnerability, err on the side of caution and report it privately.

## Policy updates

This security policy may be updated as the project matures and new security practices are adopted. Major changes to the policy will be announced in release notes.

---

*Last updated: 2025-11-11*
