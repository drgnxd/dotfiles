---
name: independent-review
description: Use before implementing a non-trivial technical proposal — a design/architecture change, credential or secret generation, an operation on real data, or a change to another repository — after analysis is done and before writing the change.
---

# Independent Review

Two gates, in order, before implementation starts on a non-trivial technical proposal:

1. **Explicit approval of the concrete proposal.** Present the actual design or
   plan and wait for the user's explicit go-ahead. General topic approval
   ("yes, let's do X") is not approval of a specific design — if the design
   was never shown in file/diff form, or changed since it was discussed,
   present it before writing the change.
2. **Independent review by a context-free agent.** After approval, before
   touching files, send the proposal — a diff, plan, or design doc, not a
   paraphrase of it — to a fresh subagent (or a different model/vendor, where
   available) that has not seen this conversation. Give it the artifact plus
   the minimum standalone context needed to judge it. Incorporate its
   findings before implementing; if it finds nothing, say so explicitly
   rather than silently skipping the step. **The dispatch must be a real
   tool call visible in this session, not a claimed or paraphrased one** —
   asserting "reviewed, no issues" without an actual dispatch call is the
   specific failure this skill exists to prevent, not a hypothetical one.

## Why both gates

Self-review reliably misses one failure mode: over-generalizing an
established pattern into a structurally different situation without
re-verifying it still fits (e.g. reapplying a single-writer safe-write
pattern to a multi-file store where it silently no longer holds). A second
pass by someone who did not build the same mental model catches what the
author's own re-reading does not. The user's go-ahead does not substitute
for this — approval confirms intent, not correctness.

## Applies to

- Architecture or design changes (new services, storage schema, sync/backup
  patterns)
- Credential or secret generation
- Operations on real data (migrations, bulk edits, destructive commands)
- Changes to another repository

Treat a change as non-trivial by default when unsure. The main exceptions are
typo fixes, formatting, and doc-wording-only edits — everything else,
including a single commit- or PR-sized step of an already-approved
multi-step effort, defaults in. Approval count and commit count are not a
substitute for review count; review each such step separately, not just the
effort as a whole.

## Running the review

- Use the native fresh reviewer for the current tool, with only the diff/plan
  and minimum standalone background — not a summary written by the proposing
  session, which inherits its blind spots. In Claude Code, dispatch the
  `Review` subagent; it inherits the current main model and is read-only. In
  OpenCode, dispatch the `review-main` subagent; it uses the `build` model and
  permits only Read, Glob, and Grep.
- Ask for concrete failure scenarios, not general praise or a restatement of
  the proposal.
- A review is complete only when the fresh reviewer returns a non-empty result
  ending in `REVIEW_STATUS: pass` or `REVIEW_STATUS: findings`. A timeout,
  cancellation, malformed result, or tool failure leaves gate 2 unmet.
- Relay unresolved findings to the user before or alongside implementing the
  fix.
- If no subagent or independent model is reachable (rate-limited, offline,
  no eligible route per `model-routing`), do not treat the proposal as
  reviewed. Say so explicitly and let the user decide whether to proceed
  without gate 2 or wait.

## Bootstrapping

Authoring or editing this skill, or the rules file that points to it, is
itself a non-trivial change to another repository (`nix-config`, from most
callers' perspective) — both gates apply to changes here too. The first
version of this file could not self-trigger via the mechanism it defines
(the pointer to it in `global_rules.md` didn't exist yet), so that pass
relied on explicit human-requested review instead of the rule enforcing
itself. Every edit after that one no longer has that excuse.
