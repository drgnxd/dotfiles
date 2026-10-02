---
name: parallel-agents
description: Use when you launch writing subagents, work as a delegated writing agent in an assigned worktree, or share a repository or output location with other concurrent writers.
---

# Parallel Writing Agents

Complements `git-workflow` and the global worktree rules; it only fills gaps and
never relaxes them. Where it conflicts with either, the stricter rule wins.

## Parent / integrator

- The parent creates every worktree and branch with unique names before
  delegating. Writing agents never run `git worktree add`.
- Each delegation prompt states the worktree path, branch, allowed edit scope,
  and that the agent must not integrate. Subagents inherit the parent's cwd, so
  an unstated path means they write in the parent's worktree.
- Assign disjoint edit scopes. Formatters, codegen, and dependency or lockfile
  updates are out of scope unless explicitly assigned.
- Prefer worktrees under `~/.local/state/<repo>/worktrees/`; do not use the
  client's built-in worktree isolation, which places them inside the repository.
- Only the integrator integrates into `main`, takes the integration lock, checks
  every worktree before `git worktree prune`, and removes worktrees and branches.
- Pushing is governed by `git-workflow`; do not push unless the user asked, and
  then only the integrator pushes the refs the user named.

## Writing agent

- Run every Git command as `git -C <assigned-worktree>` and give file tools
  absolute paths under it; the shell cwd may reset to the parent's between calls.
- Before the first write and before each commit, compare `pwd -P`-style
  canonical paths of `git rev-parse --show-toplevel` and the current branch with
  the assignment. Stop on a mismatch or a detached HEAD.
- Commit only to the assigned branch. Do not integrate, take the integration
  lock, touch `main` or refs you did not create, or remove worktrees or branches.
- Do not create, apply, pop, drop, or clear stash entries, and avoid
  `--autostash`; the stash ref is shared. Set work aside with a WIP commit on
  your own branch.
- Do not change shared Git state while others run: `git config`, hooks,
  `gc --prune=now`, or any repository-wide prune.
- A `index.lock` or other Git lock is a live writer. Retry a bounded number of
  times with backoff, then stop and report. Never remove a lock outside your
  own worktree's admin directory.
- Keep generated output inside the worktree. For unavoidable shared resources
  outside it, take an `mkdir` lock at `~/.local/state/<repo>/locks/<resource>.lock`
  (with an owner file), fail instead of waiting if it exists, and release it
  when done. Do not install `flock`.

## Finishing

Report the branch, tip OID, commit OIDs, changed paths, worktree cleanliness
(including untracked and ignored files), unresolved items, and that nothing was
integrated or pushed; then stop.
