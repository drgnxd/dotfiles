---
name: git_experts
description: Git workflow & collaboration best practices
---

# Git Experts

## Purpose
Safe, consistent Git practices for collaboration, review, history hygiene.

## Core Principles
1. Understandable, traceable history
2. Minimize risk on shared branches
3. Small, reviewable commits

## Rules

### Branching
- Feature branches for WIP
- Avoid direct commits to protected branches
- Rebase only on private branches

### Commits
- Each commit = single logical change
- Messages explain intent, not only actions
- Never commit secrets or generated artifacts

### Review & Sync
- `git status` & `git diff` before staging
- Pull/fetch before push to avoid conflicts
- Resolve conflicts locally, run tests after merges

## Examples

✅ "Feature branch + PR w/ concise summary"
❌ "Force-push to main to overwrite history"

## Edge Cases
- History rewrite needed: confirm no one depends on branch
- Sensitive data committed: rotate secrets, purge history carefully

See `COMMON.md`.

Refs: [git-commit](https://git-scm.com/docs/git-commit), [git-rebase](https://git-scm.com/docs/git-rebase), [contributing](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project) (2026-01-26)
