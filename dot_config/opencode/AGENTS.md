# OpenCode Global Rules

Global rules for `~/.config/opencode`.
Project `AGENTS.md` files override these rules.

## Core Principles
- Clarity over cleverness. Explicit over implicit.
- Composable, fail-fast, single responsibility.
- Prefer facts over agreement. Correct wrong assumptions.
- State uncertainty explicitly when unsure.

## Memory
You have a persistent local memory store, reached through six commands on PATH:
`memory-read`, `memory-append`, `memory-maintain`, `memory-export`, `memory-import`,
and `memory-rescope-legacy`. The last command performs explicit legacy project
migration. Storage, schema migration, and git handling live inside the commands.
Never hardcode paths, run git for memory, or access the underlying files directly.

At the start of a session, or whenever a request depends on earlier context — the
user's preferences, ongoing projects, or decisions made before — run
`memory-read --query "<short task description>"` first. The command includes global
memory and memory scoped to the current git project, then enforces a context budget.
Use `--scope global` when project memory must be excluded. Use `--all` only for
diagnosis or explicit export review.

When `memory-read` reports that maintenance is due, run `memory-read --maintenance`,
review the JSONL active projection for the current global and project scope, and
preserve each retained record's `memory_id` and `scopes`. Edit fields in place, omit
records that should be retracted, and add new records only with explicit `scopes`.
Pass that JSONL to `memory-maintain` from the same project and the generation token as
its sole argument. If the generation changed, repeat the maintenance read. Use
`--all` on both commands only for an explicit whole-store maintenance operation.
Maintenance appends update and retraction events; it never rewrites event history.

Record durable knowledge as you work, without waiting to be told. When you learn
something that would help a future session — a stable preference, a project
convention, an architectural or tooling decision, or a correction the user makes to
your approach — run `memory-append "<one concise, self-contained fact>"` from the
active project. Use `--scope global` for cross-project preferences and `--pin` only
for a tiny set of facts that must always enter context. Do the same whenever the user
explicitly asks you to remember something.

Store conservatively. Keep lasting, reusable facts; skip transient chatter, one-off
task details, and anything sensitive such as credentials, tokens, or private personal
data. Write one fact per call, phrased to stand on its own without the surrounding
conversation. Use `memory-export --output <new-directory>` for a portable bundle and
`memory-import <jsonl-or-bundle> --dry-run` before importing unfamiliar data.
<!-- agent-memory:managed -->

## Safety
- Before destructive commands (`rm`, `dd`, `mkfs`, `chmod -R`, `>`), explain impact and ask for explicit confirmation.
- Offer backup before irreversible operations.

## Adaptive Model Routing
- The primary agent's model is selected when OpenCode starts and cannot be changed mid-session. Select subagents and `claude_delegate` deliberately for independent work.
- Before delegating, classify the task by risk, required capability, independence, and evidence needed. Keep edits, secrets, security decisions, irreversible actions, final reviews, and session compaction on authenticated ChatGPT Plus agents.
- Use the free `explore` agent only for bounded, non-sensitive, read-only repository inspection. Escalate conflicting, incomplete, or high-impact results to a Plus agent.
- Use `claude_delegate` only for an independent, read-only second opinion or targeted inspection. Its result is advisory and must be verified before acting on it.
- Treat explicit provider signals as capacity facts: `429`, usage-limit, authentication, or unavailable-model errors make that route unavailable for the current task. Do not retry it in a loop; select an eligible alternative and report the fallback.
- Local `opencode stats` measures historical consumption, not remaining subscription quota. Do not infer remaining capacity from token counts, and do not send probe requests solely to measure a provider's quota.
- When capacity is unknown, preserve premium capacity by using the smallest eligible model and bounded read-only delegation. Do not downgrade work requiring reliable edits, security judgment, or final verification.

## Commits
- Use Conventional Commits: `type(scope): summary`.
- One logical change per commit.
- Stay on the current branch for trivial documentation, comment, or simple fixes unless the user asks for a new branch.
- Create a feature branch for substantial, risky, review-bound, or protected-branch work.
- Never commit directly to protected branches.
- Never commit secrets.

## Language and Tools
- Use `uv` for Python. Never use `pip`, `virtualenv`, or `python -m venv`.
- Prefer Nushell for structured data. Use Bash for POSIX or system tasks.
- Reply in Japanese by default. Keep code, paths, commands, and identifiers unchanged.
- Use polite desu/masu style in Japanese output unless the user requests another tone.
- Prefer short, direct sentences in active voice; explain an acronym once at first use.
- All AI-readable files (AGENTS.md, SKILL.md, reference docs) are written in English; only user-facing output is Japanese.
- Keep responses concise.
- Only load extra files when strictly necessary for the task.

## Naming Conventions
- Files: snake_case (except README.md, SKILL.md, AGENTS.md)
- Variables/functions: snake_case
- Constants: UPPER_SNAKE
- Classes: PascalCase

**Last updated**: 2026-07
