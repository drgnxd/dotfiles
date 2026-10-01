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
  multi-step support, and `review-deep` only for explicitly high-impact review.
- Respect each agent's `steps` limit. Do not retry a failed route by switching
  providers or launching additional agents without a concrete reason.
- Select and retain models and reasoning effort by role, comparing task
  correctness and quality, actual billing or quota use, retries and human
  correction, latency and availability, tool compatibility, and role-specific
  constraints. Existing configuration, prior investment, and labels such as
  `independent-review` are not sufficient reasons to keep an incumbent.
- Compare cost using the user's actual billing path. Public API token prices do
  not establish Codex quota consumption; when actual usage cannot be measured,
  state that cost as unknown rather than inferring it from API prices.
- Use higher reasoning effort only where expected review value justifies its
  additional token use and latency. Reserve `xhigh` and `max` for complex or
  high-impact work; prefer a lower effort when the risk does not warrant the
  extra resource use. Measure actual quota use and review outcomes when
  available.
- Evaluate new models per role. For unresolved trade-offs, use a representative
  pilot and compare quality, material misses, false positives, retries, actual
  usage, latency, and reliability. Do not require an all-route benchmark to
  replace an incumbent when the user has made an explicit choice or reliable
  role-specific evidence establishes that it is dominated.
- Treat unavailable-model and usage-limit errors as stop conditions. Report the
  failure instead of silently changing provider, model, or effort.
