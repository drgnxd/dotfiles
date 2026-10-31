---
name: git-workflow
description: Use before the first file edit or Git write in each repository for each task, whatever the task size. Not for read-only inspection or directories outside a Git work tree.
---

# Git Workflow

## Environment and preparation

- Resolve `git rev-parse --show-toplevel`, read repository instructions and the commit convention, and inspect relevant hooks before writes.
- Use the repository's documented shell environment, verify it loaded, and inspect an untrusted `.envrc` against the trusted version before allowing it.
- Use a fresh detached worktree for each task or revision, never a task branch or a shared worktree.
  Record the exact local `main` OID and use `git worktree add --detach <path> <oid>` at a unique path under `${XDG_STATE_HOME:-~/.local/state}/<repo>/worktrees/`, never under a temporary directory.
- Immediately record the creating session with `wtctl record --path <worktree> --session <id>`, or `--unknown` if the session is unavailable.
  Use `wtctl query --path <worktree> --json` to inspect provenance.
  A record is self-reported provenance, not proof of ownership or authorization; missing, unknown, conflicting, or unverifiable ownership fails closed.
  If recording fails, preserve the worktree and stop rather than edit or remove it.
  Verify the exact path, detached HEAD, base OID, registration, and two-way `.git`/Git-admin pointers before editing.
- Check repository-specific scheduled and non-cooperating writers and maintain the required locks and quiescence over the complete operation, including Git-annex shared state where applicable.
  Unrelated isolated worktrees are not by themselves blockers.
- A new repository with unborn `main` may receive only the minimal seed README and initial commit before creating a task worktree; do not use this exception for implementation or unrelated changes.
- If there are staged, unstaged, untracked, or ignored changes of unclear ownership, do not mutate the worktree and coordinate instead.

## Integration and cleanup

- Only the integrator may integrate or remove worktrees.
  Hold the repository's `main-integration.lock` from inspection through integration and cleanup, verify lock ownership, and stop on an existing lock; never remove another writer's lock.
  The lock is the atomic `mkdir` of `main-integration.lock` in the Git common directory; create its `owner` file exclusively with a unique token, process ID, and host on separate lines, and release only after verifying the same token.
  Coordinate any other repository-specific locks with their owners and stop if mutual exclusion cannot be established.
  Verify the exact integration checkout and target, clean tracked and untracked state, hooks, external writers, and current `main` OID before mutating it.
- When `main` is an ancestor of the verified task tip, integrate using `git merge --ff-only --no-overwrite-ignore <task-oid>` in the integration checkout, then verify the expected OID and checkout state.
  Do not use force, bypass hooks or guards, or mutate the task checkout to repair `main`.
- **Integration contract needed:** when `main` has advanced divergently, or an integration/cleanup fails partway, preserve all worktrees and stop.
  Native Git alone does not define the prior atomic integration-and-cleanup, conflict-resolution, or recovery protocol; establish and review an explicit contract before proceeding instead of guessing commands or bypassing a refusal.
- Before removal inspect exact path and two-way Git metadata, creator provenance and independently established ownership, process activity, locks, integration status, and all tracked, untracked, and ignored data.
  `git worktree remove` can delete ignored files: preserve unclear or user-owned data and obtain explicit authorization for any non-regenerable data deletion.
  Do not remove another session's worktree without explicit authorization, including when its owner is dead; a provenance record alone does not authorize removal.
  For an integrated clean worktree with only verified disposable ignored files and all checks satisfied, use `git worktree remove <exact-path>` without `--force` and verify removal with `git worktree list --porcelain`.
  Do not prune, delete Git metadata manually, or discard dirty or unintegrated work without a separately specified, authorized preservation and recovery procedure.
  The worktree guard is best-effort and does not verify ownership, quiescence, ignored-file inventory, or integration: an allowed command is not authorization to remove a worktree.
  If provenance is unknown or the installed guard cannot recognize a legacy worktree, preserve it and stop rather than bypassing the guard.
- Reconcile all worktrees created for the task, including delegated worktrees and revisions, from task records and Git's worktree list; report retained entries and reasons.
  Do not infer task linkage from names alone.
- Do not push unless explicitly requested; never force-push or rewrite history without explicit authorization.

## Parallel work

- The parent creates and records each detached worktree before delegation, gives the exact path, base and scope, and assigns disjoint paths.
  A delegated writer never creates or removes worktrees, integrates, updates refs, or pushes.
- Keep outputs inside the assigned worktree and serialize unavoidable shared resources with an owned lock.
  Do not remove another writer's lock or use a shared stash.

## Commits and verification

- Before committing inspect status, staged and unstaged diffs, and the repository's commit convention; stage only task-owned files and never commit secrets.
- Run repository-required validation and hooks, then commit coherent changes.
  Do not use `--no-verify`, disable hooks, or bypass a guard or permission refusal.
- Report commit OIDs, verification, integration and cleanup outcomes, and all unresolved work.
