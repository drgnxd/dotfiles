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
- Prefer `bun --no-env-file --config=/dev/null <this-skill-dir>/scripts/wt-session.ts create <name> [--base <rev>]` to create the worktree; always pass both flags, because plain `bun` loads `.env` and runs `bunfig.toml` preload scripts from the repository you are working in; keep `<this-skill-dir>` an absolute path, and if the `bun` on `PATH` rejects the flags, stop instead of dropping them.
  It resolves the base (default `refs/heads/main`) to an OID, runs `git worktree add --detach` at a unique path under `${XDG_STATE_HOME:-~/.local/state}/<repo>/worktrees/`, verifies the detached HEAD and two-way `.git`/Git-admin pointers, and writes a write-once `session-owner` record in the worktree's Git administration directory.
  The record holds the creating tool, session ID, base OID, canonical path, and creation time.
  The tool and session ID come from `OPENCODE_SESSION_ID`, `CLAUDE_CODE_SESSION_ID`, or `COPILOT_AGENT_SESSION_ID`; the helper records `unknown` when none is set and refuses to guess when multiple are set.
  `git worktree remove` and `git worktree prune` delete the record with the worktree; `git worktree move` keeps it but invalidates it because it names the original path.
  If the helper reports that a worktree exists but is unrecorded and preserved, including after a failed `git worktree add`, preserve it, do not retry blindly, and stop; never write, copy, or edit a `session-owner` file by hand.
- `wt-session.ts owner <worktree-root>` (same `bun` flags) compares the record with the current session and exits 0 for `mine`, 1 for `other`, 3 for `unknown`, 4 for `unrecorded`, and 2 for an error; accept `mine` only when the exit status is 0 and the output contains the line `status=mine`.
  `mine` means only that the same top-level tool session ID created the worktree: it does not identify one agent or task, and subagents or sibling agents that share the session environment all read each other's worktrees as `mine`.
  A worktree recorded as `unknown` never reads as `mine`, and a stale session ID exported in a long-lived shell yields wrong results.
  The record is supporting evidence only: it never replaces the creation and delegation evidence below and never authorizes removal or integration.
  Anything other than `mine`, or a helper error, leaves ownership unverified, so preserve the worktree and stop; the only exception is removal under the `--force` waiver in the removal bullet below.
- Retain exact current-task creation and delegation evidence identifying the creator, path, base OID, and task scope in the active task context.
  Verify registration with `git worktree list --porcelain`, status with `git status --short --untracked-files=all` and an ignored-file inventory, and verify the exact canonical path, detached HEAD, base OID, and two-way `.git`/Git-admin pointers before editing.
  Independently establish ownership and authority from contemporaneous creation and delegation evidence; Git registration, a worktree name, and historical provenance records alone are not proof of ownership or authorization.
  If identity or ownership is missing, conflicting, or unverifiable, preserve the worktree and stop.
- Check repository-specific scheduled and non-cooperating writers and maintain the required locks and quiescence over the complete operation, including Git-annex shared state where applicable.
  Unrelated isolated worktrees are not by themselves blockers.
- A new repository with unborn `main` may receive only the minimal seed README and initial commit before creating a task worktree; do not use this exception for implementation or unrelated changes.
- If there are staged, unstaged, untracked, or ignored changes of unclear ownership, do not mutate the worktree and coordinate instead, except for removal under the `--force` waiver in the removal bullet below.

## Existing worktrees and legacy state

- Before acting on an existing registered worktree, verify its exact canonical root, registration, status, and two-way Git metadata, and independently establish ownership and authority from contemporaneous creation and delegation evidence.
  Do not infer the creator from the current process, worktree name, a later owner, or an unverified legacy marker; preserve the worktree and stop if ownership is unknown or mismatched, except for removal under the `--force` waiver in the removal bullet below.
  Preserve existing provenance records, generation markers, databases, and journals without modification.
- Worktrees created by the retired `wtctl` (locked with an `agent-task` reason, or recorded in its provenance database) are ordinary Git worktrees.
  Their markers and records are historical evidence only and never establish ownership; treat them as another session's worktrees.
  Remove one only with explicit user authorization naming the exact worktree and its inventory, using `git worktree unlock <exact-path>` and then `git worktree remove <exact-path>`; if Git refuses because of modified, staged, untracked, merge-state, or submodule content, apply the `--force` waiver in the removal bullet below.
  Do not delete markers, locks, or Git administration data by hand.

## Integration and cleanup

- Only the integrator may integrate or remove worktrees.
  Hold the repository's `main-integration.lock` from inspection through integration and cleanup, verify lock ownership, and stop on an existing lock; never remove another writer's lock.
  Resolve the canonical integration checkout root and Git common directory with `git -C <verified-integration-checkout> rev-parse --path-format=absolute --show-toplevel` and `git -C <verified-integration-checkout> rev-parse --path-format=absolute --git-common-dir` before changing cwd, and verify that they identify the intended repository.
  Resolve the lock path once as `<absolute-git-common-dir>/main-integration.lock` for that verified repository, because the plain output can be relative to the `-C` directory, which `-C` does not make the shell's working directory, and a relative `mkdir` locks the wrong repository.
  The lock is the atomic `mkdir` of that path; create its `owner` file exclusively with a unique token, process ID, host, canonical repository root, absolute Git common directory, and absolute lock path on separate lines.
  Use that stored absolute path for every lock operation (`mkdir`, `owner` file, token check, release), never a relative one, so a later `cd` cannot redirect it.
  Before releasing the lock, verify that the owner file is a regular non-symlink file and exactly matches the recorded token, process ID, host, canonical repository root, absolute Git common directory, and absolute lock path.
  Perform final repository and worktree reconciliation while holding the lock; if any final check fails, do not release the lock, leave it intact, mark the task incomplete, and report its captured absolute path.
  Release the lock only after final reconciliation succeeds, then verify that the captured lock path is absent as both a filesystem entry (`! -e`) and a symlink (`! -L`).
  Coordinate any other repository-specific locks with their owners and stop if mutual exclusion cannot be established.
  Verify the exact integration checkout and target, clean tracked and untracked state, hooks, external writers, and current `main` OID before mutating it.
- When `main` is an ancestor of the verified task tip, integrate using `git merge --ff-only --no-overwrite-ignore <task-oid>` in the integration checkout, then verify the expected OID and checkout state.
  Do not use force, bypass hooks or guards, or mutate the task checkout to repair `main`.
- For divergent `main`, while maintaining the same lock and quiescence, pin the current `main` and task OIDs and create a fresh detached integration worktree at that exact `main` OID using the creation and ownership-verification procedure above.
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
- Before removal inspect exact path and two-way Git metadata, creation evidence and independently established ownership, process activity, locks, integration status, and all tracked, untracked, and ignored data.
  `git worktree remove` can delete ignored files: preserve unclear or user-owned data and obtain explicit authorization for any non-regenerable data deletion.
  Do not remove another session's worktree without explicit authorization, including when its owner is dead; historical records alone do not authorize removal.
  For an integrated clean worktree with only verified disposable ignored files and all checks satisfied, use `git worktree remove <exact-path>` without `--force` and verify removal with `git worktree list --porcelain`.
  If `git worktree remove` refuses because of modified, staged, untracked, merge-state, or submodule content, use a single `--force` (never `-ff`) only under the global waiver: current user authorization naming the exact worktree path and the complete inventory to be discarded, including submodule content, in-progress merge, rebase, cherry-pick, revert, or bisect state, per-worktree refs and the HEAD reflog, and commits reachable only from its detached HEAD, re-verified unchanged immediately before execution together with registration, two-way metadata, live processes, and lock state.
  Clear a worktree lock only with `git worktree unlock <exact-path>` under that authorization; identity and process checks still apply, ownership may be unknown or another session's, and integration status is inspected and disclosed in the inventory rather than required.
  Only the integrator uses this waiver; a delegated writer never removes worktrees.
  Never prune or delete Git metadata manually.
  Do not discard dirty or unintegrated work except under that waiver or a separately specified, authorized preservation and recovery procedure.
  If ownership is unknown, preserve the worktree and stop, unless the user names its exact path for removal under the waiver above.
- Reconcile all worktrees created for the task, including delegated worktrees and revisions, from task records and Git's worktree list; report retained entries and reasons.
  Do not infer task linkage from names alone.
- Do not push unless explicitly requested; never force-push or rewrite history without explicit authorization.

## Parallel work

- The parent creates and verifies each detached worktree before delegation, gives the exact path, base and scope, and assigns disjoint paths.
  A delegated writer never creates or removes worktrees, integrates, updates refs, or pushes.
- Keep outputs inside the assigned worktree and serialize unavoidable shared resources with an owned lock.
  Do not remove another writer's lock or use a shared stash.

## Commits and verification

- Before committing inspect status, staged and unstaged diffs, and the repository's commit convention; stage only task-owned files and never commit secrets.
- Run repository-required validation and hooks, then commit coherent changes.
  Do not use `--no-verify`, disable hooks, or bypass a guard or permission refusal.
- Report commit OIDs, verification, integration and cleanup outcomes, and all unresolved work.
