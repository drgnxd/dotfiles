## Guard Flag System
Most system changes are applied declaratively through Nix. The only interactive helper that requires a guard flag is the cloud symlink script.

| Flag | Script | Purpose |
|------|--------|---------|
| `FORCE=1` | `scripts/darwin/setup_cloud_symlinks.sh` | Cloud storage symlink creation |

## Secrets Management
Secrets are stored in `secrets/*.age` and managed with `agenix`. Do not commit plaintext secrets. Encrypted files are decrypted at activation time to user config paths.

## Rationale
- Declarative activation replaces ad-hoc scripts
- Explicit intent is required for interactive symlink creation
- Secrets remain encrypted in the repository
