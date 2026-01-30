# Security Model and Guard Flags

## Guard Flag System
System-modifying scripts require explicit environment flags to prevent accidental
execution and to keep automation non-interactive.

```bash
# Example
ALLOW_DEFAULTS=1 ./system_defaults.sh
```

| Flag | Script | Risk Level |
|------|--------|-----------|
| `ALLOW_DEFAULTS` | system_defaults.sh | Medium |
| `ALLOW_HARDEN` | security_hardening.sh | High |
| `ALLOW_GUI` | login_items.sh | Low |
| `ALLOW_KEYBOARD_APPLY` | keyboard.sh | Low |
| `FORCE` | setup_cloud_symlinks.sh | Medium |

## Secrets Management
Sensitive or user-specific files are excluded via `.chezmoiignore.tmpl`.

```
**config.local
**hosts.yml
```

## Rationale
- Non-interactive scripts remain automation-friendly
- Explicit intent is required for destructive operations
- Centralized guard checks and helper functions live in `common.sh`
- User-context execution via `run_as_user <username> <command>` for multi-user safety
