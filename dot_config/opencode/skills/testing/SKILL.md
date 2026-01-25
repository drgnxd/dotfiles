---
name: testing
description: Testing strategy and coverage guidelines
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Testing

## Purpose

Define a balanced testing strategy that improves confidence without excessive cost.

## Core Principles

1. Favor fast, deterministic tests for core logic.
2. Cover critical paths and failure modes.
3. Keep tests readable and maintainable.

## Rules/Standards

### Test Types

- Use unit tests for isolated logic.
- Use integration tests for cross-component behavior.
- Keep end-to-end tests limited to high-value flows.

### Quality

- Avoid flaky tests; fix or quarantine them quickly.
- Assert outcomes, not implementation details.

## Examples

Good:
- "Add unit tests for input validation and error paths."

Bad:
- "Only test the happy path and ignore failures."

## Edge Cases

- If external services are required, use mocks or test doubles.
- For time-dependent logic, control the clock in tests.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References


- https://martinfowler.com/articles/practical-test-pyramid.html (Last accessed: 2026-01-26)
- https://martinfowler.com/bliki/TestPyramid.html (Last accessed: 2026-01-26)
- https://web.dev/articles/ta-strategies (Last accessed: 2026-01-26)
