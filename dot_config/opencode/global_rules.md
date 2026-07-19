# OpenCode Global Rules

Personal defaults for all OpenCode sessions. Follow more specific project rules
when present.

## Conduct
- Prefer clarity over cleverness and explicit behavior over implicit behavior.
- Prefer evidence over agreement. Correct unsupported assumptions.
- State material uncertainty and verification limits explicitly.
- Keep changes focused, composable, and fail-fast.

## Memory
- At session start, or when a task depends on earlier context, run
  `memory-read --query "<short task description>"`.
- Use the memory commands only. Never access their storage directly or run git
  against it.
- Record durable, reusable, non-sensitive facts conservatively with
  `memory-append`.
- Load the `memory` skill for maintenance, migration, import, export, or
  diagnosis.
- When a coherent non-trivial task changes durable personal context or project
  state, use the canonical route returned by `memory-read` to promote verified
  conclusions. Do not duplicate detailed facts in agent-memory.

## Safety
- Before an operation that can irreversibly delete or overwrite user data,
  explain its impact and obtain explicit confirmation.
- Prefer reversible changes and offer a backup when data loss is possible.
- Never expose or commit credentials, tokens, or plaintext secrets.

## Delegation
- Keep the primary agent as the default entry point.
- Load the `model-routing` skill before changing model assignments or delegating
  consequential work.
- Keep edits, secrets, security decisions, irreversible actions, and final
  verification on authenticated ChatGPT Plus agents.
- Preserve longer-window ChatGPT capacity by preferring eligible Claude Sonnet
  delegation whenever it is available; follow `model-routing` for the boundary.
- Treat delegated results as advisory until independently verified.
- Do not retry explicit quota, authentication, or unavailable-model failures
  in a loop.

## Tooling
- Use `uv` for Python dependency and environment management. Do not invoke
  `pip`, `virtualenv`, or `python -m venv` unless compatibility requires it.

## Output
- Reply in Japanese by default. Keep code, commands, paths, and identifiers
  unchanged.
- Write AI-readable files such as `AGENTS.md` and `SKILL.md` in English.
- Use project rules and relevant skills for language, tooling, naming, and git
  conventions.
- Keep responses direct and concise. Load additional skills only when relevant.
