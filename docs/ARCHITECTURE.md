# Architecture Overview

## Quick Links
- [Nushell Configuration](architecture/nushell.md) - Modern shell with modular setup
- [XDG Base Directory Compliance](architecture/xdg-compliance.md)
- [Security Model and Guard Flags](architecture/security-model.md)
- [Platform Support](architecture/platform-support.md)
- [Taskwarrior Integration](architecture/taskwarrior.md)

## Design Principles
- XDG compliance for predictable config locations
- Security-first defaults with guarded interactive scripts
- Platform-aware configuration via Nix modules (nix-darwin + home-manager)
- Declarative activation with idempotent hooks

---

## Directory Structure

```
~/.config/nix-config/           # Nix flake repository
├── flake.nix                   # Entry point (nix-darwin + home-manager)
├── flake.lock                  # Pinned inputs
├── hosts/
│   └── macbook/default.nix     # nix-darwin system configuration
├── home/
│   ├── default.nix             # home-manager entrypoint (imports modules)
│   ├── packages.nix            # Package list
│   └── modules/
│       ├── activation.nix      # Activation hooks and user defaults
│       ├── xdg_config_files.nix # XDG configFile composition
│       ├── xdg_terminal_files.nix # Terminal/CLI config mappings
│       ├── xdg_editor_files.nix # Editor config mappings
│       ├── xdg_nushell_files.nix # Nushell config mappings
│       ├── xdg_yazi_files.nix  # Yazi config mappings
│       └── xdg_desktop_files.nix # Desktop app config mappings
├── dot_config/                 # Config sources (XDG)
│   ├── alacritty/              # Terminal emulator
│   ├── bat/                    # Syntax-highlighted cat
│   ├── gh/                     # GitHub CLI
│   ├── git/                    # Version control
│   │   ├── config              # Main config
│   │   └── config.local.example # User-specific template
│   ├── hammerspoon/            # macOS automation (Lua)
│   ├── helix/                  # Text editor
│   ├── npm/                    # Node.js packages
│   ├── opencode/               # AI coding agent
│   ├── starship/               # Shell prompt
│   ├── stats/                  # System monitor (plist)
│   ├── taskwarrior/            # Task management
│   │   ├── hooks/              # Python hooks + cache system
│   │   └── CACHE_ARCHITECTURE.md # Documentation
│   ├── zellij/                 # Terminal multiplexer
│   ├── yazi/                   # File manager
│   ├── nushell/                # Modern shell (see architecture/nushell.md)
│   │   ├── autoload/           # Modular configuration
│   │   │   ├── 01-env.nu       # Environment variables
│   │   │   ├── 02-path.nu      # PATH configuration
│   │   │   ├── 03-aliases.nu   # Command aliases
│   │   │   ├── 04-functions.nu # Custom functions
│   │   │   ├── 05-completions.nu # Command completions
│   │   │   ├── 06-integrations.nu # Integrations wrapper + Direnv init
│   │   │   ├── 07-source-tools.nu # Source cached tool init
│   │   │   ├── 08-taskwarrior.nu # Taskwarrior prompt preview
│   │   │   └── 09-lima.nu       # Lima/Docker helpers
│   │   ├── env.nu              # Entry point
│   │   └── config.nu           # Main config
├── scripts/
│   └── darwin/setup_cloud_symlinks.sh # Optional CloudStorage symlink helper
├── secrets/
│   └── secrets.nix             # agenix key map
├── docs/                       # Architecture notes
├── archive/                    # Archived legacy configs
│   └── zsh/                    # [ARCHIVED] Legacy Zsh configuration
├── README.md                   # Main README (English)
├── docs/README.ja.md           # Japanese README
└── docs/ARCHITECTURE.md        # This file
```

---

## Component Architecture

### 1. Nushell Ecosystem (Active)

See detailed documentation: [Nushell Configuration](architecture/nushell.md)

**Entry Points**:
- `env.nu` - Sources `autoload/01-env.nu` and `autoload/02-path.nu`
- `config.nu` - Loads autoload modules and local overrides

**Modular Architecture**:
```
autoload/
├── 01-env.nu           # XDG paths, ENV_CONVERSIONS
├── 02-path.nu          # PATH with path-add helper
├── 03-aliases.nu       # Conditional command aliases
├── 04-functions.nu     # Custom wrappers (yazi, zk, etc.)
├── 05-completions.nu   # Dynamic completions
├── 06-integrations.nu  # Integrations wrapper + Direnv init
├── 07-source-tools.nu  # Source cached tool init
├── 08-taskwarrior.nu   # Taskwarrior prompt preview
└── 09-lima.nu          # Lima/Docker helpers
```

**Key Features**:
- Everything is data (structured tables/records, not text)
- XDG Base Directory compliance
- Conditional command loading with fallbacks
- PATH helper with existence checks (`path-add`)
- Local overrides via `~/.config/nushell/local.nu` (empty file ensured during activation)

**Module Loading**:
```nushell
# env.nu
const config_dir = ($nu.home-dir | path join '.config' 'nushell')
source ($config_dir | path join 'autoload' '01-env.nu')
source ($config_dir | path join 'autoload' '02-path.nu')

# config.nu
const config_dir = ($nu.home-dir | path join '.config' 'nushell')
source ($config_dir | path join 'autoload' '00-constants.nu')
source ($config_dir | path join 'autoload' '00-helpers.nu')
...
```

Using `$nu.home-dir` to anchor module paths keeps loading stable even when active config files are loaded from Nix store paths.

### 2. Taskwarrior Integration
See [Taskwarrior Integration](architecture/taskwarrior.md).

### 3. Nix Integration

**Flake-based entrypoint**:
- `flake.nix` ties nix-darwin, home-manager, and agenix together
- `hosts/macbook/default.nix` owns system-level configuration
- `home/default.nix` composes user-level modules
- `home/modules/activation.nix` manages user defaults, launch-agent handling, and app setup hooks
- `home/modules/xdg_config_files.nix` composes XDG file mappings from focused `xdg_*_files.nix` lists

**Secrets**:
- Encrypted with `agenix` in `secrets/*.age`
- Decrypted into user config paths during activation

### 4. Container and Virtualization (Docker + Lima)

**Architecture**: XDG-compliant container environment without symlinks

**Configuration** (`dot_config/nushell/autoload/01-env.nu`):
```nushell
$env.DOCKER_CONFIG = ($env.XDG_CONFIG_HOME | path join "docker")
$env.LIMA_HOME = ($env.XDG_DATA_HOME | path join "lima")
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

**Management Functions** (`dot_config/nushell/autoload/09-lima.nu`):

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

### 3. Declarative macOS Configuration
- System defaults and launch agents via nix-darwin
- User-level configuration via home-manager

### 4. Taskwarrior Cache System
See [Taskwarrior Integration](architecture/taskwarrior.md).

### 5. No Symlinks for Docker/Lima
- Pure environment variable approach
- Less indirection and easier debugging

---

## Performance Optimizations

### 1. Nushell Startup
- Deterministic autoload order for fast init
- Cached tool init sourced from `~/.cache/nushell-init`
- Minimal runtime checks for optional tools

### 2. Taskwarrior
- Cache refresh is throttled and asynchronous (see taskwarrior doc)

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
- [Nushell Configuration](architecture/nushell.md)
- [Taskwarrior Cache Architecture](../dot_config/taskwarrior/CACHE_ARCHITECTURE.md)
- [FSH Chroma Guide](../archive/zsh/fsh/README.md) (Archived - Zsh)
- [Contributing Guide](CONTRIBUTING.md)
- [Commit Convention](COMMIT_CONVENTION.md)

## Archived Components

### Zsh Configuration (Legacy)

The Zsh configuration has been **archived** and migrated to Nushell. The previous setup included:

- **Entry Point**: `.zshrc.tmpl` with modular sourcing
- **Plugin System**: zplug/zinit with Fast Syntax Highlighting
- **Modules**: `.exports`, `.aliases`, `.functions`, `.zsh_plugins`
- **Completions**: Per-command completion definitions
- **Custom Themes**: 26 FSH chromas for syntax highlighting

**Migration Date**: 2026-01  
**Status**: Superseded by Nushell configuration  
**Access**: Available in git history if needed

**Key Differences from Zsh**:
| Feature | Zsh | Nushell |
|---------|-----|---------|
| Data Model | Text streams | Structured tables/records |
| Configuration | Multiple sourced files | Modular `autoload/` structure |
| Aliases | Simple string replacement | `export def` functions with logic |
| PATH Management | Manual string manipulation | `path-add` helper (prepend + exists check) |
| Environment | `.zshenv` + `.zshrc` | `env.nu` + `config.nu` |

---

**External Resources**:
- [Nix Manual](https://nixos.org/manual/nix/stable/)
- [nix-darwin](https://github.com/LnL7/nix-darwin)
- [home-manager](https://github.com/nix-community/home-manager)
- [XDG Base Directory Spec](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Last Updated**: 2026-01
**Author**: drgnxd
**License**: MIT
