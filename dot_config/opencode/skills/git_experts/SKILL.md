---
name: git_experts
description: Git workflow & collaboration best practices
---

# Git Experts

Aim:
Safe, consistent Git practices for collaboration, review, history hygiene.

Core:
1. Understandable, traceable history
2. Minimize risk on shared branches
3. Small, reviewable commits

Do:

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

Refs: See doc/refs.md
