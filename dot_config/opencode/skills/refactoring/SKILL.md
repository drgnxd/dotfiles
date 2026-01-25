---
name: refactoring
description: Refactoring strategies for safe and incremental improvements
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Refactoring

## Purpose

Provide guidance for improving code structure while preserving behavior.

## Core Principles

1. Preserve existing behavior and contracts.
2. Make small, reversible changes.
3. Use tests and tooling to validate outcomes.

## Rules/Standards

### Planning

- Identify the goal: readability, reuse, or performance.
- Avoid mixing refactors with new feature work.

### Execution

- Refactor in small steps with checkpoints.
- Run tests after each significant change.
- Keep public APIs stable when possible.

## Examples

Good:
- "Extract a function, update tests, then replace call sites."

Bad:
- "Rewrite the entire module without tests."

## Edge Cases

- If tests are missing, add characterization tests first.
- For high-risk areas, coordinate with reviewers before large refactors.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://martinfowler.com/books/refactoring.html
- https://refactoring.com/catalog/
- https://refactoring.guru/refactoring
