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
  Keep lifecycle operations on that worktree quiescent throughout each record or query; use the same absolute `XDG_STATE_HOME` for both commands and the guard, or consistently leave it unset.
  A record, including `unknown`, is self-reported provenance, not proof of ownership or authorization.
  Independently establish ownership and authority from the current creation or delegation records; missing, conflicting, or unverifiable ownership fails closed even when provenance is known.
  `unknown` provenance is usable only when that independent ownership evidence is sufficient; otherwise preserve the worktree and stop.
  If recording fails, preserve the worktree and stop rather than edit or remove it; the record may already have committed, so query it before any further action and never blindly retry.
  Verify the exact path, detached HEAD, base OID, registration, and two-way `.git`/Git-admin pointers before editing.
- Check repository-specific scheduled and non-cooperating writers and maintain the required locks and quiescence over the complete operation, including Git-annex shared state where applicable.
  Unrelated isolated worktrees are not by themselves blockers.
- A new repository with unborn `main` may receive only the minimal seed README and initial commit before creating a task worktree; do not use this exception for implementation or unrelated changes.
- If there are staged, unstaged, untracked, or ignored changes of unclear ownership, do not mutate the worktree and coordinate instead.

## Existing worktrees and legacy state

- Before recording an existing registered worktree, verify its exact canonical root and two-way Git metadata, then query its current provenance with `wtctl query --path <worktree> --json`.
  If it is unrecorded, independently verify the original creator session from contemporaneous creation records and use `wtctl record --path <worktree> --session <id>` only when that evidence establishes the creator.
  Otherwise use `wtctl record --path <worktree> --unknown`; do not infer the creator from the current process, worktree name, a later owner, or an unverified legacy marker.
  The record is insert-only: do not guess, overwrite, delete, or re-record an existing or conflicting provenance entry; preserve it and resolve discrepancies through a supported documented procedure or stop.
  Recording `--unknown` does not establish ownership or authorize edits, recovery, or deletion.
- Preserve existing legacy markers, Git administration state, worktree locks, snapshots, refs, and quarantines; the current provenance-only `wtctl` neither interprets nor migrates them.
  Do not remove or alter legacy markers, locks, quarantines, or their contents manually, and do not use native Git removal as a substitute for a refused legacy recovery.
  A legacy worktree lock or unresolved quarantine is a stop condition for ordinary cleanup until its supported recovery has completed.
- Keep the previous `wtctl` binary and its matching documentation available for legacy recovery and artifact-quarantine procedures.
  Before invoking it, identify its exact executable path, version or build identity, and documented capabilities, and verify that its documentation supports the specific legacy state and operation; do not assume the current `wtctl` implements old lifecycle commands.
  Follow that version's documented supported recovery and required checks, exact-target authorization, locks, and external-writer and Git-annex quiescence; inspect the affected data and preserve anything unclear.
  Never bypass a guard, hook, permission, lock, or safety refusal, and never use unsupported deletion or manual quarantine cleanup as a fallback.
  If the previous binary, matching documentation, identity, or applicable safe procedure cannot be established, preserve all state and report the blocker rather than guessing.

## Integration and cleanup

- Only the integrator may integrate or remove worktrees.
  Hold the repository's `main-integration.lock` from inspection through integration and cleanup, verify lock ownership, and stop on an existing lock; never remove another writer's lock.
  The lock is the atomic `mkdir` of `main-integration.lock` in the Git common directory; create its `owner` file exclusively with a unique token, process ID, and host on separate lines, and release only after verifying the same token.
  Coordinate any other repository-specific locks with their owners and stop if mutual exclusion cannot be established.
  Verify the exact integration checkout and target, clean tracked and untracked state, hooks, external writers, and current `main` OID before mutating it.
- When `main` is an ancestor of the verified task tip, integrate using `git merge --ff-only --no-overwrite-ignore <task-oid>` in the integration checkout, then verify the expected OID and checkout state.
  Do not use force, bypass hooks or guards, or mutate the task checkout to repair `main`.
- For divergent `main`, while maintaining the same lock and quiescence, pin the current `main` and task OIDs and create a fresh detached integration worktree at that exact `main` OID using the creation and provenance procedure above.
  Before merging, persist a task-owned integration record outside the worktrees containing their exact paths, the pinned OIDs, the intended target ref, integration worktree identity, pre-merge cleanliness and ignored-file inventory, and current phase; retain it until reconciliation is complete.
  In that integration worktree run `git merge --no-ff --no-commit <task-oid>`, allowing repository hooks and signing policy to operate normally.
  Resolve conflicts only there, inspect the staged result, run the repository's relevant verification, and commit with the required message and hooks.
  A merge conflict is not permission to bypass a hook, guard, or safety refusal.
  Verify the resulting commit has the pinned `main` and task OIDs as parents, the integration worktree is clean, and tests pass; record the merge OID and phase before proceeding.
  Recheck under the lock that the integration checkout is clean and still has exactly the pinned `main` OID, that the target ref has not moved, and that external-writer quiescence persists; then fast-forward it using `git merge --ff-only --no-overwrite-ignore <merge-oid>`.
  Verify the target ref, checkout, task ancestry, and merge ancestry after the fast-forward, update the record, and only then consider cleanup under the rules below.
  If the task tip is already an ancestor of `main`, verify that fact and skip the merge rather than create a redundant merge commit.
- For interruption or a failed integration, preserve the record, worktrees, refs, index, merge state, and data; never reset, clean, stash, abort, manually edit Git metadata, or remove a worktree as automatic recovery.
  Reacquire the same lock without taking another writer's lock, establish quiescence, independently verify identity and ownership, and compare the record with `main`, both pinned OIDs, all worktree statuses including ignored paths, and Git's merge state.
  If the target already equals the recorded verified merge OID, repeat the integration post-checks and then follow the normal cleanup checks.
  If `main` remains pinned and the integration worktree has the recorded pending merge with `HEAD` and `ORIG_HEAD` equal to pinned `main` and `MERGE_HEAD` equal to the task OID, inspect all changes and continue conflict resolution and verification as above only when their ownership and origin are clear.
  If interrupted after the merge commit but before recording its OID, accept the integration worktree's current commit only after verifying its exact two parents are the pinned OIDs, no merge state remains, the checkout is clean, all changes belong to the integration, and required verification passes again; then record that OID before proceeding.
  If a recorded verified merge commit exists and `main` remains pinned, repeat its parent, cleanliness, verification, and pre-fast-forward checks before retrying the fast-forward.
  If the record proves merge has not started, `main` is still pinned, and the integration worktree and merge state exactly match the recorded clean pre-merge state, restart the merge.
  For any missing record, changed target, mismatched merge state, ambiguous data, safety refusal, or other unverified partial state, stop and report it without deletion or bypass; obtain a separately reviewed recovery plan before further mutation.
- Before removal inspect exact path and two-way Git metadata, creator provenance and independently established ownership, process activity, locks, integration status, and all tracked, untracked, and ignored data.
  `git worktree remove` can delete ignored files: preserve unclear or user-owned data and obtain explicit authorization for any non-regenerable data deletion.
  Do not remove another session's worktree without explicit authorization, including when its owner is dead; a provenance record alone does not authorize removal.
  For an integrated clean worktree with only verified disposable ignored files and all checks satisfied, use `git worktree remove <exact-path>` without `--force` and verify removal with `git worktree list --porcelain`.
  Do not prune, delete Git metadata manually, or discard dirty or unintegrated work without a separately specified, authorized preservation and recovery procedure.
  The worktree guard is best-effort and does not verify ownership, quiescence, ignored-file inventory, or integration: an allowed command is not authorization to remove a worktree.
  If ownership is unknown or the installed guard cannot recognize a legacy worktree, preserve it and stop rather than bypassing the guard.
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
