---
name: python
description: Python conventions for readable, reliable code
---

# Python

## Purpose
Python-specific conventions for readability, correctness, maintainability.

## Core Principles
1. Idiomatic Python style & stdlib practices
2. Explicitness > cleverness
3. Typing & tests reduce regressions

## Rules

### Style
- PEP 8 naming & formatting
- Use `black` or project formatter if specified
- Small, focused functions

### Types & Errors
- Type hints for public APIs & complex functions
- Exceptions for exceptional conditions, not control flow
- Prefer `pathlib` over string paths

### Structure
- Group imports: stdlib → third-party → local
- Avoid mutable default arguments

## Examples

✅ "Use `pathlib.Path` & type hints for file utilities"
❌ "Use global state & implicit side effects"

## Edge Cases
- Performance hotspots: measure before optimizing
- Legacy code: prioritize consistency w/ existing patterns

See `COMMON.md`.

Refs: [PEP 8](https://peps.python.org/pep-0008/), [PEP 484](https://peps.python.org/pep-0484/), [pathlib](https://docs.python.org/3/library/pathlib.html) (2026-01-26)
