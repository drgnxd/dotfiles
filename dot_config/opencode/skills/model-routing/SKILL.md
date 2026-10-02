---
name: model-routing
description: Use when routing models or delegating.
---

# Runtime Routing

Agent names below (`review-main`, `explore`, `general`, `review-deep`) are
OpenCode's. In another client, keep every rule here and map the agent names via
`references/<client>.md`; if no such file exists, report that instead of guessing
a route.

- For model inference and delegation use only models and subagents provided by
  the active client. Never invoke or delegate to an external AI model, client,
  CLI, or API.
- In OpenCode, non-AI MCP tools remain available only when their project skill
  explicitly requires them.
- Keep the primary agent as the default entry point and route without asking the
  user to select a mode.
- Keep edits, secrets, security decisions, irreversible actions, and final
  verification on the primary authenticated model.
- For an `independent-review` gate, dispatch `review-main` only; it is the
  fresh, context-free, read-only reviewer. Do not substitute `review-deep`.
- Use `explore` for bounded read-only discovery, `general` for bounded
  multi-step support, and `review-deep` only for explicitly high-impact review.
- Treat unavailable-model and usage-limit errors as stop conditions: report the
  failure. Do not retry a failed route by switching provider, model, or effort,
  or by launching additional agents, without a concrete reason.
- Per-role models and efforts are pinned in `opencode.json` and enforced by
  `validate_opencode_setup.py`; the criteria for choosing them are measured
  quality, retries, latency, and actual billing or quota use. State cost as
  unknown when it cannot be measured, and do not keep a model merely because it
  is the incumbent. Reserve `xhigh` and `max` for complex or high-impact work.
- Add a context or output limit override only for a mismatch verified against
  the official model specification, and recheck it after catalog updates.
