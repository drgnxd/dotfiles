---
name: model-routing
description: Use when routing models or delegating.
---

# Runtime Routing

- Keep the primary agent as the default entry point and make routing decisions
  without asking the user to select a mode.
- Keep edits, secrets, security decisions, irreversible actions, and final
  verification on the primary authenticated model.
- For an `independent-review` gate in OpenCode, dispatch `review-main` only.
  It is the fresh, context-free, read-only reviewer using the main GPT model;
  do not substitute `claude_delegate`, `review-deep`, or any other reviewer.
- Preserve the longer-window ChatGPT budget. Use Claude Sonnet only for bounded
  non-review consultations or targeted read-only repository inspection. Do not
  delegate work that needs the primary conversation context, current web
  evidence, edits, or final accountability.
- Use `claude_delegate` kind `consultation` for tool-free non-review questions
  and kind `repository` for targeted non-review inspection. Use its result
  directly when sufficient instead of creating an additional premium-model
  subtask.
- `claude_delegate` always uses Claude Sonnet. Do not expose model selection or
  use another Claude model.
- Select its effort by task: `low` for straightforward questions or narrow
  lookup, `medium` for normal analysis and repository inspection, and `high`
  only when complex reasoning or decision impact justifies it. Do not use high
  effort for routine work.
- When an eligible Claude Sonnet delegation is available for non-review work,
  use it before free agents. Escalate incomplete, conflicting, or high-impact
  results.
- Keep every delegation bounded. Do not use Claude for repeated retries,
  background loops, or broad speculative exploration.
- Treat `429`, usage-limit, authentication, and unavailable-model errors as
  capacity facts. When Claude is unavailable, use a free eligible route before
  consuming ChatGPT capacity; use ChatGPT when no eligible alternative exists.
  When ChatGPT is unavailable, Claude remains eligible for non-review work.
- Historical usage statistics do not reveal remaining subscription quota, so do
  not infer capacity from token counts or send quota probes.
