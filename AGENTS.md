# Repository Rules

This repository is a cross-platform Nix flake for dotfiles: nix-darwin on `aarch64-darwin` and standalone home-manager on `x86_64-linux` with Hyprland.

## Apply Commands

- macOS: `sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.`
- Linux: `home-manager switch --flake path:.#<user>@<host>`
- Use `path:.` rather than `.#` when local evaluation must see gitignored files such as `local/identity.nix`.

## Verification Gates

- Scope gates to what changed; avoid unrelated formatting or rebuild churn.
- For `.nix` changes, run `just fmt-check`, `just lint`, and `just dead`.
- For Python under `dot_config/opencode`, run `just lint`; it runs the same `ruff check` as CI.
- `fmt-check`, `lint`, and `dead` do not evaluate the configuration. For `.nix` changes that alter module output, also evaluate the full target (`nix eval --raw path:.#darwinConfigurations.darwin.system.drvPath` on macOS) and build the changed artifact.
- For `.sh` changes, run `shfmt -d` on the changed shell files, or the repo-wide shell check when CI parity is needed.
- For workflow changes, run `actionlint`.
- For `dot_config/opencode/**`, run `uv run --directory dot_config/opencode python validate_opencode_setup.py`.
- For a helper under `dot_config/opencode/skills/*/scripts/`, also run its `just test-*` recipe (for `git-workflow`: `just test-worktree-remove`).
- For Nushell files, run `nu --ide-check 1000 <file>` and treat any `"severity":"Error"` entry as a failure; newer Nushell releases dropped `nu --check`, which CI uses only when available.

## Refactor Discipline

- Pure refactors should assert byte-equal `.drvPath` values for the affected Nix target before and after the change.
- Behavior-changing phases should gate on successful build or evaluation plus relevant linters.
- drvPath equality is not expected when the managed closure legitimately changes.

## Identity

- Never hardcode usernames or hostnames.
- Resolve flake attribute names dynamically with `builtins.attrNames` when a command needs a target.

## Documentation

- EN/JA paired docs must be updated together; the doc-pair CI check defines the authoritative pairs.
- Keep paired docs structurally aligned enough for the doc-pair warning check: headings and fenced blocks should match.

## OpenCode Assets

- Edit OpenCode sources under `dot_config/opencode/`; do not edit deployed files under `~/.config/opencode/`.
- `dot_config/opencode/global_rules.md` is concatenated with the git-ignored `~/.config/opencode/AGENTS.local.md` during activation and deployed as a writable real file `~/.config/opencode/AGENTS.md`.
- Global skills under `dot_config/opencode/skills/` deploy as read-only Nix-store symlinks. Repository-local skills under `.opencode/skills/` do not deploy globally.
- `opencode.json`, `package.json`, and `tools/` deploy as activation-synced real files.
- `tools/` must remain real files because Bun resolves imports from realpaths and must walk up to `node_modules`.

## Public Repository Boundary

- This repository is public. Never commit service names, domains, origins, personal automation job names, host names, or account identifiers, including in commit messages, branch names, tags, and PR or issue text.
- Declarative wiring belongs here, together with tooling that maintains or verifies this repository itself (CI, hooks, validators, activation scripts, `just` helpers).
- A helper whose only caller is one global skill's `SKILL.md` is bundled in that skill's `scripts/` directory with its tests beside it. "Only caller" is checked with a search: no launchd job, activation script, CI, other skill, `opencode.json` or `tools/` entry references it. It must run without installing packages (standard library, or `uv run --script` inline metadata), and a `just test-*` recipe runs its tests. A helper used by more than one skill, or by a repository-local skill, belongs in its own repository.
- Code belongs in its own repository, with any sync or deploy logic for it (this repository keeps only a thin declaration that invokes it), when it keeps state across runs (locks, markers, caches included), runs on a schedule, stores or refreshes credentials itself, runs as a server, MCP server, or client-registered tool, drives an authenticated external session, targets a specific private service, or has other consumers. Using the caller's ambient login (for example `gh`) does not count as handling credentials.
- Having tests or being long does not decide placement, but a bundled helper that grows past one file or adds a third-party dependency goes through `independent-review` before it stays here.
- Keep private values in `local/` or a state directory and read them at runtime, not as defaults in code.
- Keep the private term list outside the repo at `${XDG_CONFIG_HOME:-~/.config}/dotfiles-private/public-boundary-terms` (one extended regex per line, matched case-insensitively). `scripts/check-private-terms.sh` scans tracked files, commit messages, and pushed ranges with it; the hooks fail when the list is missing outside CI.
- Before any push, scan commit messages and ref names as well as diffs, and cover punctuation variants of every term (hyphen, space, underscore, full-width, katakana).

## Secrets

- Secrets are agenix-managed; never commit plaintext secrets.
- Before committing, run `uv tool run detect-secrets scan --baseline .secrets.baseline`.
- When a change adds, removes, or moves a detected value, review the regenerated `.secrets.baseline` and stage its semantic changes in the same commit.
- Do not stage timestamp-only changes to `.secrets.baseline`; stage reviewed finding additions, removals, or location updates.
