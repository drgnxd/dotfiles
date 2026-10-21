---
name: parallel-agents
description: Use when you launch writing subagents, work as a delegated writing agent in an assigned worktree, or share a repository or output location with other concurrent writers.
---

# Parallel Writing Agents

Complements `git-workflow` and the global rules; it only fills gaps and
never relaxes them. Where it conflicts with either, the stricter rule wins;
a user waiver under the global rules is not a conflict and still applies.

## Parent / integrator

- The parent creates every detached worktree with unique names and owner
  metadata before delegating. Writing agents never run `git worktree add`.
  Use schema-1 `wtctl create` (git-workflow): it records the parent agent
  process as owner instead of a session-id variable, so stale inherited session
  variables do not block it.
- Each delegation prompt states the worktree path, worktree ID, allowed edit
  scope, and that the agent must not integrate. Subagents inherit the parent's
  cwd, so an unstated path means they write in the parent's worktree.
- Assign disjoint edit scopes. Formatters, codegen, and dependency or lockfile
  updates are out of scope unless explicitly assigned. Worktrees isolate only
  files, the index, and checkout state; they do not prevent merge conflicts.
- Place worktrees under `~/.local/state/<repo>/worktrees/` (the global rules
  require this, never `$TMPDIR`), and name and record them as `git-workflow`
  specifies; do not use the client's built-in worktree isolation, which places
  them inside the repository.
- Only the integrator completes `wtctl finish` into `main`, which takes the
  shared integration lock, checks worktrees, and removes the task worktree.
- Pushing is governed by `git-workflow`; do not push unless the user asked, and
  then only the integrator pushes the refs the user named.

## Writing agent

- Run every Git command as `git -C <assigned-worktree>` and give file tools
  absolute paths under it; the shell cwd may reset to the parent's between calls.
- Before the first write and before each commit, compare `pwd -P`-style
  canonical paths of `git rev-parse --show-toplevel` and the assigned worktree
  ID/owner metadata (`wtctl whoami` prints both for `wtctl` worktrees). Stop
  on a mismatch or if HEAD is not detached.
- Commit only in the assigned detached worktree. Do not create or update refs,
  integrate, take the integration lock, touch `main`, or remove worktrees.
- Do not create, apply, pop, drop, or clear stash entries, and avoid
  `--autostash`; the stash ref is shared. Set work aside with a WIP commit on
  your assigned detached HEAD.
- Do not change shared Git state while others run: `git config`, hooks,
  `gc --prune=now`, or any repository-wide prune.
- A `index.lock` or other Git lock is a live writer. Retry a bounded number of
  times with backoff, then stop and report. Never remove a lock outside your
  own worktree's admin directory.
- Keep generated output inside the worktree. For unavoidable shared resources
  outside it, take an `mkdir` lock at
  `~/.local/state/<repo>/locks/<resource>.lock` containing an `owner` file (as
  `main-integration.lock` does). Fail instead of waiting if it exists, and
  release it only if the owner file is yours. Do not install `flock`.

## Finishing

Report the worktree ID, detached tip OID, commit OIDs, changed paths, worktree
cleanliness (including untracked and ignored files), unresolved items, and that
nothing was integrated or pushed; then stop.
