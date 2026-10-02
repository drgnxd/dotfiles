---
name: nushell
description: Use when editing Nushell code or configuration.
---

# Nushell

- Nushell is not POSIX: use `(...)` for command substitution and structured
  pipelines instead of text-first shell idioms.
- Handle fallible external commands through `complete` and inspect exit codes.
- In `$"..."` and `$'...'`, every `(...)` runs as a command at runtime,
  including prose like `line(s)`; in `$"..."` escape it as `\(`/`\)`,
  otherwise concatenate or use a plain string.
- `nu file.nu` calls any `main` in scope with no arguments, including one
  pulled in by `source`, so sourcing a job script to test helpers runs the
  real job. Put the helpers in a module with `export def` and `use` it.
