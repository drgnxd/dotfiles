# Repository Rules

This repository is a cross-platform Nix flake for dotfiles: nix-darwin on `aarch64-darwin` and standalone home-manager on `x86_64-linux` with Hyprland.

## Apply Commands

- macOS: `sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.`
- Linux: `home-manager switch --flake path:.#<user>@<host>`
- Use `path:.` rather than `.#` when local evaluation must see gitignored files such as `local/identity.nix`.

## Verification Gates

- Scope gates to what changed; avoid unrelated formatting or rebuild churn.
- For `.nix` changes, run `just fmt-check`, `just lint`, and `just dead`.
- For `.sh` changes, run `shfmt -d` on the changed shell files, or the repo-wide shell check when CI parity is needed.
- For workflow changes, run `actionlint`.
- For `dot_config/opencode/**`, run `uv run --directory dot_config/opencode python validate_opencode_setup.py`.
- For Nushell files, run `nu --check` for full files and `nu --ide-check` when JSON diagnostics are needed.

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
- `AGENTS.md`, `command/`, and managed skill directories deploy as read-only Nix-store symlinks.
- `opencode.json`, `package.json`, and `tools/` deploy as activation-synced real files.
- `tools/` must remain real files because Bun resolves imports from realpaths and must walk up to `node_modules`.
- `skills/local/` is user-owned and seeded non-destructively; do not rewrite local skill contents from repo automation.

## Secrets

- Secrets are agenix-managed; never commit plaintext secrets.
- The detect-secrets baseline governs allowlisted findings.
- Update the baseline only when an intentional, reviewed allowlist changes.
