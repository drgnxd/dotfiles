---
name: python
description: Python conventions for readable, reliable code
---

# Python

Aim:
- Readability, correctness, maintainability

Core:
- Idiomatic stdlib usage
- Explicitness > cleverness
- Types & tests

Do:

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

Refs: See doc/refs.md
