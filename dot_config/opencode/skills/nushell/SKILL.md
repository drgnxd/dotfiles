---
name: nushell
description: Use when writing or editing Nushell scripts, config.nu/env.nu, or autoload modules — syntax, structured pipelines, module layout, validation, and PATH handling.
---

# Nushell

- Nushell is not POSIX: use `(...)` for command substitution and structured
  pipelines instead of text-first shell idioms.
- Prefer built-ins such as `where`, `get`, `select`, `each`, `to json`, and
  `from json` over external text parsing when structured values are available.
- Preserve records and tables until a string boundary is required.
- Handle fallible external commands through `complete` and inspect exit codes.
