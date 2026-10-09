---
name: git-workflow
description: Use before the first file edit or Git write in each repository for each task, whatever the task size. Not for read-only inspection or directories outside a Git work tree.
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
  with `git config branch.<branch>.description "<text>"` (not
  `--edit-description`, which opens an editor); this is the one shared-config
  write allowed at creation, and only before concurrent agents start.
  Prefer `python3 <skill-dir>/scripts/worktree-create.py --slug <slug> --client
  <claude|opencode|copilot> --task "<text>" [--from main] [--parent <branch>]
  [--prefix integration]`: it applies the numbering rule, runs the single
  `git worktree add -b`, checks the new `.git` identity, and writes the
  description `<task> client=<c> session=<id> base=<OID> pid=<pid>@<start>
  [parent=<branch>]`. Keep `client=` first after the task text; the
  `--expect-owner` match at removal uses the task text. The session id comes only from the client's own
  variable: `CLAUDE_CODE_SESSION_ID` for Claude Code, `OPENCODE_SESSION_ID` for
  OpenCode (set by the `session-env` plugin), none for Copilot CLI. A missing
  or malformed value is recorded as `session=unknown`; never guess one. Exit
  code 3 means the worktree exists but the description was not written:
  write the printed text by hand. Exit code 4 means the identity check failed:
  preserve the worktree. Without the script, do the same steps by hand.
- To find forgotten worktrees run `python3 <skill-dir>/scripts/worktree-audit.py
  [--base main]`. It is read-only and takes no lock. `ACTIVE` and `UNKNOWN` are
  never removal candidates; only `IDLE-MERGED` prints a dry-run
  `safe-worktree-remove.py` command, and unmerged work gets none.
- `scripts/worktree_guard.py` backs the main-checkout rule as a PreToolUse hook
  (Claude Code) and a `tool.execute.before` plugin (OpenCode). It acts only on
  repos listed in the machine-local `$XDG_CONFIG_HOME/worktree-guard/config.json`
  (`mode`: `warn` logs what `deny` would block; `repos`; `allow_paths` for
  main-checkout-only runtime data such as a local database). It denies edits to
  any non-allowed path in a protected checkout (the primary one, or a worktree
  with the default branch checked out or a detached HEAD) and inside Git
  directories, git write commands there, `git worktree add|remove|...`, and
  `--no-verify`. When it denies, create a task worktree instead; never work
  around it with Bash writes. It fails open on its own errors, does not see
  `sed -i` or shell redirects, and Copilot CLI has no guard. Decisions are
  logged (tool, rule, resolved path only) under `$XDG_STATE_HOME/worktree-guard/`.
  Documented fallbacks are guard-denied unless made safe: record a description
  with `git -C <task worktree> config branch.<b>.description ...`, create the
  integration lock with Bash `mkdir`, and treat a manual `git worktree add` or
  `git worktree remove` as an escalation point: ask the user.
- A read-only agent may share a worktree only if it does not checkout, generate,
  format, update dependencies, or otherwise write files. A detached-HEAD
  worktree is allowed only for read-only inspection that cannot share an
  existing worktree. It uses the same directory naming, and it is
  removed like other task worktrees. Existing worktrees and branches keep their
  names.
- When verifying a linked worktree's `.git`, determine the entry's own type
  without following symlinks; a content reader may show a symlink target as a
  directory. Accept only a gitfile or a symlink resolving to the registered
  worktree admin directory. For a symlink, resolve its target; for a gitfile,
  read its `gitdir:` target. Resolve relative paths against the directory
  containing the entry that records them. Verify the canonical target is Git's
  registered worktree admin directory and the admin directory's `gitdir` points
  back to that worktree's `.git`. Stop and preserve the entry and any symlink
  target if the entry has another type, the relationship is mismatched, or
  identity cannot be established. A successful identity check does not waive
  other safety checks.
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
  --expect-owner "<task text you recorded>" [--discard-direnv-cache]
  [--delete-branch] [--base <ref>]`,
  where `<skill-dir>` is `~/.config/opencode/skills/git-workflow` or
  `~/.local/share/claude/skills/git-workflow` (same files). Release your own
  `main-integration.lock` first; the script takes it. It refuses unless the
  worktree is clean (ignored and untracked included), has no hidden edits,
  in-progress operation, submodule, or process with its cwd inside (needs
  `lsof`), HEAD and every HEAD-reflog commit are reachable from `--base`
  (default `main`), and the branch description contains the `--expect-owner`
  text; without that option ownership is not checked. A root `cultura.db`
  symlink is accepted only when it resolves to the regular `cultura.db` in the
  registered `main` worktree. It unlinks only the symlink, rechecks the
  worktree, and restores the link on refusal when its path remains free; the
  database target is never touched. A root `.direnv` path is quarantined
  outside the worktree so it cannot block removal. Pass `--discard-direnv-cache`
  only when the task created the cache and the helper's strict Nix-direnv
  `use flake` layout check accepts it; it is purged only after Git confirms
  successful removal. Unknown layouts remain quarantined and the archive path
  is reported. Other ignored/untracked paths still cause refusal. The caller
  must exclude all
  writers for the complete inspection-to-removal interval; the script lock
  coordinates cooperating removals only. It copes with git-annex's `.git`
  symlink, prints `owner:` on stderr, drops the deleted branch's config
  section, and never forces. Any refusal is a stop condition, and
  `--allow-unreferenced-reflog` needs the user's explicit approval. Use
  `--delete-branch` only when the worktree's branch was created for this task
  and is confirmed task-owned; never use it for a reused or shared branch.
  After successful removal, verify that the worktree is unregistered and, for
  task-owned branches, that the branch ref is absent. Before reporting
  completion, verify that no task/integration worktree or task-owned branch
  created for this task remains. If removal is refused or a task-owned branch
  must be retained, report cleanup as incomplete.
- Do not stop removing a task-owned worktree merely because another task
  worktree exists or has unrelated dirty files. Scope exclusivity to the target
  worktree and any shared resources for which cleanup requires conflicting
  access, including shared Git or annex state accessed by `git annex restage`.
  Preserve all existing mandatory lock-acquisition and caller-coordination
  requirements, including the main-integration lock where required, throughout
  the inspection-to-completion interval; process inspection is not a substitute
  for those safeguards. An unrelated task blocks cleanup only if its activity
  conflicts with that scope, or required exclusivity within that scope cannot be
  established. Inspect relevant processes and locks rather than inferring
  conflict from repository-wide status. Unlinking only the target worktree's
  verified canonical DB symlink does not itself modify the canonical DB and
  does not require unrelated DB users to stop.
- When reporting a commit to the user, quote its message verbatim, including its
  language, rather than paraphrasing or translating it into the reply language.
