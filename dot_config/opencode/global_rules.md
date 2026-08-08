# OpenCode Global Rules

Personal defaults for all OpenCode sessions. Follow more specific project rules
when present.

- Before saying a background task "will notify when done," verify it is
  actually progressing (check process/output state); a task can silently
  stall without ever completing or notifying.

## Memory
- See `~/.config/opencode/AGENTS.local.md` (machine-local, not in this public
   repo) for the pointer to this user's canonical personal-context store and
   its retrieval conventions. If that file is empty, no such store is
   configured on this machine.
- Prefer reusable, vendor-neutral plain-text/Markdown for anything meant to
  persist, so it converts losslessly into future context-retention systems.

## Git
- Load the `git-workflow` skill before repository-history changes.
- Match the target repository's established commit-message language; do not
  carry a convention from another repository into it.

## Safety
- Before an operation that can irreversibly delete or overwrite user data,
  explain its impact and obtain explicit confirmation.
- Prefer reversible changes and offer a backup when data loss is possible.
- Never expose or commit credentials, tokens, or plaintext secrets.
- Do not launch GUI terminal windows for interactive authentication without
  explicit user consent; if any are launched, close only those windows when
  finished and preserve pre-existing terminal sessions.
- Load the `independent-review` skill before implementing a non-trivial
  technical proposal (design/architecture change, credential generation,
  real-data operations, or a change to another repository); confirmation
  alone does not cover its review gate.

## Delegation
- Load the `model-routing` skill before selecting subagents, changing model
  assignments, or delegating consequential work.
- In OpenCode, satisfy an independent-review gate only through `review-main`,
  the fresh context-free read-only main-GPT reviewer.

## Tooling
- Use `uv` for Python dependency and environment management. Do not invoke
  `pip`, `virtualenv`, or `python -m venv` unless compatibility requires it.
- Do not install programming language runtimes globally; keep `uv` and Nix
  tooling global, and manage other runtimes, LSPs, and build tools per project
  with a Nix devShell/direnv.

## Output
- Reply in Japanese by default. Keep code, commands, paths, and identifiers
  unchanged.
- Write AI-readable files such as `AGENTS.md` and `SKILL.md` in English.
- Prefer ASCII/English filenames whenever practical; keep study-facing or
  user-facing file contents in Japanese.
