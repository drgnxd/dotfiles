---
name: code_review
description: Code review focus & quality checklist
---

# Code Review

Aim:
Consistent checklist for effective, fair code reviews.

Core:
1. Focus: correctness, clarity, maintainability
2. Be specific & actionable
3. Prioritize risks & user impact

Do:

### Correctness
- Validate edge cases & error handling
- Confirm data validation & security

### Readability
- Clear, consistent naming
- Simple control flow > deeply nested logic

### Tests
- New behavior covered by tests
- Tests deterministic & scoped

## Examples

✅ "This can return null; add guard or update type"
❌ "Looks bad" (no actionable detail)

## Edge Cases
- Large changes: suggest splitting into smaller PRs
- Performance-critical: ask for benchmarks

Refs: See doc/refs.md
