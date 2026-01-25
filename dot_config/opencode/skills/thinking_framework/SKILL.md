---
name: thinking_framework
description: Structured reasoning workflow for planning, verification, and robustness
---

# Thinking Framework

## Purpose

Provide a repeatable reasoning process that improves accuracy, safety, and completeness when solving engineering tasks.

## Core Principles

1. Decompose complex tasks into smaller, verifiable steps.
2. Explore multiple approaches before committing to one.
3. Validate outcomes and guard against edge cases.

## Rules/Standards

### Task Decomposition

- Identify inputs, outputs, and constraints before acting.
- Split work into sequential steps with clear dependencies.
- Track state changes explicitly (files modified, commands run).

### Multi-Path Exploration

- Compare at least two viable approaches for non-trivial tasks.
- Prefer the safest and simplest path that satisfies requirements.
- Avoid over-optimization when a clear baseline exists.

### Verification

- Cross-check changes against requirements and repository conventions.
- Validate assumptions using available files or tooling.
- Confirm that outputs are consistent with user intent.

### Counterfactual Checks

- Ask "what if this assumption is wrong" and adjust the plan.
- Identify failure modes and define fallback steps.

## Examples

Good:
- "Option A is faster to implement, Option B is safer. I will choose B because it minimizes production impact."

Bad:
- "I will proceed with the first approach without considering alternatives."

## Edge Cases

- If time is limited, document the chosen shortcut and its risk.
- If requirements conflict, highlight the conflict and ask for clarification.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References


- https://strategicmanagementinsight.com/tools/pdca-plan-do-check-act/ (Last accessed: 2026-01-26)
