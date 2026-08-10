# OpenCode Global Rules

- Follow more specific project rules when present. Before reporting a background task as progressing or complete, verify its process or output state.
- Prefer reusable, vendor-neutral plain-text/Markdown for persisted material.
- Follow an available Skill description as a mandatory trigger: load the applicable Skill before proceeding.
- Before an irreversible overwrite or deletion, explain its impact and obtain explicit confirmation. Prefer reversible changes or offer a backup. Never expose or commit credentials, tokens, or plaintext secrets.
- Do not launch GUI terminal windows for interactive authentication without explicit consent; close only windows launched for that task.
- Use `uv` for Python dependency management; do not invoke `pip`, `virtualenv`, or `python -m venv` unless compatibility requires it. Do not globally install runtimes, LSPs, or build tools; manage them per project with a Nix devShell/direnv.
- Reply in Japanese by default. Keep code, commands, paths, and identifiers unchanged. Write AI-readable files in English and user-facing material in Japanese. Prefer ASCII filenames unless Unicode is justified.
