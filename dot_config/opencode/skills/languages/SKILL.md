---
name: languages
description: Language-specific coding conventions for Bash, Python, JavaScript, Rust, and Nushell, including safety patterns and anti-patterns.
---

# Bash

- Use strict mode by default: `set -euo pipefail`.
- Quote variable expansions as `"${var}"`.
- Validate required inputs before using them.
- Preferred pattern: `readonly V="${1}"; [[ -n "$V" ]] || exit 1`.
- Avoid unsafe patterns like unquoted expansion in destructive commands (for example `rm -rf $V`).

# Python

- Follow PEP 8 and include type hints where practical.
- Prefer `pathlib` over legacy path APIs.
- Do not use mutable default arguments.
- Use `uv` workflows:
  - Create env: `uv venv`
  - Install deps: `uv pip install <pkg>`
  - Run scripts: `uv run script.py`
- Forbidden tools: `pip`, `python -m venv`, `virtualenv`.
- Import grouping order: standard library, third-party, local modules.
- Target line length: 88.

# JavaScript / TypeScript

- Prefer `const`/`let` over `var`.
- Use strict equality (`===`, `!==`).
- Prefer `async`/`await` over callback-heavy style.
- Avoid `any` unless explicitly justified.
- Acceptable async pattern: `const d = await fetch(u).then(r => r.json())`.

# Rust

- Keep code `rustfmt` and `clippy` clean.
- Prefer `Result`/`Option` propagation over `unwrap()` in non-test code.
- Prefer iterator-based style over manual index loops.
- Prefer explicit result signatures such as `fn read(p: &Path) -> Result<String>`.

# Nushell

- Prefer structured data pipelines and immutable transformations.
- Use explicit typing and schema-preserving transformations when possible.
- Common table filter pattern: `ls | where size > 1mb | select name size`.
- Common transform pattern: `open data.json | each { |x| $x.value * 2 }`.
- Error handling pattern: `do { cmd } | complete | if $in.exit_code != 0 { error make {...} }`.
- Structured file conversion: `open data.csv | from csv | save output.json`.
- Environment update pattern: `$env.PATH = ($env.PATH | append "/path")`.
- Interop with external commands via `^cmd` or `bash -c` when needed.
- Avoid `eval` and unchecked `run-external` usage.
