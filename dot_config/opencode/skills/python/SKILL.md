---
name: python
description: Python conventions for readable and reliable code
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Python

## Purpose

Define Python-specific conventions that improve readability, correctness, and maintainability.

## Core Principles

1. Follow idiomatic Python style and standard library practices.
2. Prefer explicitness over cleverness.
3. Use typing and tests to reduce regressions.

## Rules/Standards

### Style

- Follow PEP 8 naming and formatting conventions.
- Use `black` or the project formatter if specified.
- Keep functions focused and small.

### Types and Errors

- Add type hints for public APIs and complex functions.
- Use exceptions for exceptional conditions, not control flow.
- Prefer `pathlib` over string paths.

### Structure

- Group imports: standard library, third-party, local.
- Avoid mutable default arguments.

## Examples

Good:
- "Use `pathlib.Path` and type hints for file utilities."

Bad:
- "Use global state and implicit side effects."

## Edge Cases

- For performance hotspots, measure before optimizing.
- For legacy code, prioritize consistency with existing patterns.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://peps.python.org/pep-0008/
- https://peps.python.org/pep-0484/
- https://docs.python.org/3/library/pathlib.html
