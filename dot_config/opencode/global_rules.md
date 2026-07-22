# OpenCode Global Rules

Personal defaults for all OpenCode sessions. Follow more specific project rules
when present.

## Conduct
- Prefer clarity over cleverness and explicit behavior over implicit behavior.
- Prefer evidence over agreement. Correct unsupported assumptions.
- State material uncertainty and verification limits explicitly.
- Keep changes focused, composable, and fail-fast.

## Memory
- `~/dev/context-core` is the canonical store for durable personal context,
  knowledge, decisions, and progress logs. Before non-trivial personal,
  research, learning, or career work, read its `context/current.md` and follow
  `projects/index.md`, `knowledge/maps/index.md`, or `decisions/index.md`.
- Prefer reusable, vendor-neutral plain-text/Markdown for anything meant to
  persist, so it converts losslessly into future context-retention systems.
- Archive complete OpenCode and Claude Code conversation histories locally
  until manually deleted; keep only durable summaries and preferences in the
  canonical files above, never raw conversation dumps.
- The `memory-read`/`memory-append` agent-memory CLI store is deprecated as of
  2026-07-23 — its content was migrated into this file and into the relevant
  project `AGENTS.md`/canonical files, then retracted. Do not read from or
  write to it for routine work; the `memory` skill remains only for a one-off
  export/diagnosis of the historical archive if ever needed.

## Git
- Before any commit or amend, identify the active repository and read its
  nearest project instructions. Inspect its `git status`, relevant diff, and
  recent commit history.
- Match the active repository's documented convention or recent history,
  including commit-message language. Never carry a commit convention from a
  different repository into the current one.
- Avoid creating git branches for documentation-only or otherwise simple
  updates unless explicitly requested or clearly necessary.
- Load the `git-workflow` skill before repository-history changes, stage only
  intended files, run the active repository's required validation gates, and
  do not commit when any gate fails.

## Safety
- Before an operation that can irreversibly delete or overwrite user data,
  explain its impact and obtain explicit confirmation.
- Prefer reversible changes and offer a backup when data loss is possible.
- Never expose or commit credentials, tokens, or plaintext secrets.
- Do not launch GUI terminal windows for interactive authentication without
  explicit user consent; if any are launched, close only those windows when
  finished and preserve pre-existing terminal sessions.

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
- Do not install programming language runtimes globally; keep `uv` and Nix
  tooling global, and manage other runtimes, LSPs, and build tools per project
  with a Nix devShell/direnv.
- Before building a new tool or feature, check whether an existing OSS tool
  (or combination of tools) already solves it; avoid reinventing the wheel and
  build custom only after confirming a real gap.
- Do not suggest Oracle Cloud (including the Always Free tier) — a prior
  account-creation attempt failed for an unresolved reason.

## Output
- Reply in Japanese by default. Keep code, commands, paths, and identifiers
  unchanged.
- Write AI-readable files such as `AGENTS.md` and `SKILL.md` in English.
- Use project rules and relevant skills for language, tooling, naming, and git
  conventions.
- Prefer ASCII/English filenames whenever practical; keep study-facing or
  user-facing file contents in Japanese.
- Keep responses direct and concise. Load additional skills only when relevant.
