---
name: git-workflow
description: Use before the first file edit or Git write in each repository for each task, whatever the task size. Not for read-only inspection or directories outside a Git work tree.
---

# Git Workflow

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
- Use only schema-1 `wtctl` for task worktree lifecycle. Before creating a
  worktree, run `wtctl capabilities --json` and verify it advertises `create`,
  `finish`, legacy lifecycle, Git-annex, artifact quarantine, and quarantine
  purge support. If these capabilities are unavailable, stop and request a
  package update; do not fall back to Python lifecycle scripts or manual
  `git worktree` operations.
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
  filters; use `--allow-commit-signing` only when the user authorized the
  repository's configured signer. Executable repository hooks block by
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
- `finish` discards recognized generated artifacts by default. Use
  `--preserve-generated-artifacts` to quarantine and retain recognized cache,
  build, and marked Nix-generated config paths. Unknown ignored/untracked data
  blocks cleanup. Recover a retained quarantine only with
  `wtctl remove --repo <repo> --purge-preserved-quarantine <operation-id>
  --external-writers-quiesced`; unverified `.direnv` additionally requires
  `--discard-unverified-direnv`. Do not use direct `remove` to select or discard
  task data unless the user explicitly approved those selectors.
- If any lifecycle command refuses, preserve the worktree and data, inspect the
  reported state, and report cleanup as incomplete. Never use `--force`, bypass
  a safety refusal, or manually delete worktree/quarantine data. After a crash,
  inspect `wtctl list --orphans`; adopt a dead-owner task only with explicit
  user authorization and `wtctl adopt --repo <repo> --id <worktree-id>`. Use
  `wtctl reap` only for safe dead-owner worktrees after its grace period.
- Use `wtctl list --all` and `wtctl whoami` for task ownership/status. Legacy
  session-owned worktrees are visible to wtctl and must be managed with the
  exact worktree ID or branch selector; do not use Python fallback tools.
- The `worktree_guard.py` hook protects main checkouts and Git internals. Do not
  bypass it with Bash, shell redirection, direct Git administration commands,
  `--no-verify`, or edits in Git directories. Resolve conflicts only in the
  task/integration worktree and retry `wtctl finish` after a safety refusal is
  addressed.

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
