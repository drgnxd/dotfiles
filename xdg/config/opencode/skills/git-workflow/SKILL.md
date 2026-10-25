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
  package update; do not fall back to Python lifecycle scripts. The only
  lifecycle fallback allowed here is the exact non-forced Git worktree removal
  defined below; direct filesystem deletion of worktree or quarantine contents
  is not authorized.
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
  serialize integration and surface conflicts; do not imply that `wtctl`
  automatically resolves content conflicts. Stop if ownership or a required
  safety condition remains unverifiable, and do not treat a clean worktree or
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
- If any lifecycle command refuses, preserve the worktree and data, inspect the reported state, and report cleanup as incomplete unless one of the two narrowly scoped manual recovery procedures below applies.
- The existing ignored-artifact fallback applies only when the refusal is solely caused by an unsupported ignored-artifact shape and the user explicitly authorizes cleanup of the exact task worktree.
  For that narrow fallback, verify the exact registered path and both `.git` identity directions, current owner/adoption state, a clean tracked and non-ignored untracked status, every ignored path, and confirm each is a task-generated disposable artifact or has a retained copy verified byte-identical.
  For any other ignored path, show the exact path and deletion impact and obtain explicit user authorization for it; if ownership, purpose, or retention is unclear, preserve it and stop.
  Also verify that all task commits are integrated, no process is using the worktree, no relevant lock other than this adopted task worktree's exact expected lock is active, no external writer is active, and any annex writer quiescence required by repository policy.
  Inspect the Git worktree lock reason; if it is exactly `agent-task <worktree-id>` for this adopted task, unlock only that task lock with `git worktree unlock <path>`, verify it is gone, then remove only that exact worktree with `git worktree remove <path>` and no force option.
  If the lock reason differs, is unreadable, or either Git command refuses, stop and preserve the remaining state.
  Do not directly edit Git administration data or quarantine contents.
  After a crash, inspect `wtctl list --orphans`; adopt a dead-owner task only with explicit user authorization and `wtctl adopt --repo <repo> --id <worktree-id>`.
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
  If WTCTL refuses removal, preserve the worktree; this exception never authorizes manual worktree deletion.
- After a crash, use `wtctl list --orphans`; adopt a dead-owner task only with explicit user authorization and `wtctl adopt --repo <repo> --id <worktree-id>`.
- Use `wtctl reap` only for safe dead-owner worktrees after its grace period.
- Use `wtctl list --all` and `wtctl whoami` for task ownership/status. Legacy
  session-owned worktrees are visible to wtctl and must be managed with the
  exact worktree ID or branch selector; do not use Python fallback tools.
- The `worktree_guard.py` hook protects main checkouts and Git internals. Do not
  bypass it with Bash, shell redirection, direct Git administration commands,
  `--no-verify`, or edits in Git directories. The only exceptions are the exact
  artifact fallback and manual failed-merge abort procedures above, each limited
  to its named commands and checks. The failed-merge exception does not permit
  manual `git worktree remove`, force, hook suppression, or Git-administration
  edits. Resolve conflicts only in the task/integration worktree and retry
  `wtctl finish` after a safety refusal is addressed.

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
