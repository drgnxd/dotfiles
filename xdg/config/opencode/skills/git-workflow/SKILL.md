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
- Never make task edits with `main` checked out. For every user-requested task,
  regardless of size, record the live local `refs/heads/main` OID and create a
  fresh uniquely named detached task worktree at that exact commit before
  editing. Task and integration worktrees do not create branches. Verify the
  worktree ID, path, base OID, and owner metadata; if names/paths exist or
  metadata cannot be written and verified, choose new ones or stop.
- Unless the target repository documents its own worktree naming, name each
  worktree directory `<slug>-<YYYYMMDD>-<NN>`. `<slug>` is 2-4 lowercase ASCII
  words of letters and digits joined by hyphens that say what the task does;
  the date is local. `<NN>` is a two-digit number greater than every number
  already seen for that slug and date in worktree directories,
  `git worktree list --porcelain` entries, and stale `.git/worktrees/` admin
  directories; never fill a gap. Create a detached worktree with
  `git worktree add --detach <path> <OID>`; if it fails, treat the name as
  taken and pick a higher `<NN>`. A revision gets a fresh `<NN>`. Right after
  creation, the creator records the task, client/session, base OID, agent PID,
  and optional parent task in a private owner file inside the verified per-
  worktree Git admin directory. Do not create task or integration branch refs.
  For AI-managed tasks, prefer the lifecycle wrapper:
  `python3 <skill-dir>/scripts/worktree-task.py start --repo <repo> --slug <slug> --client <claude|opencode> --task "<text>" [--allow-repository-hooks]`.
  `--repo` is required and never inferred from cwd. After task changes are
  committed and verified, finish with
  `python3 <skill-dir>/scripts/worktree-task.py finish --repo <repo> --worktree-id <exact-worktree-id> --external-writers-quiesced [--integration-message <message>] [--allow-repository-hooks] [--allow-annex-filter] [--allow-commit-signing] [--preserve-generated-artifacts]`.
  Run `finish` from outside the task/integration worktree being removed (prefer
  the repository's main checkout); the caller's own cwd is included in the
  process-use check and otherwise blocks cleanup.
  The assertion flag is valid only after checking repository-specific scheduled
  jobs and coordinating non-cooperating writers through integration and all
  cleanup. `status --repo <repo>` delegates to `worktree-audit.py`.
  `finish` locks from preflight through post-check, checks path aliases, hooks,
  filters and submodules, and updates main only by fast-forward. Another task
  worktree's active-session status alone does not block this task's integration
  or cleanup.
  If main advanced from the task base, it creates a detached integration
  worktree and merges the immutable task-tip OID there before fast-forwarding main. Conflicts,
  unrelated histories, and failed safety checks preserve worktrees and stop.
  Post-check failures after main has moved are reported from the actual HEAD/ref
  and are never rolled back. Successful `finish` removes worktrees by default;
  removes detached task/integration worktrees after successful integration.
  It creates no task or integration branch refs. `finish` discards recognized
  generated caches and build outputs by default after successful
  removal, while unknown ignored/untracked data still blocks cleanup. Use
  `--preserve-generated-artifacts` to quarantine and retain recognized caches,
  build outputs, and a marked Nix-generated `.pre-commit-config.yaml` instead.
  Direct low-level `safe-worktree-remove.py` calls remain opt-in: pass
  `--discard-generated-artifacts` to discard the same recognized artifacts.
  The tool invokes the actual safe remover without requiring its
  pre-restage dry-run, which may false-positive for git-annex worktrees.
  Executable repository hooks block by default. After inspecting every relevant
  hook, `--allow-repository-hooks` lets Git run them normally, but never allows a
  `reference-transaction` hook because it may alter refs during integration.
  When main has advanced and an integration merge commit is required, supply
  `--integration-message` when the target repository's commit convention differs
  from the default message.
  Integration preflight checks the task worktree's own delta; it checks path and
  filter conflicts again against the actual merged tree before fast-forwarding.
  Filters are denied by default. `--allow-annex-filter` permits only the known
  `git-annex` clean/smudge/process commands after checking their configuration
  and that `git-annex` is available; arbitrary filters remain blocked.
  If the target repository configures signed commits, `finish` stops before
  creating an integration worktree. Pass `--allow-commit-signing` only after the
  user authorizes use of that repository's configured signer.
  The lower-level creator is
  `python3 <skill-dir>/scripts/worktree-create.py --repo <repo> --slug <slug> --client
  <claude|opencode|copilot> --task "<text>" [--from <commit>] [--parent <worktree-id>]
  [--allow-repository-hooks]`: it applies the numbering rule, runs
  `git worktree add --detach`, checks the new `.git` identity, and writes the
  owner metadata into the verified per-worktree Git admin directory. The
  `(client, session)` pair identifies cleanup ownership; the worktree ID selects
  one worktree when a session creates several. Task
  text is descriptive only and must not contain reserved trailer tokens such as
  `client=`, `session=`, `base=`, `pid=`, or `parent=`. The session id comes only from the client's own
  variable: `CLAUDE_CODE_SESSION_ID` for Claude Code, `OPENCODE_SESSION_ID` for
  OpenCode (set by the `session-env` plugin), none for Copilot CLI. A missing
  or malformed value is recorded as `session=unknown`; never guess one. Exit
  code 3 means the worktree exists but owner metadata was not written. Exit code
  4 means the identity check failed: preserve the worktree. Without the script,
  do the same steps by hand.
- To find forgotten worktrees run `python3 <skill-dir>/scripts/worktree-audit.py
  [--base main]`. It is read-only and takes no lock. `ACTIVE` and `UNKNOWN` are
  never removal candidates. Only `IDLE-MERGED` worktrees owned by the current
  `(client, session)` print a dry-run `safe-worktree-remove.py` command; other
  sessions and unmerged work get no command.
- `scripts/worktree_guard.py` backs the main-checkout rule as a PreToolUse hook
  (Claude Code) and a `tool.execute.before` plugin (OpenCode). It acts only on
  repos listed in the machine-local `$XDG_CONFIG_HOME/worktree-guard/config.json`
  (`mode`: `warn` logs what `deny` would block; `repos`; `allow_paths` for
  main-checkout-only runtime data such as a local database). It denies edits to
  any non-allowed path in a protected checkout (the primary one, a worktree
  with the default branch checked out, or a detached worktree without valid
  task owner metadata) and inside Git directories, git write commands there,
  `git worktree add|remove|...`, and
  `--no-verify`. When it denies, create a task worktree instead; never work
  around it with Bash writes. It fails open on its own errors, does not see
  `sed -i` or shell redirects, and Copilot CLI has no guard. Decisions are
  logged (tool, rule, resolved path only) under `$XDG_STATE_HOME/worktree-guard/`.
  Documented fallbacks are guard-denied unless made safe: create the worktree
  owner metadata with `worktree-create.py`, create the integration lock with
  Bash `mkdir`, and treat a manual `git worktree add` or `git worktree remove`
  as an escalation point: ask the user.
- A read-only agent may share a worktree only if it does not checkout, generate,
  format, update dependencies, or otherwise write files. Writable task agents
  use separate detached worktrees with verified per-worktree owner metadata;
  commits stay on detached HEAD until integrated into `main`. Existing
  branch-backed worktrees remain supported for cleanup and migration.
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
  checkpoint them with a commit on detached HEAD, inspect ignored/untracked
  state, then create a fresh revision worktree from that checkpoint and record
  the parent worktree ID. If ownership is unclear, stop and coordinate. For
  revisions after integration, create a fresh detached worktree from current
  main. Never reuse prior names.
- When other writers may be active, record each commit OID and the detached
  worktree tip immediately after committing. Before reporting completion verify
  the OID is reachable from that worktree's HEAD and the worktree still contains
  the change; if the tip moved or either check fails, stop and re-inspect status,
  history, and the target diff.
- Integrate every completed task into local `main`; a detached task commit alone
  is not completion. Record the task base OID, all task commit OIDs, and task
  tip OID; do not rebase, squash, or rewrite them. If main still equals the task
  base, use the task tip as integration tip. If task tip is already contained
  in current main, verify it and treat it as already integrated. If the recorded
  task base is a common ancestor of current main and task tip, create a fresh
  detached integration worktree from current main and merge the immutable task
  tip OID there with a merge commit; preserve all task commits, then fast-forward main to the
  verified integration tip. A merge conflict preserves both worktrees for
  coordination. If no common base can be verified or repository policy requires
  rewriting, stop and coordinate. If task changes a submodule gitlink, treat the
  nested repository as a separate task; verify nested HEAD/status and source
  availability before changing the parent, and do not auto-update or push it.
- Serialize local main integration with a repository-wide lock under the
  common Git directory: `main-integration.lock`, a directory created with
  `mkdir` that holds an `owner` file with your token. A directory without an
  `owner` file counts as occupied; ignore `main-integration.lock.released.*`.
  Release it only when the token matches, by renaming it to
  `main-integration.lock.released.<token>`, then delete that renamed directory
  (its `owner` file, then `rmdir`; never anything with another token) so no
  leftovers accumulate. Acquire it before preflight and
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
  OID, lock ownership, and each detached worktree's ID, owner metadata, and HEAD;
  stop/rebuild if any changed. Verify no refs other than the recorded main
  fast-forward were changed.
  After integration, verify live main ref and HEAD/tree equal the recorded
  integration tip, task commits/content are present, and main status has no
  unexplained changes. Inspect every used worktree/nested repo. Do not report
  completion while task changes remain outside main or verification is
  ambiguous.
- The mere existence or active-session status of another task worktree is not evidence of a conflicting writer. Separate task worktrees isolate their filesystem and index; the integration lock serializes shared-ref updates, and integration checks detect path conflicts. Do not block a task's integration or cleanup on an unrelated worktree's activity. Still honor concrete shared-resource conflicts, the external-writer assertion, target-worktree process checks, and all required locks.
- Remove only task/integration worktrees recorded as created by this task,
  after the integration OID is reachable from main, their tips are integrated,
  their tracked/untracked/ignored state is safe, and no process is using them.
  If Git refuses removal, apply the target repository's documented remediation
  for that refusal; if none applies or it stops, preserve the worktree and
  report the blocker. Never force-remove. Get explicit approval before any
  irreversible data or history loss, and stop if ownership or integration is
  ambiguous. While they remain, report the task as incomplete, not done. To
  remove a detached worktree directly, run
  `python3 <skill-dir>/scripts/safe-worktree-remove.py <worktree>
  --expect-worktree-id "<exact worktree ID>" [--base <ref>]
  [--discard-direnv-cache] [--discard-generated-caches]
  [--discard-generated-build-outputs] [--discard-generated-artifacts]
  [--preserve-generated-artifacts]`,
  where `<skill-dir>` is `~/.config/opencode/skills/git-workflow` or
  `~/.local/share/claude/skills/git-workflow` (same files). Release your own
  `main-integration.lock` first; the script takes it. It refuses unless the
  worktree is clean (ignored and untracked included), has no hidden edits,
  in-progress operation, submodule, or process with its cwd inside (needs
  `lsof`), HEAD and every HEAD-reflog commit are reachable from `--base`
  (default `main`), the current client session ID matches the recorded owner,
  and the exact `--expect-worktree-id` matches the detached worktree's verified
  Git admin directory and owner metadata. Legacy branch-backed worktrees can
  still be selected with `--expect-branch`; new task worktrees are detached.
  Session identity is read from the current client's environment variable, not
  supplied as a free-form argument; `session=unknown`, legacy, or malformed
  owner metadata are refused. A worktree ID selects a target but does not
  transfer ownership to another session. `--expect-owner` is obsolete and
  refused. This is a cooperative session-ownership guard, not an authentication
  boundary against a process that can modify its environment. A root `cultura.db`
  symlink is accepted only when it resolves to the regular `cultura.db` in the
  registered `main` worktree. It unlinks only the symlink, rechecks the
  worktree, and restores the link on refusal when its path remains free; the
  database target is never touched. The standard `worktree-task finish` passes
  `--discard-generated-artifacts` by default; direct low-level calls require
  that flag to discard cache/build roots. A root `.direnv` path is quarantined
  and retained by direct calls unless `--discard-direnv-cache` or
  `--discard-generated-artifacts` is passed; it is deleted only when its strict
  Nix-direnv `use flake` layout verifies. Unknown layouts remain quarantined and
  the archive path is reported. By default all other ignored/untracked paths still cause
  refusal. `--discard-generated-artifacts` selects the verified Nix-direnv
  cache, recognized cache/build paths, the root `result` symlink, and the root
  `.pre-commit-config.yaml` only when its Nix-generated marker matches. The
  standard `worktree-task finish` workflow passes this option by default.
  `--preserve-generated-artifacts` is an opt-out that quarantines and retains
  those recognized cache/build paths and marked generated config.
  `--discard-generated-caches` selects
  the entire contents of root `.pytest_cache`, root `.ruff_cache`, and
  `__pycache__` directories beneath the worktree. The separate
  `--discard-generated-build-outputs` flag selects only root `target`,
  `rust/target`, and the root `result` symlink; the symlink itself is unlinked
  and its target is never followed or removed. Names are selectors, not proof
  of provenance: every entry beneath a selected cache/build root is discarded,
  including hand-edited files. Do not store independent user data there; use
  `--preserve-generated-artifacts` to retain recognized roots. Dry-run lists
  the selected paths. The helper rejects tracked contents, unsafe path
  types, nested Git repositories, mount boundaries, and selected directories
  with open handles. It quarantines selected paths, restores them on
  pre-removal refusal without overwriting occupied paths, and purges them only
  after Git confirms removal. Interrupted purges retain per-entry progress in
  the private manifest. Resume them with
  `safe-worktree-remove.py --purge-preserved-quarantine <operation-id> --repo <repo>`;
  this verifies repository identity, saved signatures, open handles, and the
  current main ancestry under the repository lock. Legacy `.direnv` quarantines
  without a saved signature require the additional `--discard-unverified-direnv`
  opt-in. Unknown or changed entries remain preserved for inspection. The
  discard option is never added by `worktree-audit.py`. The
  caller must exclude writers that can affect the target worktree or shared
  resources for the complete inspection-to-removal interval; the script lock
  coordinates cooperating integration and cleanup operations. It copes with git-annex's `.git`
  symlink, prints `owner:` on stderr, and never forces. `--delete-branch` is
  retained only for legacy branch-backed worktrees. Any refusal is a stop condition, and
  `--allow-unreferenced-reflog` needs the user's explicit approval. Use
  `--delete-branch` only when explicitly removing a task-owned legacy branch;
  never use it for a reused or shared branch. After successful removal, verify
  that the worktree is unregistered. Before reporting completion, verify that
  no task/integration worktree created for this task remains. If removal is
  refused, report cleanup as incomplete.
- Do not stop integrating or removing a task-owned worktree merely because
  another task worktree exists, is active, or has unrelated dirty files. Scope
  exclusivity to the target worktree and any shared resources for which cleanup requires conflicting
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
