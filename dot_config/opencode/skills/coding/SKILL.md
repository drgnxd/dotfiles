---
name: coding
description: Baseline coding standards grounded in Unix philosophy and clean design.
license: Apache-2.0
metadata:
  author: drgnxd
  version: "1.0.0"
  category: coding
---

# Coding Skill - Unix Philosophy

This skill provides baseline guidance for writing maintainable, composable code.
Project-specific rules always take priority over this global skill.

## Purpose

- Define a consistent baseline for code style and structure
- Encourage small, testable units that compose well
- Provide a clear override hierarchy for local rules

## Core Principles

1. Single responsibility: each module or function does one job.
2. Composability: prefer standard input and output with small tools.
3. Clarity first: readability beats cleverness.
4. Explicit errors: handle failures loudly and with context.
5. Project overrides: local rules always win.

## Rules and Standards

### Priority Hierarchy

Rule: follow the most local rule set available.

Order:
1. `.opencode/skills/coding/SKILL.md`
2. `CODING_STANDARDS.md` or `STYLE_GUIDE.md`
3. `.editorconfig`
4. Language configs (`pyproject.toml`, `setup.cfg`, `.eslintrc`, `.prettierrc`)
5. This global skill

Rationale: local constraints prevent style conflicts.

### Unix Philosophy

Rule: design small, composable components.

Good:
- `read_file()` reads only, `parse_json()` parses only
- CLI tools read from stdin and write to stdout

Bad:
- one function reads, parses, and writes in one step

Rationale: small components are easier to test and reuse.

### Naming Conventions

Rule: use descriptive names and consistent casing.

- variables and functions: snake_case
- constants: UPPER_SNAKE_CASE
- classes and types: PascalCase

### Functions and Modules

Rule: keep functions focused and short.

- one responsibility per function
- avoid large, multi-purpose blocks
- prefer pure functions when practical

### Error Handling

Rule: catch specific exceptions and add context.

Good:
```python
try:
    with open(path) as handle:
        return handle.read()
except FileNotFoundError as exc:
    raise RuntimeError(f"Missing file: {path}") from exc
```

Bad:
```python
try:
    return open(path).read()
except Exception:
    return ""
```

### Documentation

Rule: document public APIs with clear docstrings.
Include purpose, arguments, return values, and raised exceptions.

### Comment Language

Rule: write comments and docstrings in English by default.
Follow project-specific guidance if a different language is required.

### Imports and Structure

Rule: group imports in this order.

1. standard library
2. third-party
3. local packages
4. types
5. styles or assets

### Language-Specific Guidelines

- Python: PEP 8, type hints, max line length 88
- Shell: `set -euo pipefail`, quote variables
- JavaScript/TypeScript: ESLint + Prettier, prefer `const`

### Tools and Scripts

- `bin/check_style.sh`: run lint and format checks for Python and shell
- `bin/lint.py`: wrapper for `bin/check_style.sh`
- `share/templates/module_template.py`: Python module template

### Validation

Run before committing:
```bash
bin/check_style.sh src/
bin/lint.py src/
```

## Examples

For detailed examples, see:

- `doc/unix_philosophy.md`
- `doc/clean_code.md`
- `doc/best_practices.md`
- `doc/anti_patterns.md`

## Related Skills

- `documentation`: documentation guidelines
- `testing`: test strategy and coverage
- `refactoring`: safe refactoring
- `default_naming_conventions`: default naming rules

## References

Last accessed: 2026-01-26

- https://agentskills.io/specification
- https://en.wikipedia.org/wiki/Unix_philosophy
