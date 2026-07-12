## Guard Flag System
Most system changes are applied declaratively through Nix. The only interactive helper that requires a guard flag is the cloud symlink script.

| Flag | Script | Purpose |
|------|--------|---------|
| `FORCE=1` | `scripts/darwin/setup_cloud_symlinks.sh` | Cloud storage symlink creation |

## Secrets Management
Secrets are stored in `secrets/*.age`, managed with `agenix`, and defined at the home-manager layer in `home/modules/secrets.nix` for both macOS and Linux. Do not commit plaintext secrets. Encrypted files are decrypted at activation time to user config paths.

## Dependency Update Automation
Dependabot checks GitHub Actions weekly and groups minor and patch updates into one pull request. Major updates stay as individual pull requests for manual review. The weekly flake.lock update workflow also opens an automated pull request. Both automated dependency PR types are only queued for auto-merge after required CI passes; branch protection remains the gate.

Security and lint tool binaries used by CI, including `gitleaks` and `actionlint`, resolve from `flake.lock` through `nix run --inputs-from .`, so tool versions move with the weekly flake.lock update instead of manual checksum edits.

## Default Branch Ruleset
The default branch is protected by a GitHub repository ruleset that requires changes to arrive through a pull request and pass the configured required status checks.

The repository admin role is on that ruleset's bypass list with `bypass_mode: always`. This permits direct pushes to the default branch and skips both the pull-request requirement and the required status checks. Direct pushes by the admin are not gated by CI. CI still runs on push, so failures are detected after the fact, not prevented. A broken default branch will cause subsequent automated dependency pull requests to fail CI for reasons unrelated to the dependency update.

Automated pull requests, including Dependabot and the flake.lock updater, are not on the bypass list and remain fully gated by the required checks. This preserves the reason the ruleset exists: `gh pr merge --auto` merges immediately when no required status checks are configured.

## Rationale
- Declarative activation replaces ad-hoc scripts
- Explicit intent is required for interactive symlink creation
- Secrets remain encrypted in the repository
- Dependency automation reduces stale tooling while keeping major version changes under review
