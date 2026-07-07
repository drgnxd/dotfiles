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

## Rationale
- Declarative activation replaces ad-hoc scripts
- Explicit intent is required for interactive symlink creation
- Secrets remain encrypted in the repository
- Dependency automation reduces stale tooling while keeping major version changes under review
