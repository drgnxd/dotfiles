---
name: thinking_framework
description: Structured reasoning workflow for planning, verification, robustness
---

# Thinking Framework

Aim:
Repeatable reasoning process for accuracy, safety, completeness in engineering tasks.

Core:
1. Decompose complex tasks into smaller, verifiable steps
2. Explore multiple approaches before committing
3. Validate outcomes, guard against edge cases

Do:

### Task Decomposition
- Identify inputs, outputs, constraints before acting
- Split work into sequential steps w/ clear dependencies
- Track state changes explicitly (files modified, commands run)

### Multi-Path Exploration
- Compare ≥2 viable approaches for non-trivial tasks
- Prefer safest, simplest path satisfying requirements
- Avoid over-optimization when clear baseline exists

### Verification
- Cross-check changes against requirements & repo conventions
- Validate assumptions using available files or tooling
- Confirm outputs consistent w/ user intent

### Counterfactual Checks
- Ask "what if this assumption is wrong" and adjust plan
- Identify failure modes, define fallback steps

## Examples

✅ "Option A faster, Option B safer. Choose B to minimize production impact."
❌ "Proceed w/ first approach w/o considering alternatives"

## Edge Cases
- Time limited: doc chosen shortcut & risk
- Requirements conflict: highlight conflict, ask clarification

Refs: See doc/refs.md
