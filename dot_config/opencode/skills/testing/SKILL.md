---
name: testing
description: Testing strategy & coverage guidelines
---

# Testing

## Purpose
Balanced testing strategy for confidence w/o excessive cost.

## Core Principles
1. Fast, deterministic tests for core logic
2. Cover critical paths & failure modes
3. Readable, maintainable tests

## Rules

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

See `COMMON.md`.

Refs: [Test pyramid](https://martinfowler.com/articles/practical-test-pyramid.html), [bliki](https://martinfowler.com/bliki/TestPyramid.html), [strategies](https://web.dev/articles/ta-strategies) (2026-01-26)
