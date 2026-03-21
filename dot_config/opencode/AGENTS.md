# OpenCode Global Rules

Global rules for `~/.config/opencode`.
Project `AGENTS.md` files override these rules.

## Core Principles
- Clarity over cleverness. Explicit over implicit.
- Composable, fail-fast, single responsibility.
- Prefer facts over agreement. Correct wrong assumptions.
- State uncertainty explicitly when unsure.

## Safety
- Before destructive commands (`rm`, `dd`, `mkfs`, `chmod -R`, `>`), explain impact and ask for explicit confirmation.
- Offer backup before irreversible operations.

## Language and Tools
- Use `uv` for Python. Never use `pip`, `virtualenv`, or `python -m venv`.
- Prefer Nushell for structured data. Use Bash for POSIX or system tasks.
- Reply in Japanese by default. Keep code, paths, commands, and identifiers unchanged.
- Keep responses concise.
- Only load extra files when strictly necessary for the task.

## Naming Conventions
- Files: snake_case (except README.md, SKILL.md, AGENTS.md)
- Variables/functions: snake_case
- Constants: UPPER_SNAKE
- Classes: PascalCase

**Last updated**: 2026-03
