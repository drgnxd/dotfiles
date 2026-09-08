---
name: model-routing
description: Use when routing models or delegating.
---

# Runtime Routing

- Use only OpenCode-provided models and tools for model inference. Never invoke
  or delegate to an external AI model, client, CLI, or API. Non-AI MCP tools
  remain available only when their project skill explicitly requires them.
- Keep the primary agent as the default entry point and make routing decisions
  without asking the user to select a mode.
- Keep edits, secrets, security decisions, irreversible actions, and final
  verification on the primary authenticated model.
- For an `independent-review` gate, dispatch `review-main` only. It is the
  fresh, context-free, read-only reviewer; do not substitute `review-deep`.
- Use `explore` for bounded read-only discovery, `general` for bounded
  multi-step support, and `review-deep` only for explicitly high-risk review.
- Respect each agent's `steps` limit. Do not retry a failed route by switching
  providers or launching additional agents without a concrete reason.
- When a new frontier model becomes available, trial it only on an explicitly
  deep route such as `review-deep` or a high-effort planning path. Do not
  replace every agent at once: keep the proven model for build work and the
  low-effort model for exploration, compaction, title, and summary tasks until
  a fixed benchmark shows a quality benefit worth the added resource use.
- Treat unavailable-model and usage-limit errors as stop conditions. Report the
  failure instead of silently changing provider, model, or effort.
