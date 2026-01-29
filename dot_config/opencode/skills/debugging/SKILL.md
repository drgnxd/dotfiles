---
name: debugging
description: Efficient issue isolation techniques
---

# Debugging

Aim:
Structured approach to reproduce, isolate, fix defects.

Core:
1. Reproduce reliably before changes
2. Isolate minimal failing case
3. Validate fix, guard against regressions

Do:

### Reproduction
- Capture inputs, env, steps
- Reduce to smallest example

### Investigation
- Inspect logs, metrics, traces
- Add temp instrumentation if needed
- Verify assumptions w/ experiments

### Fix & Verify
- Smallest fix addressing root cause
- Add/update tests covering bug

## Examples

✅ "Create minimal failing test, fix underlying logic"
❌ "Guess a change, hope it works"

## Edge Cases
- Nondeterministic: add logging, time-based guards
- Production-only: simulate env when possible

Refs: See doc/refs.md
