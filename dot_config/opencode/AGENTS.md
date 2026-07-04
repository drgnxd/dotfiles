# OpenCode Global Rules

Global rules for `~/.config/opencode`.
Project `AGENTS.md` files override these rules.

## Core Principles
- Clarity over cleverness. Explicit over implicit.
- Composable, fail-fast, single responsibility.
- Prefer facts over agreement. Correct wrong assumptions.
- State uncertainty explicitly when unsure.

## Memory
You have a persistent local memory store, reached through two commands on PATH:
`memory-read` and `memory-append`. Their storage location, file format, and git
handling live inside the commands — never hardcode paths or run git for memory here,
and do not read or write the underlying files directly.

At the start of a session, or whenever a request depends on earlier context — the
user's preferences, ongoing projects, or decisions made before — run `memory-read`
first, so you build on what is already known instead of asking again.

Record durable knowledge as you work, without waiting to be told. When you learn
something that would help a future session — a stable preference, a project
convention, an architectural or tooling decision, or a correction the user makes to
your approach — run `memory-append "<one concise, self-contained fact>"`. Do the same
whenever the user explicitly asks you to remember something.

Store conservatively. Keep lasting, reusable facts; skip transient chatter, one-off
task details, and anything sensitive such as credentials, tokens, or private personal
data. Write one fact per call, phrased to stand on its own without the surrounding
conversation.
<!-- agent-memory:managed -->

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

**Last updated**: 2026-04
