---
name: testing
description: Testing strategy & coverage guidelines
---

# Testing

Aim:
Balanced testing strategy for confidence w/o excessive cost.

Core:
1. Fast, deterministic tests for core logic
2. Cover critical paths & failure modes
3. Readable, maintainable tests

Do:

### Test Types
- Unit tests for isolated logic
- Integration tests for cross-component behavior
- E2E tests limited to high-value flows

### Quality
- Avoid flaky tests; fix or quarantine quickly
- Assert outcomes, not implementation details

## Examples

✅ "Add unit tests for input validation & error paths"
❌ "Only test happy path, ignore failures"

## Edge Cases
- External services required: use mocks or test doubles
- Time-dependent logic: control clock in tests

Refs: See doc/refs.md
