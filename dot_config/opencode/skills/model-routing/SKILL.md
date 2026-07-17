---
name: model-routing
description: Use when selecting subagents or claude_delegate, changing model assignments, handling provider capacity failures, or reviewing OpenCode routing.
---

# Model Routing

Maintain the model-to-agent routing in `dot_config/opencode/opencode.json`.
Treat model names, provider catalogs, and plan entitlements as volatile. Do not
assume that a previously available model can still be selected or that a newer
model is automatically better for every role.

## Goals

- Use ChatGPT Plus as the default path for work requiring reliable edits,
  planning, summaries, and reviews.
- Use verified free models only for low-risk, read-only, bounded work.
- Use GitHub Copilot where its plan and client expose a usable model. Do not
  force a Copilot model ID into OpenCode when the provider does not expose it.
- Keep the number of enabled models and providers minimal.
- Prefer a working, measured routing over a theoretical benchmark ranking.

## Required Investigation

Before changing a routing assignment, collect all of the following:

1. Read the current `dot_config/opencode/opencode.json` and inspect the active
   configuration with `opencode debug config`.
2. Check credentials with `opencode providers list`. Never print or read secret
   values from `auth.json`.
3. List the available models for every candidate provider with
   `opencode models <provider>`.
4. Consult the current official provider documentation for plan entitlement,
   model availability, usage limits, and supported reasoning controls.
5. Inspect local history with `opencode stats --days 30 --models` before
   replacing a model that has a meaningful sample size.
6. Run a minimal smoke test in the approved temporary directory for every new
   model. For an agentic candidate, require at least one read-only tool call.

Use a temporary config through `OPENCODE_CONFIG` or `OPENCODE_CONFIG_CONTENT`
for experiments. Do not change deployed files under `~/.config/opencode/`.

## Assignment Rules

Start from roles, not provider marketing labels.

| Role | Requirements | Assignment rule |
| --- | --- | --- |
| `build`, `general` | Reliable edits and tool loops | Use the best balanced, authenticated ChatGPT Plus model at medium effort. |
| `plan`, `review-deep` | Deep reasoning, high-value decisions | Use a stronger Plus model. `review-deep` must remain read-only. |
| `explore` | File search, grep, bounded read-only inspection | Prefer a verified free model with an explicit step limit. Escalate to a Plus model when results conflict or the search is broad. |
| `scout` | External documentation and upstream research | Use a reliable Plus lightweight model unless a free candidate has been tested for source quality. |
| `title`, `summary` | Preserve useful session state concisely | Use a reliable lightweight Plus model, not an unverified free model. |
| `compaction` | Preserve decisions and resume state | Use a reliable balanced Plus model at low effort. |

Current free-model policy:

- A free model may only be assigned to an agent that cannot edit the workspace.
- Keep a step limit on free-model agents.
- Do not use a free model for secrets, irreversible operations, security
  decisions, final reviews, or compaction.
- Remove a free assignment after repeated tool failures, fabricated paths, or
  material omissions. Report the evidence before changing it.

## Claude Code Delegation

The `claude_delegate` custom tool invokes the installed Claude Code CLI as a
separate, bounded read-only investigator. It is not an OpenCode provider or
agent model assignment.

- The primary agent is the default entry point. Do not require mode selection
  for ordinary conversation, curiosity-driven questions, research, or coding.
- Use kind `consultation` for a general independent opinion with no tools or
  workspace access. Use kind `repository` only for targeted read-only codebase
  inspection.
- Use it for independent second opinions, targeted repository inspection, and
  concise evidence-based summaries.
- Give it one specific task and the desired answer format. The primary agent
  remains responsible for evaluating its output and making any changes.
- The tool permits only `Read`, `Glob`, and `Grep`; never broaden this default
  to shell, edits, network access, or skip-permission flags.
- Do not delegate secrets, irreversible actions, implementation work, or tasks
  requiring interactive clarification.
- Report CLI quota or authentication failures directly. Do not retry in a loop
  or silently fall back to a different account.

## Capacity-Aware Selection

OpenCode model assignments are static for a running session. The primary agent
cannot replace itself dynamically, but it can select appropriate subagents and
whether to use `claude_delegate`.

1. Classify the task by risk, required capability, independence, and scope.
2. Check explicit availability signals already observed in the session. Treat
   `429`, usage-limit, authentication, and unavailable-model errors as facts;
   do not retry that route in a loop.
3. Use the smallest eligible route: free `explore` for bounded non-sensitive
   read-only inspection, `claude_delegate` for an independent read-only second
   opinion, and Plus agents for edits, high-impact reasoning, and final review.
4. Escalate free or delegated results that conflict, lack evidence, or affect a
   high-risk decision to the applicable Plus agent.
5. State the selected fallback when an explicit capacity failure changes the
   route.

`opencode stats` is historical usage telemetry only. It does not report the
remaining ChatGPT Plus or Claude Pro quota. Never infer quota from token counts
or spend a probe request solely to measure remaining capacity.

GitHub Copilot policy:

- Copilot Student may offer unlimited inline completions while restricting
  chat/agent access to Auto model selection.
- If `opencode models github-copilot` exposes no selectable model, keep Copilot
  in its editor integration and do not assign it to an OpenCode agent.
- If selectable models become available, test them first. Use Auto only through
  a Copilot client that supports it; do not guess an internal picker model ID.

## Change Procedure

1. State the proposed routing table, expected benefit, and confidence level.
2. Keep existing providers and models unless a concrete replacement is verified.
3. Update only `dot_config/opencode/opencode.json` unless a distinct agent
   prompt is needed.
4. Preserve `$schema`, existing provider options, permissions, and unrelated
   plugins.
5. Use `enabled_providers` and provider whitelists to expose only the selected
   routing models.
6. Validate with:

```sh
uv run --directory dot_config/opencode python validate_opencode_setup.py
OPENCODE_CONFIG="$PWD/dot_config/opencode/opencode.json" opencode debug config
OPENCODE_CONFIG="$PWD/dot_config/opencode/opencode.json" opencode debug agent <agent>
git diff --check
```

7. Smoke-test each changed model through the source config. A model resolving
   in `debug agent` is necessary but not sufficient.
8. Apply the Nix configuration and restart OpenCode. Config-time changes are
   not hot-reloaded.

## Reporting

Report:

- Provider and model availability actually observed.
- The final role-to-model table and reasoning variants.
- What was smoke-tested and what remains unverified.
- Subscription or credit implications.
- Whether the user needs to rebuild and restart OpenCode.

Do not claim cost savings or quality improvements without a measured local
comparison. State selection bias and small sample sizes explicitly.
