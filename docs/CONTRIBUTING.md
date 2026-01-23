# Contributing Guide

## Development Setup

### Prerequisites
- macOS or Linux
- [chezmoi](https://www.chezmoi.io/) installed
- Git

### Initial Setup
```bash
# Clone and apply
chezmoi init --apply drgnxd

# Or fork your own
chezmoi init --apply yourusername
```

---

## Brewfile Management

### Declarative Workflow (Recommended)

1. **Edit the Brewfile**
   ```bash
   chezmoi edit dot_config/homebrew/Brewfile
   ```

2. **Apply changes**
   ```bash
   chezmoi apply
   # This triggers run_onchange script to execute brew bundle
   ```

### Imperative Workflow

Capture currently installed packages:
```bash
brew bundle dump --file="$(chezmoi source-path)/dot_config/homebrew/Brewfile" --force --describe
```

### Sync Check

**Check missing packages**:
```bash
brew bundle check --file="$(chezmoi source-path)/dot_config/homebrew/Brewfile" --verbose
```

**Check unmanaged packages**:
```bash
brew bundle cleanup --file="$(chezmoi source-path)/dot_config/homebrew/Brewfile"
```

---

## Commit Convention

Follow [Conventional Commits](./COMMIT_CONVENTION.md):

### Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting (no code logic change)
- **refactor**: Code restructuring
- **perf**: Performance improvement
- **test**: Adding tests
- **chore**: Build/tool changes

### Examples
```bash
feat(zsh): add Taskwarrior cache system
fix(hammerspoon): correct window calculation for ultra-wide monitors
docs(readme): update installation instructions
refactor(scripts): extract common functions to lib/common.sh
```

---

## Testing Locally

### Before Committing

1. **Check diff**
   ```bash
   chezmoi diff
   ```

2. **Dry run**
   ```bash
   chezmoi apply --dry-run --verbose
   ```

3. **Apply to test system**
   ```bash
   chezmoi apply
   ```

### Script Testing

**macOS setup scripts** (use with caution):
```bash
# With safety flags
ALLOW_DEFAULTS=1 .internal_scripts/darwin/system_defaults.sh
ALLOW_HARDEN=1 .internal_scripts/darwin/security_hardening.sh
```

**Python hooks**:
```bash
python3 dot_config/taskwarrior/hooks/update_cache.py < /dev/null
```

**Bash common library**:
```bash
source .internal_scripts/lib/common.sh
log_info "Testing common library"
```

---

## Security Best Practices

### Guard Flags

Destructive operations require environment variable confirmation:

| Flag | Purpose |
|------|---------|
| `ALLOW_DEFAULTS=1` | macOS defaults write |
| `ALLOW_HARDEN=1` | Security hardening |
| `ALLOW_GUI=1` | Login items modification |
| `ALLOW_KEYBOARD_APPLY=1` | Keyboard settings |
| `FORCE=1` | Cloud symlink creation |

### Sensitive Files

Files excluded via `.chezmoiignore.tmpl`:
- `**/config.local`
- `**/hosts.yml`
- Private keys

Use `private_` prefix for template files containing secrets.

---

## Code Style

### Shell Scripts
- Use `#!/bin/bash` or `#!/bin/sh`
- `set -euo pipefail` for error handling
- Source common library: `source "$(dirname "$0")/../lib/common.sh"`
- Use logging functions: `log_info`, `log_error`, `log_success`

### Python
- PEP 8 compliant
- Type hints for public functions
- Docstrings for modules and functions

### Lua (Hammerspoon)
- 2-space indentation
- Comment complex calculations
- Module pattern (`local M = {}; return M`)

---

## Pull Request Process

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes following conventions
3. Test locally (`chezmoi apply`)
4. Commit with conventional format
5. Push and create PR with description

---

## Questions?

Open an issue for:
- Feature requests
- Bug reports
- Documentation improvements
- General questions

---

**Last Updated**: 2026-01
