---
name: git-workflow
description: Use before creating commits, branches, rebases, pull requests, or other repository-history changes.
---

# Git Workflow

- Follow the active repository's documented commit convention. Use Conventional
  Commits as a fallback when it defines none.
- Keep one logical change per commit.
- Stay on the current branch for trivial documentation, comment, or simple
  fixes unless the user requests a branch.
- Create a feature branch for substantial, risky, review-bound, or
  protected-branch work. Never commit directly to protected branches.
- Before committing, inspect `git status`, `git diff`, and `git log --oneline -10`.
  Stage only intended files and never commit secrets.
- Run all validation gates declared by the active repository.
- Do not commit while a required validation gate fails.
- Do not amend, force-push, or use interactive git commands unless explicitly
  requested.
