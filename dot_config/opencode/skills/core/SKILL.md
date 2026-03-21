---
name: core
description: Always-on coding fundamentals for safety, naming conventions, import order, and instruction precedence across all tasks.
---

# Core Principles

- Clarity over cleverness.
- Explicit behavior over implicit behavior.
- Prefer composable solutions.
- Fail fast when assumptions are violated.
- Keep single responsibility at function/module boundaries.

# Safety Rules

- Treat these as destructive operations: `rm`, `dd`, `mkfs`, `chmod -R`, and shell redirection overwrite (`>`).
- Before any destructive action, explain what will change, where it will change, and why it is needed.
- Obtain explicit confirmation before execution.
- Offer a backup path before irreversible operations.

# Python Package Management

- `uv` is mandatory for environment and package workflows.
- Never use `pip`, `python -m venv`, or `virtualenv` directly.

# Naming Conventions

- Files: `snake_case` (exceptions: `README.md`, `SKILL.md`, `AGENTS.md`).
- Variables and functions: `snake_case`.
- Constants: `UPPER_SNAKE`.
- Classes and types: `PascalCase`.
- Acceptable short forms when clear: `src`, `lib`, `doc`, `cfg`, `bin`, `tmp`, `env`, `pkg`.

# Instruction Precedence

Apply project guidance in this order:

1. `.opencode/skills`
2. `CODING_STANDARDS.md`
3. `.editorconfig`
4. Language-specific configuration
5. Global defaults

# Import Order

Use this import grouping order:

1. Standard library
2. Third-party dependencies
3. Local project modules
4. Type-only imports
5. Static assets/resources

# Reasoning Activation

- Keep active, mode-aware reasoning enabled.
- For decision models and confidence handling, load and follow the `thinking` skill.
