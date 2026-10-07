---
name: git-workflow
description: Use before Git history changes.
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
- Never make task edits with `main` checked out or in detached HEAD. For every
  user-requested task, regardless of size, record the live local
  `refs/heads/main` OID and create a fresh uniquely named task branch/worktree
  from that exact OID before editing. Verify the branch, path, and base OID;
  if names/paths exist or the branch is in use, choose new ones or stop.
- Unless the target repository documents its own branch naming, name the
  worktree directory `<slug>-<YYYYMMDD>-<NN>` and its branch
  `task/<slug>-<YYYYMMDD>-<NN>` (`integration/...` for an integration branch).
  `<slug>` is 2-4 lowercase ASCII words of letters and digits joined by hyphens
  that say what the task does; the date is local. `<NN>` is a two-digit number
  greater than every number already seen for that slug and date in local
  branches, worktree directories, `git worktree list --porcelain` entries,
  stale `.git/worktrees/` admin directories, and remote-tracking refs; never
  fill a gap. Create branch and worktree in one
  `git worktree add -b <branch> <path> <OID>`; if it fails, treat the name as
  taken and pick a higher `<NN>`, and never adopt an existing branch. A revision
  gets a fresh `<NN>`. Right after creation, the creator records the task, and
  for revisions or integrations the parent branch and base or checkpoint OID,
  and ends the text with `client=<claude|opencode|copilot>` (the agent cannot reliably
  know its session id, so do not record one), with
  `git config branch.<branch>.description "<text>"` (not
  `--edit-description`, which opens an editor); this is the one shared-config
  write allowed at creation, and only before concurrent agents start.
- A read-only agent may share a worktree only if it does not checkout, generate,
  format, update dependencies, or otherwise write files. A detached-HEAD
  worktree is allowed only for read-only inspection that cannot share an
  existing worktree. It uses the same directory naming, and it is
  removed like other task worktrees. Existing worktrees and branches keep their
  names.
- Keep implementation edits, commits, tests, generators, and conflict
  resolution in task/integration worktrees. Scope explicit and implicit output
  paths (baselines, caches, databases, logs, temp files, configs) to those
  worktrees; inspect hooks/filters and stop if they may push, alter main/other
  refs, or write outside the current worktree. Preserve user data; do not use
  reset/restore/clean/stash/delete to make a worktree appear clean.
- For a revision before integration, verify remaining changes are task-owned,
  checkpoint them in the current task branch, inspect ignored/untracked state,
  then create a fresh revision branch/worktree from that checkpoint. If
  ownership is unclear, stop and coordinate. For revisions after integration,
  create a fresh branch/worktree from current main. Never reuse prior names.
- When other writers may be active, record the commit OID and the intended
  branch tip right after committing. Before reporting completion verify the OID
  is still reachable from that branch and the branch tree still contains the
  change; if the tip moved or either check fails, stop and re-inspect status,
  history, and the target diff.
- Integrate every completed task into local `main`; a task-branch commit alone
  is not completion. Record the task base OID, all task commit OIDs, and task
  tip OID; do not rebase, squash, or rewrite them. If main still equals the task
  base, use the task tip as integration tip. If main advanced as a descendant,
  create a fresh integration branch/worktree from current main and merge the
  immutable task-tip OID there, preserving task commits. If histories diverged
  or repository policy requires rewriting, stop and coordinate. If task
  changes a submodule gitlink, treat the nested repository as a separate task;
  verify nested HEAD/status and source availability before changing the parent,
  and do not auto-update or push it.
- Serialize local main integration with a repository-wide lock under the
  common Git directory: `main-integration.lock`, a directory created with
  `mkdir` that holds an `owner` file with your token. A directory without an
  `owner` file counts as occupied; ignore `main-integration.lock.released.*`.
  Release it only when the token matches, by renaming it to
  `main-integration.lock.released.<token>`. Acquire it before preflight and
  hold it through post-check; all cooperating agents must honor it. If occupied
  or unavailable, stop without removing another owner's lock. The only
  permitted update to the main worktree/index/ref is the complete fast-forward
  integration command; never manually edit, stage, commit, reset, restore, clean, cherry-pick, squash,
  or resolve conflicts there. Use
  `git merge --ff-only --no-overwrite-ignore <recorded-integration-OID>`; do not
  push. If Git refuses, preserve state and coordinate.
- If concurrent work is discovered after edits have begun in a shared
  worktree, or staged or unstaged changes there have unclear ownership or fall
  outside the task, stop all mutations there (checkout, staging, commit, reset,
  restore, clean, rebase) and preserve its state; continue only in a dedicated
  worktree. Do not move or selectively clean mixed/ambiguous changes.
- Before committing, inspect `git status`, both `git diff` and `git diff --cached`,
  and `git log --oneline -10`; verify every staged change belongs to the task,
  stage only intended files, preserve unrelated changes, and never commit
  secrets.
- Run the target repository's commit-message validation command or installed
  `commit-msg` hook when available; do not use `--no-verify` to bypass it.
- Before committing, draft the exact subject and body and compare them field by
  field with every applicable requirement in the target repository's documented
  contract, including summary opening/action, type/scope, title formatting,
  language, and body requirements. Re-read the exact final message immediately
  before committing; a valid Conventional Commits prefix alone does not
  establish repository-specific compliance.
- Run all validation gates declared by the active repository.
- Do not commit while a required validation gate fails.
- Do not amend, force-push, or use interactive git commands unless explicitly
  requested.
- Before integration, require main checked out on `main`, HEAD equal to the
  live ref, ordinary tracked/untracked status clean, and no
  assume-unchanged/skip-worktree entries. Record main's pre-integration OID,
  ignored/untracked path inventory, task tip, integration tip, and all intended
  task commits. Verify no `refs/replace/*` affects OID/tree checks. Enumerate
  the expected final tracked paths and all untracked/ignored paths with
  `git status --short --untracked-files=all --ignored=matching`; compare paths
  pairwise and across existing data using target-filesystem canonicalization,
  including case, Unicode, reserved names, trailing dot/space, and file/
  directory/symlink aliases. Reject collisions or unrepresentable paths; never
  overwrite user data. Inspect invoked hooks/filters for writes, remote access,
  and submodule recursion; stop if unsafe or unknown.
- Immediately before fast-forward, recheck the recorded main OID, integration
  OID, lock ownership, and worktree state; stop/rebuild if any changed. Verify
  the task/integration branch refs changed only through the recorded commands.
  After integration, verify live main ref and HEAD/tree equal the recorded
  integration tip, task commits/content are present, and main status has no
  unexplained changes. Inspect every used worktree/nested repo. Do not report
  completion while task changes remain outside main or verification is
  ambiguous.
- Remove only task/integration branches and worktrees recorded as created by
  this task, after the integration OID is reachable from main, their tips are
  integrated, their tracked/untracked/ignored state is safe, and no worktree is
  using them. If Git refuses removal, apply the target repository's documented
  remediation for that refusal; if none applies or it stops, preserve them and
  report the blocker. Never force-remove. Get explicit approval before any
  irreversible data or history loss, and stop if ownership or integration is
  ambiguous. While they remain, report the task as incomplete, not done. To remove a worktree run
  `python3 <skill-dir>/scripts/safe-worktree-remove.py <worktree>
  --expect-owner "<task text you recorded>" [--delete-branch] [--base <ref>]`,
  where `<skill-dir>` is `~/.config/opencode/skills/git-workflow` or
  `~/.local/share/claude/skills/git-workflow` (same files). Release your own
  `main-integration.lock` first; the script takes it. It refuses unless the
  worktree is clean (ignored and untracked included), has no hidden edits,
  in-progress operation, submodule, or process with its cwd inside (needs
  `lsof`), HEAD and every HEAD-reflog commit are reachable from `--base`
  (default `main`), and the branch description contains the `--expect-owner`
  text; without that option ownership is not checked. It copes with git-annex's
  `.git` symlink, prints `owner:` on stderr, drops the deleted branch's config
  section, and never forces. Any refusal is a stop condition, and
  `--allow-unreferenced-reflog` needs the user's explicit approval.
- When reporting a commit to the user, quote its message verbatim, including its
  language, rather than paraphrasing or translating it into the reply language.
