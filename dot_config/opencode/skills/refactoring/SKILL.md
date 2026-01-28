---
name: refactoring
description: Safe, incremental improvement strategies
---

# Refactoring

## Purpose
Improve code structure while preserving behavior.

## Core Principles
1. Preserve existing behavior & contracts
2. Small, reversible changes
3. Use tests & tooling to validate

## Rules

### Planning
- Identify goal: readability, reuse, or performance
- Don't mix refactors w/ new features

### Execution
- Refactor in small steps w/ checkpoints
- Run tests after each significant change
- Keep public APIs stable when possible

## Examples

✅ "Extract function, update tests, replace call sites"
❌ "Rewrite entire module w/o tests"

## Edge Cases
- Tests missing: add characterization tests first
- High-risk areas: coordinate w/ reviewers before large refactors

See `COMMON.md`.

Refs: [Fowler Refactoring](https://martinfowler.com/books/refactoring.html), [catalog](https://refactoring.com/catalog/), [guru](https://refactoring.guru/refactoring) (2026-01-26)
