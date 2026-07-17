---
name: model-routing
description: Use when selecting subagents or claude_delegate, changing model assignments, handling provider capacity failures, or reviewing OpenCode routing.
---

# Runtime Routing

- Keep the primary agent as the default entry point. Answer ordinary questions
  directly; inspect the workspace or research current facts before delegating.
- Delegate only when an independent perspective materially improves the answer.
  Give one bounded task and retain responsibility for evaluating the result.
- Keep edits, secrets, security decisions, irreversible actions, and final
  verification on the primary authenticated model.
- Use lower-cost or free models only for bounded, non-sensitive, read-only
  work. Escalate incomplete, conflicting, or high-impact results.
- Use `claude_delegate` kind `consultation` for a tool-free independent opinion
  and kind `repository` only for targeted read-only inspection.
- Treat `429`, usage-limit, authentication, and unavailable-model errors as
  capacity facts. Select an eligible fallback; do not retry in a loop.
- Historical usage statistics do not reveal remaining subscription quota.
