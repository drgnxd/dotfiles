---
name: practices
description: Engineering practice guidelines for Unix design, function boundaries, error handling, testing, code review, refactoring, and debugging workflows.
---

# Unix Philosophy

- Build small components that each do one thing well.
- Prototype quickly, then refine.
- Prefer portability when the tradeoff is reasonable.

# Function Design

- Keep one clear responsibility per function.
- Keep functions short and focused.
- Prefer pure functions unless side effects are required.

# Error Handling

- Provide explicit context in raised errors.
- Chain exceptions to preserve root causes.
- Never fail silently.
- Good pattern:

```python
try:
    return f.read()
except FileNotFoundError as e:
    raise RuntimeError(f"Missing {p}") from e
```

- Avoid broad catch-and-ignore patterns.

# Testing

- Keep tests fast and deterministic.
- Cover critical behavior and failure paths first.
- Optimize for readability and diagnosis quality.
- Test pyramid intent:
  - Unit tests: isolated logic.
  - Integration tests: component boundaries.
  - End-to-end tests: high-value user flows only.
- Avoid flaky tests and tests locked to implementation internals.

# Code Review

- Prioritize correctness, clarity, and maintainability.
- Check edge cases, error paths, input validation, and security posture.
- Validate naming quality and control-flow simplicity.
- Give actionable feedback (for example, "add null guard"), not vague criticism.

# Refactoring

- Preserve behavior unless requirements explicitly change.
- Make small, reversible steps.
- Validate each step with tests.
- Plan first: identify goals and avoid mixing feature work with refactor scope.
- Keep public APIs stable while refactoring internals.

# Debugging Workflow

- Follow sequence: reproduce -> isolate -> validate fix -> add/regress test.
- Use logs, metrics, traces, and temporary instrumentation.
- Continuously verify assumptions with evidence.
