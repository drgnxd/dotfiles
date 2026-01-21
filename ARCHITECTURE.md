# Architecture Overview

## Design Principles

### 1. **XDG Base Directory Compliance**
All configuration files follow the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):

```
$XDG_CONFIG_HOME (~/.config)  → Application configuration
$XDG_CACHE_HOME (~/.cache)    → Non-essential cached data
$XDG_DATA_HOME (~/.local/share) → User-specific data files
```

**Benefits**:
- Clean home directory
- Predictable file locations
- Easy backup/sync

### 2. **Security-First Design**
- **Guard Flags**: Destructive operations require explicit environment variables
- **Fail-Safe**: Scripts exit on error (`set -euo pipefail`)
- **Secrets Exclusion**: `.chezmoiignore.tmpl` prevents sensitive files from being tracked

### 3. **Platform Independence**
- Conditional inclusion via chezmoi templates
- Platform-specific scripts in `.internal_scripts/darwin/`
- Shared tools configured for both macOS and Linux

### 4. **Idempotency**
All scripts can run multiple times safely:
- Checks before modifications
- Non-destructive defaults
- State-based execution (`run_onchange_` scripts)

---

## Directory Structure

```
~/.local/share/chezmoi/         # chezmoi source directory
├── .chezmoiignore.tmpl         # Platform-specific exclusions
├── .internal_scripts/
│   ├── darwin/                 # macOS-only setup scripts
│   │   ├── system_defaults.sh  # UI/UX preferences
│   │   ├── security_hardening.sh # Firewall, remote access
│   │   ├── keyboard.sh         # Key repeat settings
│   │   ├── login_items.sh      # Startup applications
│   │   ├── menubar.sh          # Menu bar configuration
│   │   ├── audit_security.sh   # Security posture check
│   │   ├── install_packages.sh.tmpl # Brewfile execution
│   │   ├── import_stats.sh.tmpl # Stats app config
│   │   └── setup_cloud_symlinks.sh.tmpl # iCloud/Dropbox links
│   └── lib/
│       └── common.sh           # Shared bash functions
├── dot_config/                 # → ~/.config/
│   ├── alacritty/              # Terminal emulator
│   ├── bat/                    # Syntax-highlighted cat
│   ├── gh/                     # GitHub CLI
│   ├── git/                    # Version control
│   │   ├── config              # Main config
│   │   └── config.local.example # User-specific template
│   ├── hammerspoon/            # macOS automation (Lua)
│   ├── helix/                  # Text editor
│   ├── homebrew/               # Package manager
│   │   └── Brewfile.tmpl       # Package definitions
│   ├── npm/                    # Node.js packages
│   ├── opencode/               # AI coding agent
│   ├── starship/               # Shell prompt
│   ├── stats/                  # System monitor (plist)
│   ├── taskwarrior/            # Task management
│   │   ├── hooks/              # Python hooks + cache system
│   │   └── CACHE_ARCHITECTURE.md # Documentation
│   ├── tmux/                   # Terminal multiplexer
│   ├── yazi/                   # File manager
│   └── zsh/                    # Shell configuration
│       ├── .zshrc.tmpl         # Entry point
│       ├── .functions          # Custom functions
│       ├── .aliases            # Command shortcuts
│       ├── .exports            # Environment variables
│       └── fsh/                # Syntax highlighting chromas
├── dot_zshenv                  # → ~/.zshenv (XDG setup)
├── run_onchange_after_setup.sh.tmpl # Post-apply orchestrator
├── README.md / README.ja.md    # Bilingual documentation
├── CONTRIBUTING.md             # Development guide
└── ARCHITECTURE.md             # This file
```

---

## Security Model

### Guard Flag System

**Purpose**: Prevent accidental execution of system-modifying scripts

**Implementation**:
```bash
# In script
require_flag "ALLOW_DEFAULTS" "macOS defaults変更"

# User execution
ALLOW_DEFAULTS=1 ./script.sh
```

**Flags**:
| Flag | Script | Risk Level |
|------|--------|-----------|
| `ALLOW_DEFAULTS` | system_defaults.sh | Medium |
| `ALLOW_HARDEN` | security_hardening.sh | High |
| `ALLOW_GUI` | login_items.sh | Low |
| `ALLOW_KEYBOARD_APPLY` | keyboard.sh | Low |
| `FORCE` | setup_cloud_symlinks.sh | Medium |

### Secrets Management

**Exclusions** (`.chezmoiignore.tmpl`):
```
# User-specific configs
**config.local
**hosts.yml

# macOS-specific files (on Linux)
{{ if ne .chezmoi.os "darwin" }}
.internal_scripts/darwin
{{ end }}
```

**Proton Pass Integration**:
- SSH keys retrieved via `ppget` command
- Git signing configured in `config.local`
- Credentials never committed

---

## Platform Support

### macOS (darwin)

**Package Manager**: Homebrew (`Brewfile.tmpl`)

**System Integration**:
- `system_defaults.sh`: NSUserDefaults modifications
- `Hammerspoon`: Window management, input switching
- `Stats`: System monitor (plist-based config)

**Automation**:
- Login items managed via AppleScript
- Menu bar configuration via `defaults` command

### Linux

**Package Manager**: Native (apt/dnf/pacman)

**Shared Tools**:
- Alacritty, Zsh, Tmux, Helix
- Taskwarrior, Yazi, Starship
- All CLI tools (bat, eza, fd, ripgrep)

**Exclusions**:
- Hammerspoon (macOS-only)
- Homebrew (macOS-centric)
- `.internal_scripts/darwin/`

---

## Component Architecture

### 1. Zsh Ecosystem

**Entry Point**: `.zshrc.tmpl`
```zsh
source ~/.config/zsh/.exports    # Environment variables first
source ~/.config/zsh/.aliases    # Command shortcuts
source ~/.config/zsh/.functions  # Custom functions
source ~/.config/zsh/.zsh_plugins # Plugin management
```

**Plugin System**: zplug/zinit
- Fast Syntax Highlighting with 26 custom chromas
- zoxide (smart cd)
- fzf integration

**Module Design**:
- `.homebrew`: Homebrew-specific setup
- `.pyenv`: Python version management
- `.direnv`: Per-directory environment
- `.proton`: Proton Pass CLI wrapper

### 2. Taskwarrior Integration

**Architecture**: See `dot_config/taskwarrior/CACHE_ARCHITECTURE.md`

**Components**:
```
[Task add/modify]
      ↓
[Python Hooks] → update_cache.py → [Cache Files]
      ↓                                    ↓
[Zsh Functions] ← [Fast Syntax Highlighting]
      ↓
[Live Preview + Validation]
```

**Features**:
- Real-time ID validation
- Mini-buffer preview
- Smart completion
- 1-second TTL cache

### 3. chezmoi Integration

**State Management**:
- `run_onchange_` scripts execute when source changes
- Template hash tracking prevents redundant execution

**Templates**:
```
dot_config/homebrew/Brewfile.tmpl
  → Rendered during brew bundle
  → Hash-based change detection

run_onchange_after_setup.sh.tmpl
  → Orchestrates all setup scripts
  → Conditional platform execution
```

---

## Key Technical Decisions

### 1. Why XDG Base Directory?
- **Standard**: Widely adopted across Linux/Unix tools
- **Clean**: Keeps `~` clutter-free
- **Portable**: Easy to sync dotfiles

### 2. Why Guard Flags over Prompts?
- **Non-Interactive**: Scripts run without user input
- **Explicit**: User must consciously enable dangerous operations
- **Automation-Friendly**: CI/CD compatible

### 3. Why Separate Common Library?
- **DRY Principle**: 9 scripts shared 200+ lines of code
- **Consistency**: Unified error messages and logging
- **Maintainability**: Bug fixes propagate to all scripts

### 4. Why Taskwarrior Cache System?
- **Performance**: `task export` takes 100-500ms
- **Responsiveness**: Cache read takes <1ms
- **User Experience**: Instant feedback vs. noticeable lag

---

## Performance Optimizations

### 1. Zsh Startup Time
- Lazy-load heavy plugins
- Minimal `.zshrc` (delegates to modules)
- Compiled `.zshrc.zwc` via zcompile

### 2. Taskwarrior
- Cache TTL (1 second) prevents redundant reads
- Python hooks use `subprocess.DEVNULL` for silent operation
- Non-blocking cache updates

### 3. Homebrew
- `run_onchange` executes only when Brewfile changes
- Parallel installation where possible
- Auto-update via `homebrew-autoupdate`

---

## Future Enhancements

**Considered but not implemented**:
- [ ] Multi-machine profiles (work/personal)
- [ ] Automated backup via git hooks
- [ ] Ansible playbook for initial system setup
- [ ] Docker-based testing environment

---

## Reference

**Related Documentation**:
- [Taskwarrior Cache Architecture](dot_config/taskwarrior/CACHE_ARCHITECTURE.md)
- [FSH Chroma Guide](dot_config/zsh/fsh/README.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Commit Convention](COMMIT_CONVENTION.md)

**External Resources**:
- [chezmoi Documentation](https://www.chezmoi.io/)
- [XDG Base Directory Spec](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Last Updated**: 2026-01
**Author**: drgnxd
**License**: MIT
