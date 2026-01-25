---
name: code_review
description: Code review focus areas and quality checklist
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Code Review

## Purpose

Provide a consistent checklist for reviewing code changes effectively and fairly.

## Core Principles

1. Focus on correctness, clarity, and maintainability.
2. Be specific and actionable in feedback.
3. Prioritize risks and user impact.

## Rules/Standards

### Correctness

- Validate edge cases and error handling.
- Confirm data validation and security concerns.

### Readability

- Ensure naming is clear and consistent.
- Prefer simple control flow over deeply nested logic.

### Tests

- Verify new behavior is covered by tests.
- Confirm tests are deterministic and scoped.

## Examples

Good:
- "This function can return null; add a guard or update the type."

Bad:
- "Looks bad." (no actionable detail)

## Edge Cases

- For large changes, suggest splitting into smaller PRs.
- For performance-critical paths, ask for benchmarks.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References


- https://google.github.io/eng-practices/review/reviewer/ (Last accessed: 2026-01-26)
- https://google.github.io/eng-practices/review/reviewer/standard.html (Last accessed: 2026-01-26)
- https://google.github.io/eng-practices/review/ (Last accessed: 2026-01-26)
