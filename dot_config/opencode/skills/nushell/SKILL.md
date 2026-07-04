---
name: nushell
description: Use when writing or editing Nushell scripts, config.nu/env.nu, or autoload modules — syntax, structured pipelines, module layout, validation, and PATH handling.
---

# Nushell Is Not POSIX

- Do not write POSIX shell idioms in Nushell files.
- Command substitution uses `(...)`, not `$(...)`.
- Nushell pipelines pass structured values, not plain text by default.
- There is no `set -e` equivalent; handle fallible commands through Nushell's error and `complete` patterns.

# Reusable Logic

- Define reusable module functions with `export def`.
- Keep function signatures explicit when practical.
- Prefer small commands that return structured values over commands that print formatted strings.

# Configuration Layout

- Put environment setup in `env.nu`.
- Put interactive shell behavior in `config.nu`.
- Keep shared modules under `autoload/` so Nushell can load them predictably.

# Structured Pipelines

- Prefer built-ins such as `where`, `get`, `select`, `reject`, `each`, `to json`, and `from json` over text parsing tools.
- Avoid unnecessary `grep`, `sed`, or `awk` translations when a structured Nushell operation exists.
- Preserve records and tables until the boundary where a string is required.

# Validation

- Validate full files with `nu --check`.
- Use `nu --ide-check` when JSON diagnostics are needed, matching this repo's CI usage.
- Check the same file paths CI checks when changing Nushell config or autoload modules.

# PATH Handling

- Use this repo's `path-add` helper for PATH updates.
- `path-add` should prepend paths and check existence before insertion.
- Avoid directly rebuilding `$env.PATH` unless the helper cannot express the change.
