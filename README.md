# dotfiles

My personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

## Quick Start

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply drgnxd
```

## Overview

This repository contains configurations for my macOS and Linux environments, including:

*   **Shell:** Nushell (modern shell with structured data, XDG-compliant, modular configuration)
    *   See [docs/architecture/nushell.md](docs/architecture/nushell.md) for details
    *   Key commands: `ca` (chezmoi apply), `ce` (chezmoi edit), `t` (task), `g` (ripgrep), `f` (fd), `cat` (bat), `y` (yazi), `update` (system upgrade)
    *   Includes all previous Zsh functionality migrated to Nushell
*   **Legacy Shell:** Zsh configuration archived under `archive/zsh` (see git history if needed)
*   **Terminal:** Alacritty with Solarized Dark theme
*   **Browser:** Floorp (Privacy-focused Firefox-based browser)
*   **Terminal Multiplexer:** Tmux with Solarized Dark theme and Vim-style keybindings
*   **Editor:** Helix with Emacs hybrid bindings (Solarized Dark)
*   **File Manager:** Yazi with Solarized Dark flavor
*   **Window Manager:** Hammerspoon (macOS only)
*   **Package Manager:** Homebrew (macOS), Native Package Manager (Linux)
*   **Note Taking:** zk (Zettelkasten)
*   **Task Management:** Taskwarrior
*   **Development Tools:** Git (with delta, git-lfs), lazygit, gh, opencode (`oc`, `ocd` aliases), Guile (GNU Guile)
*   **Containers & Virtualization:** Lima (Linux virtual machines), Docker, Docker Compose
    *   Lima management: `lima-start`, `lima-stop`, `lls` (list VMs), `docker-ctx` (context switch)
    *   Fully XDG-compliant (`~/.config/docker/`, `~/.local/share/lima/`)
*   **Utilities:** atuin, bat, eza, fd, ripgrep, choose, sd, dust, duf, xh, jaq, grex, ncdu, smartmontools, direnv, shellcheck, pearcleaner, mas
*   **Version Managers:** uv (Python), node, rust
*   **3D/CAD & Simulation:** OrcaSlicer, ngspice, Kicad (PCB design), qFlipper (Device flasher)

## Installation

### Prerequisites

*   macOS or Linux
*   Git
*   curl/wget

### One-line Install

```sh
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply drgnxd
```

Or, if you have `chezmoi` installed already:

```sh
chezmoi init --apply drgnxd
```

## Post-Installation Setup

### Dependency Check

Verify required commands are available before running macOS setup scripts:

```sh
bash .internal_scripts/check_dependencies.sh
```

If any commands are missing, install them with:

```sh
brew bundle install
```

### Git Configuration

After installation, create a local git configuration file to set your user details:

```sh
cp ~/.config/git/config.local.example ~/.config/git/config.local
# Edit the file with your name and email
hx ~/.config/git/config.local
```

### Pre-commit Hooks (Optional)

pre-commit is optional. CI runs the same security scan and config validation.

If you want local hooks:

```sh
brew install pre-commit
pre-commit install
```

To (re)generate the secrets baseline:

```sh
uv tool run detect-secrets scan --baseline .secrets.baseline
```

## Management

### Managing Homebrew Packages

This repository manages `dot_config/homebrew/Brewfile` within the `chezmoi` source directory and uses `$XDG_CONFIG_HOME/homebrew/Brewfile` (default `~/.config/homebrew/Brewfile`) instead of `~/.Brewfile`.

**Execution flags (safety):**
- `run_onchange_after_setup.sh.tmpl`: orchestrates macOS setup steps; optional `CONTINUE_ON_ERROR=1` to continue after a failed step.
- `.internal_scripts/darwin/install_packages.sh.tmpl`: renders Brewfile and runs `brew bundle`. No extra flag.
- `.internal_scripts/darwin/import_stats.sh.tmpl`: fails if plist missing; exits non-zero.
- `.internal_scripts/darwin/setup_cloud_symlinks.sh.tmpl`: requires `FORCE=1` to create symlinks (interactive; non-symlink targets are skipped).
- `.internal_scripts/darwin/login_items.sh`: requires `ALLOW_GUI=1` to modify login items.
- `.internal_scripts/darwin/security_hardening.sh`: requires `ALLOW_HARDEN=1`; aggregates failures.
- `.internal_scripts/darwin/system_defaults.sh`: requires `ALLOW_DEFAULTS=1`. Optional flags: `ALLOW_LSQUARANTINE_OFF=1`, `ALLOW_SPOTLIGHT_DISABLE=1`. Applies Dock running-apps-only (`static-only`).
- `.internal_scripts/darwin/keyboard.sh`: requires `ALLOW_KEYBOARD_APPLY=1` when using `--apply`.
- `.internal_scripts/darwin/menubar.sh`: no extra flag.
- `.internal_scripts/darwin/audit_security.sh`: no extra flag.

#### Adding/Removing Packages

**Recommended Workflow (Declarative):**

1. Edit the source file to add or remove packages:
    ```sh
    chezmoi edit dot_config/homebrew/Brewfile
    ```
2. Apply changes to the system:
    ```sh
    chezmoi apply
    ```

**Alternative Workflow (Import Current State):**

To reflect manually installed packages into the configuration file:

```sh
# Overwrite Brewfile with current system state (with descriptions)
brew bundle dump --file="$(chezmoi source-path)/dot_config/homebrew/Brewfile" --force --describe
```

#### Checking Consistency

Verify discrepancies between the definition file (`dot_config/homebrew/Brewfile`) and the current system state.

  * **Check for missing packages** (listed in Brewfile but not installed):

    ```sh
    brew bundle check --file="$(chezmoi source-path)/dot_config/homebrew/Brewfile" --verbose
    ```

  * **Check for unmanaged packages** (installed but not listed in Brewfile):

    ```sh
    # List unmanaged packages without uninstalling (Dry Run)
    brew bundle cleanup --file="$(chezmoi source-path)/dot_config/homebrew/Brewfile"
    ```

#### Automatic Updates

This configuration includes `homebrew/autoupdate` to keep packages fresh.
To enable automatic updates (including GUI apps via `--greedy`), run:

```sh
brew autoupdate start 43200 --upgrade --cleanup --greedy
```

This will check for updates every 12 hours.

<!-- end list -->

## Structure

*   `.chezmoiignore.tmpl`: Template to ignore files based on OS (e.g. ignore macOS apps on Linux).
*   `.pre-commit-config.yaml`: Optional local hooks (detect-secrets, YAML/TOML checks, local validators).
*   `.secrets.baseline`: detect-secrets baseline for allowlisted findings.
*   `.chezmoidata.toml`: Shared Solarized palette used by templated configs (Alacritty, tmux, yazi).
*   `dot_config/homebrew/Brewfile`: List of Homebrew packages to install (macOS only).
*   `.internal_scripts/`: Internal macOS setup scripts (invoked by `run_onchange_after_setup.sh.tmpl`).
*   `docs/`: Architecture notes.
*   `dot_config/`: Configuration files for various tools (XDG Base Directory compliant).
    *   `alacritty/`: GPU-accelerated terminal emulator configuration
    *   `gh/`: GitHub CLI configuration
    *   `git/`: Git configuration with delta integration
    *   `hammerspoon/`: macOS automation (window management, input switching, caffeine mode)
    *   `helix/`: Post-modern modal text editor configuration
    *   `npm/`: Node.js package manager configuration
    *   `opencode/`: Configuration for OpenCode (AI coding agent)
    *   `starship/`: Cross-shell prompt configuration
    *   `stats/`: Configuration for Stats (system monitor)
    *   `taskwarrior/`: Task management configuration
    *   `tmux/`: Terminal multiplexer with Solarized Dark theme
    *   `yazi/`: Blazing fast terminal file manager with custom theme
    *   `nushell/`: Modern shell configuration (see architecture/nushell.md)
        *   `autoload/`: Modular configuration files
*   `archive/`: Archived legacy configurations
    *   `zsh/`: [ARCHIVED] Zsh configuration (migrated to Nushell)
*   `run_onchange_after_setup.sh.tmpl`: Orchestrates macOS setup steps after `chezmoi apply`.

## Features

### Taskwarrior

Taskwarrior cache system for fast, shell-agnostic integrations:

*   **Automatic Cache**: Python hooks refresh the cache on every add/modify operation
*   **Structured Outputs**: ID and description lists optimized for prompt/completion usage
*   **Legacy UI**: Zsh-specific highlighting/preview features are archived

### Hammerspoon

Window management and automation features:

*   **Window Management** (Ctrl+Alt): Rectangle-style window resizing
    *   `left/right`: Left/right half screen
    *   `up/down`: Top/bottom half screen
    *   `enter`: Maximize
    *   `U/I/J/K`: Quarter screen positions (top-left, top-right, bottom-left, bottom-right)
    *   `C`: Center (80% size)
*   **Auto Input Switching**: Automatically switches to English input for Alacritty and Sol
*   **Caffeine Mode**: Prevent display sleep via menubar icon (coffee/sleep)
*   **Cheat Sheet** (Ctrl+Alt+/): Display all keybindings
*   **Auto Reload**: Configuration reloads automatically on file changes
*   **Manual Reload**: Ctrl+Shift+R to reload configuration

### Nushell

Modern shell with structured data and modular configuration:

*   **Everything is Data**: Pipelines use structured data (tables, records) instead of plain text
*   **XDG Compliant**: All configuration follows XDG Base Directory specification
*   **Modular Architecture**: Configuration split across `autoload/` directory for maintainability
*   **Conditional Commands**: Smart fallbacks (`g` uses `rg`/`grep`, `f` uses `fd`/`find`, `cat` uses `bat`/`cat`)
*   **Standard Library**: Uses `std/util` for PATH management and other utilities
*   **Key Commands**:
    *   `ca`, `ce` - Chezmoi apply/edit
    *   `t` - Taskwarrior
    *   `g` - Ripgrep search
    *   `f` - fd search
    *   `cat` - bat (fallback to cat)
    *   `la`, `ld`, `lf`, `lsize` - List variants
    *   `y` - Yazi file manager with cwd tracking
    *   `update` / `upgrade-all` - Unified system upgrade
*   **Auto-initialized Tools**: Starship, Zoxide, Direnv, Carapace, Atuin
*   **Local Overrides**: Support for `~/.config/nushell/local.nu` for machine-specific settings
*   **Documentation**: See [docs/architecture/nushell.md](docs/architecture/nushell.md) for full details

### Helix language-server (LSP) support

This configuration enables additional language-server integrations for the Helix editor and documents the matching Homebrew packages. The repository now includes recommended LSPs such as `pyright`, `ruff`, `marksman`, `taplo`, `rust-analyzer`, `lua-language-server`, `yaml-language-server`, and `texlab`. See `dot_config/helix/` for editor settings and `dot_config/homebrew/Brewfile` for package declarations.

## License

MIT License
