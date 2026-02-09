# Contributing Guide

## Development Setup

### Prerequisites
- macOS
- Nix (flakes enabled)
- Git

### Initial Setup
```bash
# Clone into the recommended location
git clone git@github.com:drgnxd/dotfiles.git ~/.config/nix-config

# Apply configuration
darwin-rebuild switch --flake ~/.config/nix-config#macbook
```

---

## Package Management

### CLI/TUI Packages
Packages are defined in `home/packages.nix`.

1. Edit `home/packages.nix`
2. Apply:
```bash
darwin-rebuild switch --flake ~/.config/nix-config#macbook
```

### macOS Apps (Casks/MAS)
GUI apps and MAS entries are managed in `hosts/macbook/default.nix` under `homebrew`.

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
feat(nushell): add Taskwarrior cache system
fix(hammerspoon): correct window calculation for ultra-wide monitors
docs(readme): update installation instructions
```

---

## Testing Locally

### Before Committing
1. **Build**
   ```bash
   darwin-rebuild build --flake ~/.config/nix-config#macbook
   ```

2. **Apply to test system**
   ```bash
   darwin-rebuild switch --flake ~/.config/nix-config#macbook
   ```

### Scripts
**Cloud symlink setup** (interactive, guarded):
```bash
FORCE=1 scripts/darwin/setup_cloud_symlinks.sh
```

### Python hooks
```bash
uv run --quiet --script dot_config/taskwarrior/hooks/update_cache.py --update-only
```

---

## Security Best Practices

### Secrets
Secrets are stored in `secrets/*.age` and managed with `agenix`. Do not commit plaintext secrets.

### Local Overrides
Local, machine-specific overrides live outside the repo (examples):
- `~/.config/nushell/local.nu`
- `~/.config/taskwarrior.local.rc`

---

## Code Style

### Shell Scripts
- Use `#!/bin/bash` with `set -euo pipefail`
- Avoid destructive operations without explicit guard flags

### Python
- Use `uv` for dependency management
- PEP 8 compliant
- Type hints for public functions

### Lua (Hammerspoon)
- 2-space indentation
- Comment complex calculations
- Module pattern (`local M = {}; return M`)

---

## Pull Request Process

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes following conventions
3. Build locally (`darwin-rebuild build`)
4. Commit with conventional format
5. Push and create PR with description

---

## Questions?

Open an issue for:
- Feature requests
- Bug reports
- Documentation improvements
- General questions
