---
name: coding
description: Baseline coding standards (Unix philosophy & clean design)
---

# Coding - Unix Philosophy

Baseline for maintainable, composable code. Project-specific rules always take priority.

Aim:
- Consistent baseline for style & structure
- Small, testable units that compose well
- Clear override hierarchy

Core:
1. Single responsibility per module/function
2. Composability: standard I/O, small tools
3. Clarity > cleverness
4. Explicit errors w/ context
5. Project overrides: local rules win

Do:

### Priority Hierarchy
1. `.opencode/skills/coding/SKILL.md`
2. `CODING_STANDARDS.md` / `STYLE_GUIDE.md`
3. `.editorconfig`
4. Language configs (`pyproject.toml`, `.eslintrc`, etc.)
5. This global skill

### Unix Philosophy
Design small, composable components.

✅ `read_file()` reads only, `parse_json()` parses only
❌ One function reads, parses, writes in one step

### Naming
- Variables/functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes/types: `PascalCase`

### Functions
- One responsibility
- Short & focused
- Prefer pure when practical

### Error Handling
Catch specific exceptions, add context.

✅ 
```python
try:
    with open(path) as f:
        return f.read()
except FileNotFoundError as e:
    raise RuntimeError(f"Missing: {path}") from e
```

❌ 
```python
try:
    return open(path).read()
except Exception:
    return ""
```

### Documentation
Doc public APIs: purpose, args, returns, exceptions.

### Comments
English by default; follow project if different.

### Imports
Order: stdlib → third-party → local → types → assets

### Language-Specific
- Python: PEP 8, type hints, max line 88
- Shell: `set -euo pipefail`, quote vars
- JS/TS: ESLint + Prettier, prefer `const`

### Tools
- `bin/check_style.sh`: lint & format checks
- `bin/lint.py`: wrapper for check_style.sh
- `share/templates/module_template.py`: Python template

See `doc/unix_philosophy.md`, `doc/clean_code.md`, `doc/best_practices.md`, `doc/anti_patterns.md` for details.

Related: `documentation`, `testing`, `refactoring`, `default_naming_conventions`

Refs: See doc/refs.md
