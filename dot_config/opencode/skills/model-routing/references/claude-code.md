# Claude Code routing

Provisional mapping; `settings.json` and the agent files under
`dot_local/share/claude/agents/` are canonical. Confirm against them before
relying on this file.

- Use only Claude Code models, tools, and subagents. Never delegate to OpenCode,
  Codex, or any other client or external AI.
- Main model: the `model` in `settings.json` (currently `sonnet`).
- `independent-review` gate: dispatch the `Review` agent (read-only allowlist;
  must end with a `REVIEW_STATUS:` line). Do not substitute another agent.
- Discovery and planning: `Explore` and `Plan`. Neither restricts Bash, so do
  not treat them as a hard read-only guarantee.
- `Review` currently uses a denylist (`disallowedTools`), not an allowlist.
  Switching to `tools:` needs a smoke test first: confirm the result still
  returns to the caller and which tools remain.
- Unavailable-model and usage-limit errors are stop conditions, as in the main
  skill.
