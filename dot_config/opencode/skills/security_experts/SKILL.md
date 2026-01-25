---
name: security_experts
description: Security best practices for software and infrastructure
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Security Experts

## Purpose

Provide baseline security practices for protecting data, systems, and users.

## Core Principles

1. Apply least privilege and defense in depth.
2. Protect secrets and sensitive data at rest and in transit.
3. Validate inputs and reduce attack surface.

## Rules/Standards

### Secrets

- Never hardcode secrets in source control.
- Use secret managers or environment variables.
- Rotate secrets if exposure is suspected.

### Input and Output

- Validate and sanitize all external input.
- Encode outputs to prevent injection vulnerabilities.

### Dependencies

- Track third-party dependencies and update regularly.
- Avoid unmaintained or high-risk packages.

## Examples

Good:
- "Store API keys in a secret manager and load them at runtime."

Bad:
- "Commit credentials in a config file for convenience."

## Edge Cases

- For legacy systems, document compensating controls.
- For security incidents, prioritize containment and logging.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://owasp.org/www-project-top-ten/
- https://cheatsheetseries.owasp.org/
- https://owasp.org/www-project-cheat-sheets/
