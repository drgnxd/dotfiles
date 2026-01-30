# Architecture Overview

## Quick Links
- [XDG Base Directory Compliance](architecture/xdg-compliance.md)
- [Security Model and Guard Flags](architecture/security-model.md)
- [Platform Support](architecture/platform-support.md)
- [Taskwarrior Integration](architecture/taskwarrior.md)

## Design Principles
- XDG compliance for predictable config locations
- Security-first guard flags for destructive operations
- Platform-aware configuration via chezmoi templates
- Idempotent scripts safe to re-run with state checks

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
├── dot_config/                 # -> ~/.config/
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
│       ├── .zshrc.tmpl         # Main entry point
│       ├── .zshenv             # Environment variables
│       ├── .exports            # PATH and env vars
│       ├── .aliases            # Command shortcuts
│       ├── .functions          # Custom functions
│       ├── .zsh_options        # Zsh settings
│       ├── .zsh_completion     # Completion system
│       ├── .zsh_plugins        # Plugin management
│       ├── .completions/       # Per-command completions
│       ├── .homebrew           # Homebrew setup
│       ├── .pyenv              # Python version management
│       ├── .zoxide             # Smart cd
│       ├── .proton             # Proton Pass integration
│       ├── .lima               # Lima/Docker functions
│       ├── .fzf / .fzf_theme   # FZF integration and theme
│       ├── .direnv             # Per-directory environments
│       └── fsh/                # Fast Syntax Highlighting chromas
├── dot_zshenv                  # -> ~/.zshenv (XDG setup)
├── run_onchange_after_setup.sh.tmpl # Post-apply orchestrator
├── README.md / README.ja.md    # Bilingual documentation
├── CONTRIBUTING.md             # Development guide
└── ARCHITECTURE.md             # This file
```

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
See [Taskwarrior Integration](architecture/taskwarrior.md).

### 3. chezmoi Integration

**State Management**:
- `run_onchange_` scripts execute when source changes
- Template hash tracking prevents redundant execution

**Templates**:
```
dot_config/homebrew/Brewfile.tmpl
  -> Rendered during brew bundle
  -> Hash-based change detection

run_onchange_after_setup.sh.tmpl
  -> Orchestrates all setup scripts
  -> Conditional platform execution
```

### 4. Container and Virtualization (Docker + Lima)

**Architecture**: XDG-compliant container environment without symlinks

**Configuration** (`dot_config/zsh/.exports`):
```bash
export DOCKER_CONFIG="$XDG_CONFIG_HOME/docker"    # ~/.config/docker
export LIMA_HOME="$XDG_DATA_HOME/lima"            # ~/.local/share/lima
```

**Directory Structure**:
```
~/.config/docker/
  ├── config.json           # Docker CLI config (contexts, auth)
  └── contexts/             # Docker context definitions
      └── meta/*/meta.json  # Context metadata (endpoints)

~/.local/share/lima/
  ├── _config/              # Lima global config
  └── <vm-name>/            # VM instances (e.g., myvm, dev, prod)
      ├── lima.yaml         # VM configuration (CPUs, memory, mounts)
      ├── sock/docker.sock  # Docker socket (if Docker enabled in VM)
      ├── diffdisk          # VM disk image
      └── ...               # VM runtime data
```

**Management Functions** (`dot_config/zsh/.lima`):

| Function | Purpose | Example |
|----------|---------|---------|
| `lima-start <vm>` | Start VM and auto-switch Docker context | `lima-start dev` |
| `lima-stop <vm>` | Stop VM gracefully | `lima-stop dev` |
| `lima-status` (alias: `lls`) | List all VMs with status | `lls` |
| `lima-shell <vm>` | Open shell inside VM | `lima-shell dev` |
| `lima-delete <vm>` | Delete VM with confirmation | `lima-delete old-vm` |
| `docker-ctx <name>` (alias: `dctx`) | Switch Docker context | `dctx dev-context` |
| `docker-ctx-reset` | Reset to default context | `docker-ctx-reset` |
| `lima-docker-context <vm>` | Create/update Docker context for VM | `lima-docker-context dev` |

**Typical Workflow**:
```bash
# 1. Create Lima VM with Docker
limactl create --name=dev template://docker

# 2. Start VM (automatically switches Docker context if it exists)
lima-start dev

# 3. Create Docker context for the VM
lima-docker-context dev

# 4. Verify Docker connection
docker ps
docker info

# 5. Use Docker normally
docker run -d --name nginx nginx:alpine

# 6. Stop VM when done
lima-stop dev
```

**Design Benefits**:
- XDG compliance keeps paths portable
- No symlinks needed for Docker/Lima
- Multi-VM support with per-VM contexts

---

## Key Technical Decisions

### 1. XDG Base Directory
See [XDG Base Directory Compliance](architecture/xdg-compliance.md).

### 2. Guard Flags Over Prompts
See [Security Model and Guard Flags](architecture/security-model.md).

### 3. Separate Common Library
- Shared helpers reduce duplication across scripts
- Unified logging and guard behavior

### 4. Taskwarrior Cache System
See [Taskwarrior Integration](architecture/taskwarrior.md).

### 5. No Symlinks for Docker/Lima
- Pure environment variable approach
- Less indirection and easier debugging

---

## Performance Optimizations

### 1. Zsh Startup Time
- Lazy-load heavy plugins
- Minimal `.zshrc` (delegates to modules)
- Compiled `.zshrc.zwc` via zcompile

### 2. Taskwarrior
- Cache refresh is throttled and asynchronous (see taskwarrior doc)

### 3. Homebrew
- `run_onchange` executes only when Brewfile changes
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
