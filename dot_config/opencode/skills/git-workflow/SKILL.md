---
name: git-workflow
description: Use before creating commits, branches, rebases, pull requests, or other repository-history changes.
---

# Git Workflow

- Before any Git write, resolve the target repository with `git rev-parse
  --show-toplevel`. Read its `AGENTS.md`/contribution instructions and documented
  commit convention (check its root and `docs/`) as the commit contract. Global
  defaults never impose a commit-message language or format on that contract.
- Follow the target's documented commit convention. If none exists, match the
  style established in `git log --oneline -20`; fall back to Conventional
  Commits only when neither source establishes a convention.
- Keep one logical change per commit.
- Stay on the current branch for trivial documentation, comment, or simple
  fixes unless the user requests a branch.
- Create a feature branch for substantial, risky, review-bound, or
  protected-branch work. Never commit directly to protected branches.
- Before committing, inspect `git status`, `git diff`, and `git log --oneline -10`.
  Stage only intended files and never commit secrets.
- Run the target repository's commit-message validation command or installed
  `commit-msg` hook; do not use `--no-verify` to bypass it.
- Run all validation gates declared by the active repository.
- Do not commit while a required validation gate fails.
- Do not amend, force-push, or use interactive git commands unless explicitly
  requested.
