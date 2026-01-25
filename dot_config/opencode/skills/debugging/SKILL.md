---
name: debugging
description: Debugging techniques for isolating issues efficiently
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Debugging

## Purpose

Provide a structured approach to reproduce, isolate, and fix defects.

## Core Principles

1. Reproduce the issue reliably before making changes.
2. Isolate the minimal failing case.
3. Validate the fix and guard against regressions.

## Rules/Standards

### Reproduction

- Capture inputs, environment, and steps to reproduce.
- Reduce the case to the smallest example.

### Investigation

- Inspect logs, metrics, and traces.
- Add temporary instrumentation if needed.
- Verify assumptions with targeted experiments.

### Fix and Verify

- Implement the smallest fix that addresses the root cause.
- Add or update tests to cover the bug.

## Examples

Good:
- "Create a minimal failing test case and fix the underlying logic."

Bad:
- "Guess a change and hope it works."

## Edge Cases

- For nondeterministic issues, add logging and time-based guards.
- For production-only failures, simulate the environment when possible.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://sre.google/sre-book/effective-troubleshooting/
- https://sre.google/resources/book-update/effective-troubleshooting/
- https://komodor.com/blog/troubleshooting-vs-debugging/
