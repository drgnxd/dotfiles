---
name: security_experts
description: Security best practices for software & infrastructure
---

# Security Experts

## Purpose
Baseline security practices for protecting data, systems, users.

## Core Principles
1. Least privilege & defense in depth
2. Protect secrets & sensitive data (at rest & in transit)
3. Validate inputs, reduce attack surface

## Rules

### Secrets
- Never hardcode secrets in source control
- Use secret managers or env vars
- Rotate secrets if exposure suspected

### Input & Output
- Validate & sanitize all external input
- Encode outputs to prevent injection vulnerabilities

### Dependencies
- Track third-party deps, update regularly
- Avoid unmaintained or high-risk packages

## Examples

✅ "Store API keys in secret manager, load at runtime"
❌ "Commit credentials in config for convenience"

## Edge Cases
- Legacy systems: doc compensating controls
- Security incidents: prioritize containment & logging

See `COMMON.md`.

Refs: [OWASP Top 10](https://owasp.org/www-project-top-ten/), [cheat sheets](https://cheatsheetseries.owasp.org/) (2026-01-26)
