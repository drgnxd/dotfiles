---
name: git-workflow
description: Use before the first file edit or Git write in each repository for each task, whatever the task size. Not for read-only inspection or directories outside a Git work tree.
---

# Git Workflow

A user waiver under the global rules applies to this Skill's procedural rules, except the
items the global rules list as not waivable by conversation.

## Shell Environment

- Follow Lifecycle for the working directory of `wtctl` create, integration,
  and removal; task-worktree setup must not depend on that worktree already
  existing. After creation, run task commands from the task worktree so its
  approved `.envrc` can activate the repository environment through direnv.
- If direnv blocks a fresh worktree, inspect its `.envrc` and compare it with
  the trusted repository version before allowing that exact file; never approve
  an unseen environment file. When changing worktrees, let direnv apply the
  environment for the new directory.
- Use one persistent command shell for the task. Confirm that the expected
  environment actually loaded using the repository's documented shell marker or
  direnv status; executable availability alone does not prove that the intended
  environment is active. Then run Git and `wtctl` directly in that shell; do
  not start `nix develop -c git ...` for each command.
- If the command runner does not apply direnv, use the repository's documented
  devShell-loading method once in the persistent shell. Use a one-shot devShell
  invocation only when the command runner cannot preserve an initialized shell.

## Lifecycle

- Before any Git write, resolve the repository with `git rev-parse
  --show-toplevel`. Read its `AGENTS.md`/contribution instructions and documented
  commit convention (including commit bodies). Follow that contract and keep one
  logical change per commit.
- For a user-requested new repository with no existing `main`, first verify the
  intended destination is absent or an empty directory. If the path contains
  data before this task's bootstrap begins, preserve it and stop unless its
  ownership and inclusion are explicitly confirmed. For a bootstrap already
  started in this task, continue only when repository metadata and any existing
  `README.md` are attributable to this task and no other files are present; do
  not overwrite the README. Check the required schema-1 `wtctl` capabilities
  before creating the destination or repository metadata, so failure to
  provide task worktrees does not leave a seed repository behind. The request
  to create the repository authorizes only this narrow bootstrap: initialize
  `main`, create a minimal `README.md` describing the purpose and ownership
  boundary, and commit that seed. Do not add a remote or push unless explicitly
  requested. Do not add task deliverables, dependencies, tests, or
  implementation in the bootstrap checkout. Record the exact seed `main` OID,
  then immediately create a detached task worktree from it and continue under
  the normal lifecycle below. The seed commit is the only task-related commit
  automatically allowed outside a `wtctl` worktree; any broader exception must
  meet the separate explicit-exception rule.
- Use schema-1 `wtctl` for task worktree lifecycle. Before creating a
  worktree, run `wtctl capabilities --json` and verify it advertises `create`,
  `finish`, legacy lifecycle, Git-annex, artifact quarantine, and quarantine
  purge support. If these capabilities are unavailable, stop and request a
  package update; do not fall back to Python lifecycle scripts. For cleanup,
  use WTCTL normally and attempt its supported path first; the only manual
  cleanup fallback is the bounded exact-worktree deletion procedure below.
- Treat `wtctl finish --dry-run` as a preview only when
  `wtctl capabilities --json` from the installed binary contains
  `finish_dry_run: true`. Otherwise, do not pass `--dry-run`: it may execute
  the real integration and cleanup rather than previewing them. If a preview
  is required, stop and request a `wtctl` package that advertises
  `finish_dry_run: true`. Do not infer support from another binary or source
  revision.
- Record the live local `refs/heads/main` OID. Create a fresh detached worktree
  at that exact OID with `wtctl create --repo <repo> --slug <slug> --task
  "<text>" --from <oid>`. For a revision, use a new slug/ID and record its
  parent with `--parent <worktree-id>`. Never reuse a task or integration
  worktree across tasks or sessions, and never create task or integration
  branches.
- Verify the returned worktree ID, path, base OID, owner marker, and the
  two-way `.git`/Git-admin-directory relationship before editing. Keep all
  edits, commits, tests, generators, and conflict resolution in the task
  worktree; scope build outputs and caches there or use a repository-documented
  external cache path.
  A regular `.git` file may be the normal `gitdir:` file; verify that its
  pointer resolves to the registered admin directory and that the admin
  directory's `gitdir` pointer resolves back to that exact worktree `.git`.
  Do not reject a worktree solely because `test -L .git` is false.
- After task changes are committed and verified, run
  `wtctl finish --repo <repo> --id <worktree-id>
  --external-writers-quiesced` from outside the task worktree. `finish` performs
  preflight, handles a compatible `main` advance without rebasing, fast-forwards
  `main`, performs post-checks, and removes the exact task/integration worktree
  under the shared lock. It creates no task/integration branch refs. Pass
  `--integration-message` only when required by the repository's commit
  convention.
- Before every `finish`, inspect the repository's commit-message hook and
  verify that the installed `wtctl` can pass a complete integration message
  satisfying it if a merge becomes necessary. Do this even when the current
  graph permits a fast-forward: a standalone comparison does not reserve
  `main`, which may advance before `finish` acquires its lock. If the required
  message cannot be supplied, update `wtctl` before running `finish`; do not
  rely on the default merge message or a later abort.
- Before reporting task completion, rerun `wtctl list --all` and reconcile all
  worktrees created for this task, plus any worktrees explicitly linked to it
  by wtctl `parent` metadata or task/session records. Include siblings sharing
  a recorded parent; do not infer linkage only from similar names or matching
  HEADs, and do not clean unrelated worktrees. `finish` handles only its exact
  ID; it does not clean duplicates or siblings. For each related worktree,
  confirm ownership, integration, and tracked, untracked, and ignored state,
  then finish resolved work with its exact ID. For an already-integrated
  worktree with a dead owner, obtain explicit user authorization before
  exact-ID `adopt` and `finish`; otherwise preserve it and report that cleanup
  is incomplete.
- `--external-writers-quiesced` is an assertion, not a lock. Before using it,
  inspect repository-specific scheduled jobs and coordinate non-cooperating
  writers through integration and cleanup. Git-annex `create` and mutating
  `integrate`, `remove`, `reap`, and quarantine-purge operations also require
  that assertion. Use `--allow-annex-filter` only for verified Git-annex
  filters. The user's standing authorization covers signing local commits and
  integrations when the repository's workflow enables signing, using its
  already-configured signer; it also covers replacement-commit signatures
  after the user separately authorizes a local history rewrite. Pass
  `--allow-commit-signing` when wtctl would otherwise block that signing, without
  asking again. Do not enable signing where the repository has it disabled. Ask
  only if signing requires new authentication or changing the configured
  signer. This preference does not authorize history rewrites or pushes.
  Executable repository hooks block by
  default; after inspecting them, `--allow-repository-hooks` permits them
  except `reference-transaction` hooks.
- Before treating another worktree or agent as a blocker, identify the specific
  shared resource touched by this operation and verify an active
  scheduled/non-cooperating writer, a relevant lock, ambiguous ownership, or an
  actual `wtctl` refusal; an active task-worktree label, live owner process, or
  possible future content conflict alone is not sufficient. Keep the
  operation-specific quiescence checks for shared resources, including
  Git-annex state, databases, and lifecycle metadata. Establish and maintain
  any required locks and external-writer quiescence for the specific shared
  resources throughout the operation's required safety interval, including
  inspection through completion where required; a successful preflight check
  alone does not establish continued quiescence. If those checks pass, continue
  in this task's own schema-1 `wtctl` worktree and use `wtctl finish` to
  serialize integration and surface conflicts. Do not defer `finish` or ask the
  user to clear another isolated task worktree solely because paths overlap or
  a conflict may occur. The actor running `wtctl finish` is the later integrator
  and owns any conflict surfaced by that attempt; resolve it only in the
  task/integration worktree under the documented WTCTL lifecycle, then retry
  `wtctl finish`. Do not mutate another task worktree or `main` directly to
  resolve a conflict. This rule does not relax any external-writer, shared-lock,
  ownership, annex, repository-hook, or WTCTL refusal check. Stop whenever a
  required safety condition is unmet or cannot be verified, and handle WTCTL
  refusals only through the documented lifecycle. Do not treat a clean worktree or
  absence of unintegrated commits alone as proof that shared-state writers are
  quiescent.
- Without an explicit artifact selector, `finish` and `remove` follow Git's
  default worktree-removal boundary: tracked changes and non-ignored untracked
  files block removal, while ignored files are deleted with the worktree. This
  path does not classify artifacts, create quarantine, or require `.wtctl.json`.
- `finish --keep-worktree` retains ignored files because it does not remove the
  worktree. Artifact selectors remain opt-in and add artifact classification,
  signature, and quarantine handling. Use them only when the task explicitly
  requires that handling. Do not use direct `remove` to select or discard task
  data unless the user explicitly approved those selectors.
- Do not retain a task worktree or ask the user solely to keep a verified task-generated, regenerable cache such as `.direnv`; inspect ignored paths and WTCTL's manifest to confirm the cache's origin and discardability.
  Use normal `finish`/`remove`.
  Before purging a quarantine, verify the exact operation contains only task-generated, regenerable caches.
  Purge it without asking only when every artifact meets that condition.
  If it contains any other or unverified data, preserve it and follow existing approval safeguards.
- `--preserve-generated-artifacts` retains recognized cache, build, and marked
  Nix-generated config paths in quarantine. Broad discard selectors discard
  selected artifacts after successful worktree removal. Unknown ignored or
  untracked paths remain subject to the explicit artifact policy and may block
  cleanup. Recover a retained quarantine only with
  `wtctl remove --repo <repo> --purge-preserved-quarantine <operation-id>
  --external-writers-quiesced`; unverified `.direnv` additionally requires
  `--discard-unverified-direnv`.
- `reap` remains conservative and only cleans its existing narrowly recognized
  disposable Python caches. Unknown ignored or untracked data continues to
  block `reap`.
- To discard unintegrated or uncommitted work that is no longer wanted, use `wtctl remove --abandon` instead of any manual deletion.
  Always pass `--include-uncommitted` with `--abandon`: it snapshots tracked, staged, and non-ignored untracked changes, and it switches on the ignored-file listing and the `--dead-owner` safeguards.
  `wtctl stale --repo <repo> [--older-than-days <n>]` is read-only and lists dead-owner tasks idle for at least `n` days (default 7).
  It reports the commits that are not on `main` by patch equivalence, merge-commit and already-on-`main` flags, and uncommitted and ignored paths; a merge commit makes the patch-equivalence verdict unreliable.
  The text output shows only counts and at most five commit subjects, so use `--json` (`ignored_paths`) to build the inventory.
  `wtctl show --repo <repo> --id <id> [--json]` may print the owning `session` and `resume` command when a session hint was recorded.
  A dead owner pid does not mean the session is dead: a resumed session gets a new pid.
  Before abandoning a worktree that another session created, confirm that session is idle, meaning its transcript or database shows no recent update and no `claude --resume <id>`, `claude -r <id>`, `opencode --session <id>`, or `opencode -s <id>` process is running.
  A `claude --continue` or `opencode --continue` process does not show the id, so also check for a recent update of the latest conversation in that directory.
  A task owned by copilot records no resume command, so establish its idleness by another means.
  Run `wtctl remove --repo <repo> --id <id> --abandon --include-uncommitted [--dead-owner] [--discard-ignored-files] --dry-run --external-writers-quiesced` first.
  `--abandon` keeps the worktree HEAD under `refs/wtctl/abandoned/<id>`, and `--include-uncommitted` adds the snapshot of uncommitted changes to that ref.
  `--dead-owner` allows a verified-dead owner without `adopt` and requires the newest uncommitted file change to be at least ten minutes old.
  A quiet-period refusal means wait, recheck that the session is idle, and retry; with nothing uncommitted no quiet check runs, so the session-idle check above is the only guard.
  Ignored files are never kept.
  For a dead-owner task the dry-run refuses and names the ignored paths until `--discard-ignored-files` is passed, so that refusal and `wtctl stale --json` are the inventory step.
  After the paths are verified or authorized, rerun with `--discard-ignored-files`.
  Pass `--discard-ignored-files` only for regenerable caches or for a symlink whose target is verified to remain, unless the user approves the exact paths.
  `wtctl restore --repo <repo> --id <id> --slug <slug>` recreates an abandoned task in a new worktree, with uncommitted work restored as a commit authored by wtctl with the message `wtctl: uncommitted changes of <id>`; Git-annex repositories also need `--external-writers-quiesced`, and a `post-checkout` hook needs `--allow-repository-hooks`.
  Re-commit that restored commit with an authorized history operation that meets the repository's message and signing conventions before `finish`.
  A task you created in this session and still own as a live owner (no `--dead-owner`) may be abandoned without extra approval when its work is no longer wanted and the dry-run lists no ignored paths other than verified task-generated, regenerable caches.
  Otherwise present the ID, path, unique commits, uncommitted and ignored inventory, and what the snapshot keeps, then obtain the user's authorization for that exact target; this includes every `--dead-owner` abandon, whatever session created the task.
  Report the `refs/wtctl/abandoned/<id>` ref in the cleanup report.
  Never use `wtctl prune --refs` as routine cleanup: it deletes every abandoned and superseded ref older than the given age whose task is no longer registered, which destroys the only copy of that work.
  Run `wtctl prune --repo <repo> --older-than-days <n> --refs --dry-run` first and obtain the user's confirmation of the listed refs.
  Immediately before the real run, repeat the dry-run with the same `--older-than-days` value and stop if its list differs from the confirmed one.
  Then run it with `--external-writers-quiesced`.
  `--abandon` refuses, among other checks, submodules, nested repositories, unreviewed filters, annex-stored content, changed `.gitignore` or `.gitattributes`, partially staged paths, a conflicting existing ref, another live owner (or, with `--dead-owner`, an owner that is not verifiably dead), and processes whose cwd is inside the worktree.
  Treat any such refusal as a stop condition.
  It does not check open file handles.
- If any lifecycle command refuses, preserve the worktree and data and inspect the reported state.
  For unintegrated or dirty work that is no longer wanted, try `wtctl remove --abandon` first, subject to the authorization rules above; a refusal from `--abandon` is itself a stop condition, apart from the quiet-period wait and the ignored-path authorization described above.
  Work that is still wanted is never abandoned because `finish` refused: resolve it in the task worktree and retry `finish`.
  Only a non-safety capability or operation refusal from another lifecycle command may trigger the bounded manual cleanup below; any permission-system, hook, guard, authorization, or safety-check refusal requires stopping and reporting cleanup as incomplete.
- The existing ignored-artifact fallback applies only when the refusal is solely caused by an unsupported ignored-artifact shape and the user explicitly authorizes cleanup of the exact task worktree.
  For that narrow fallback, verify the exact registered path and both `.git` identity directions, current owner/adoption state, a clean tracked and non-ignored untracked status, every ignored path, and confirm each is a task-generated disposable artifact or has a retained copy verified byte-identical.
  For any other ignored path, show the exact path and deletion impact and obtain explicit user authorization for it; if ownership, purpose, or retention is unclear, preserve it and stop.
  Also verify that all task commits are integrated, no process is using the worktree, no relevant lock other than this adopted task worktree's exact expected lock is active, no external writer is active, and any annex writer quiescence required by repository policy.
  Inspect the Git worktree lock reason; if it is exactly `agent-task <worktree-id>` for this adopted task, unlock only that task lock with `git worktree unlock <path>`, verify it is gone, then remove only that exact worktree with `git worktree remove <path>` and no force option.
  If the lock reason differs, is unreadable, or either Git command refuses, stop and preserve the remaining state.
  Do not directly edit Git administration data or quarantine contents.
  After a crash, inspect `wtctl list --orphans`; adopt a dead-owner task only with explicit user authorization and `wtctl adopt --repo <repo> --id <worktree-id>`.
- The cleanup restrictions in this section govern registered worktrees, their quarantine, and data of unclear ownership.
  They do not stop you from deleting the temporary or regenerable files that the global rules allow you to remove without confirmation; those rules define the allowed locations and conditions.
- Manual worktree deletion is permitted only after WTCTL cannot complete cleanup for a non-safety capability or operation reason, the task has not entered the separate failed-merge or relationship-mismatch recovery procedure, and the target is proven to be the exact task-owned worktree being resolved.
  A task that entered failed-merge recovery is never eligible for this path; if that separate procedure or its exact-ID removal refuses, preserve the worktree and report the refusal.
  Verify the exact registered ID and path, owner and adoption status, and the complete tracked, staged, unstaged, untracked, and ignored inventory.
  Verify `.git` is either an ordinary gitfile or repository-approved symlink; inspect path types with `lstat`, resolve both identity directions using canonical absolute paths, and never follow or remove the admin target or symlink target as part of deleting the worktree directory.
  Verify byte-identical retained copies for all data to be kept, or identify each item explicitly approved for disposal, and identify any task commit loss; all commits must be integrated or their loss expressly described and authorized.
  Establish documented exclusive access or an applicable lock, and confirm no process is using the target, no other relevant lock or writer is active, no other writer's lock will be touched, and repository-specific external-writer and Git-annex quiescence can be maintained continuously through inventory, authorization, deletion, and registry verification; if this cannot be established, stop.
  Before asking for exact current user authorization, present the worktree ID and path, owner and task status, complete inventory, retained/deleted data and effects, and irreversible consequences; if any ownership, data, or preservation status is ambiguous, stop and preserve it.
  First attempt supported, safe, non-forced Git/worktree tools; only after their refusal may the exact target worktree directory be deleted, without force, direct quarantine deletion, Git-admin-file edits, or hook/guard bypass.
  After deletion, verify the exact path is absent and Git's worktree registry and admin metadata are consistent; use supported `git worktree prune` only after a dry-run or equivalent effect inspection proves that only this exact authorized target's metadata would be removed, and stop if unrelated metadata would be pruned or the effect cannot be bounded safely.
- For a failed merge, first use the installed `wtctl` documented recovery path with an integration message accepted by the hook.
  The manual failed-merge exception applies only when `wtctl finish --recover-failed-merge` refuses solely because the recorded task/main/merge relationship does not match; every other refusal remains a stop condition.
  Verify the task ID, registered path, owner/adoption state, exact `agent-task <task-id>` lock reason, and both directions of the `.git`/Git-admin-directory identity.
  Verify `ORIG_HEAD` equals the recorded pre-merge `HEAD`, `MERGE_HEAD` equals the authorized merge-source OID, and both match the contemporaneous record; also verify the recorded task base and tip identify the exact task and the record shows the worktree was clean before that merge began.
  Confirm there is no `MERGE_AUTOSTASH`, rebase, cherry-pick, revert, sequencer, unresolved index entry, or staged/unstaged change of unclear origin.
  Pin the exact current `main` OID and inventory every tracked, staged, unstaged, untracked, and ignored path affected by abort or subsequent removal.
  Verify every task-specific change to be discarded is present in that pinned `main` tree or in a retained copy outside both the target worktree and the cleanup scope.
  Compare file bytes and modes, symlink targets, gitlinks, submodule working-tree and untracked state, and Git-annex keys and required content; a matching pointer or commit ID alone does not prove annex content is retained.
  Confirm each ignored path is task-generated and disposable or has a byte-identical retained copy; otherwise preserve it and stop.
  Confirm no process has the worktree open, no non-cooperating writer or unrelated relevant lock is active, and external-writer and annex quiescence can be maintained from inspection through abort, post-check, and exact-ID `wtctl remove`; the already-verified exact task lock is the only allowed worktree lock.
  Keep exclusive access to the target worktree and make no shared-ref changes during manual abort; verify the pinned `main` OID is an ancestor of the current `refs/heads/main` immediately before abort and again immediately before WTCTL removal, and stop if either check fails.
  Do not unlock another writer's lock or change the task lock manually.
  After every pre-abort check passes, present the exact task ID/path, what `git merge --abort` will restore, what exact-ID `wtctl remove` will delete, and the pinned `main` OID or retained copies preserving each task-specific change; obtain the user's explicit authorization for both non-forced `git merge --abort` and exact-ID `wtctl remove`.
  Run only the explicitly authorized, non-forced `git merge --abort`; do not use `git commit`, `reset`, `clean`, `stash`, manual `git worktree remove`, or Git-administration edits as recovery.
  After abort, verify `HEAD` equals the recorded pre-merge task tip, merge pseudo-refs are gone, and the index, working tree, untracked paths, and ignored paths match the verified pre-merge state.
  If abort fails or any postcondition differs, preserve the resulting state and stop without further cleanup.
  After the abort post-check passes, use only exact-ID `wtctl remove` with the required external-writer and annex checks.
  If WTCTL refuses removal, preserve the worktree; this failed-merge exception itself never authorizes manual worktree deletion or merge abort beyond its separate exact flow.
- After a crash, use `wtctl list --orphans`; adopt a dead-owner task only with explicit user authorization and `wtctl adopt --repo <repo> --id <worktree-id>`.
- Use `wtctl reap` only for safe dead-owner worktrees after its grace period.
- Use `wtctl list --all` and `wtctl whoami` for task ownership/status. Legacy
  session-owned worktrees are visible to wtctl and must be managed with the
  exact worktree ID or branch selector; do not use Python fallback tools.
- The `worktree_guard.py` hook protects main checkouts and Git internals. Never
  bypass a hook or guard with Bash, shell redirection, direct Git administration
  commands, `--no-verify`, or edits in Git directories. The artifact fallback,
  bounded manual worktree cleanup, and manual failed-merge recovery procedures
  authorize only their named actions, exact current authorization, and checks;
  they must run through hooks and guards normally and stop if one refuses.
  Resolve conflicts only in the task/integration worktree and retry `wtctl
  finish` after a safety refusal is addressed.

## Parallel Work

- The parent creates every detached worktree with `wtctl create` before
  delegating and passes the exact path and ID. Writing agents never run
  `git worktree add`, integrate, remove worktrees, update refs, or push.
- Delegate disjoint edit scopes and state explicitly which paths may be changed.
  Formatting, code generation, dependency updates, and shared-output writes are
  out of scope unless explicitly assigned. A read-only agent may share a
  worktree only if it does not checkout or write files.
- Only the integrator runs `wtctl finish` and pushes refs explicitly requested
  by the user. A task commit alone is not completion; verify its OID is
  integrated and local `main` is clean before reporting.

## Commits and Verification

- Before committing, inspect `git status`, `git diff`, `git diff --cached`, and
  recent commit bodies. Stage only task-owned files; never commit secrets or
  unrelated changes. Do not rewrite commits, force-push, or use interactive Git
  commands unless explicitly authorized.
- Run repository-required validation and commit-message checks before committing.
  Do not commit while a required gate fails. Quote the commit message verbatim
  when reporting a commit.
- Preserve concurrent or unclear worktree changes. If ownership is unclear, stop
  mutating that worktree and coordinate rather than cleaning, stashing, or
  transferring its data.
