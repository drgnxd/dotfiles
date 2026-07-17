---
name: git-workflow
description: Use before creating commits, branches, rebases, pull requests, or other repository-history changes.
---

# Git Workflow

- Use Conventional Commits: `type(scope): summary`.
- Keep one logical change per commit.
- Stay on the current branch for trivial documentation, comment, or simple
  fixes unless the user requests a branch.
- Create a feature branch for substantial, risky, review-bound, or
  protected-branch work. Never commit directly to protected branches.
- Before committing, inspect `git status`, `git diff`, and `git log --oneline -10`.
  Stage only intended files and never commit secrets.
- Run all applicable repository validation gates. In this repository, run
  `uv tool run detect-secrets scan --baseline .secrets.baseline`, confirm that
  its timestamp-only drift is not staged, and do not commit while a required
  gate fails.
- Do not amend, force-push, or use interactive git commands unless explicitly
  requested.
