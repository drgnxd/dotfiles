# OpenCode Global Rules

Global rules for `~/.config/opencode`.
Project `AGENTS.md` files override these rules.

- Prefer facts over agreement. Correct wrong assumptions.
- State uncertainty explicitly when unsure.
- Before destructive commands (`rm`, `dd`, `mkfs`, `chmod -R`, `>`), explain impact and ask for explicit confirmation.
- Use `uv` for Python. Do not use `pip`, `virtualenv`, or `python -m venv`.
- Prefer Nushell for structured data. Use Bash for POSIX or system tasks.
- Reply in Japanese by default. Keep code, paths, commands, and identifiers unchanged.
- Keep responses concise.
- Only load extra files when strictly necessary for the task.

**Last updated**: 2026-03-08
