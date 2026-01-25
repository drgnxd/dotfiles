---
name: git_experts
description: Git workflow and collaboration best practices
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Git Experts

## Purpose

Establish safe, consistent Git practices for collaboration, review, and history hygiene.

## Core Principles

1. Keep history understandable and traceable.
2. Minimize risk when changing shared branches.
3. Prefer small, reviewable commits.

## Rules/Standards

### Branching

- Use feature branches for work in progress.
- Avoid direct commits to protected branches.
- Rebase only on private branches.

### Commits

- Ensure each commit is scoped to a single logical change.
- Write messages that explain intent, not only actions.
- Do not commit secrets or generated artifacts.

### Review and Sync

- Run `git status` and `git diff` before staging.
- Pull or fetch before pushing to avoid conflicts.
- Resolve conflicts locally and run tests after merges.

## Examples

Good:
- "Use a feature branch and open a PR with a concise summary."

Bad:
- "Force-push to main to overwrite history."

## Edge Cases

- If history rewrite is required, confirm no one else depends on the branch.
- If sensitive data was committed, rotate secrets and purge history carefully.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://git-scm.com/docs/git-commit
- https://git-scm.com/docs/git-rebase
- https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project
