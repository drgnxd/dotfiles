# dotfiles

My personal dotfiles managed with nix-darwin + standalone home-manager.

## Quick Start

For a fresh machine, see the [Bootstrap Guide](docs/architecture/bootstrap.md).

```bash
darwin-rebuild switch --flake ~/.config/nix-config#darwin
```

## Overview

This repository contains configurations for my macOS and Linux environments, including:

*   **Shell:** Nushell (modern shell with structured data, XDG-compliant, modular configuration)
    *   See [docs/architecture/nushell.md](docs/architecture/nushell.md) for details
    *   Key commands: `t` (task), `g` (ripgrep), `f` (fd), `cat` (bat), `y` (yazi), `update` (system upgrade)
    *   Includes all previous Zsh functionality migrated to Nushell
*   **Legacy Shell:** Zsh configuration is archived in git history
*   **Terminal:** Alacritty with Solarized Dark theme
*   **Browser:** Floorp (Privacy-focused Firefox-based browser, managed via Homebrew cask)
*   **Terminal Multiplexer:** Zellij
*   **Editor:** Helix with Readline-style insert-mode keybindings (Solarized Dark)
*   **File Manager:** Yazi with Solarized Dark flavor
*   **Window Manager:** Hammerspoon (macOS only)
*   **Linux Desktop (Phase 2):** Hyprland, Waybar, Wofi, fcitx5 + mozc, cliphist + wl-clipboard, hypridle + hyprlock, mako, grim + slurp, SwayOSD, Hyprpicker
*   **Package Manager:** Nix (nix-darwin + home-manager)
*   **Note Taking:** zk (Zettelkasten)
*   **Task Management:** Taskwarrior
*   **Development Tools:** Git (with delta, git-lfs, git-absorb, git-cliff), clang-tools, lldb, ast-grep, nix-diff, nix-tree, lazygit, gh, opencode (`oc`, `ocd` aliases), Guile (GNU Guile)
*   **Containers & Virtualization:** Lima (Linux virtual machines), Docker, Docker Compose
    *   Lima management: `lima-start`, `lima-stop`, `lls` (list VMs), `docker-ctx` (context switch)
    *   Fully XDG-compliant (`~/.config/docker/`, `~/.local/share/lima/`)
*   **Utilities:** atuin, bat, eza, fd, ripgrep, choose, sd, dust, duf, xh, jaq, grex, ncdu, tealdeer, tokei, typos, watchexec, hexyl, hyperfine, procs, smartmontools, age, direnv, shellcheck, pearcleaner, mas
*   **Version Managers:** uv (Python), node, rust
*   **3D/CAD & Simulation:** OrcaSlicer, ngspice, Kicad (PCB design), qFlipper (Device flasher)

## Installation

### Prerequisites

*   macOS or Linux (Ubuntu/Fedora/Arch)
*   Git
*   Nix (flakes enabled)

### Apply Configuration

```sh
darwin-rebuild switch --flake ~/.config/nix-config#darwin
```

### Local identity override (recommended)

Copy the example and set your machine-specific values:

```sh
cp local/identity.nix.example local/identity.nix
```

### Linux (standalone home-manager)

Make sure `local/identity.nix` matches your environment before applying.

```sh
home-manager switch --flake ~/.config/nix-config#<user>@<linuxHostname>
```

Linux support includes the core CLI/shell stack, Alacritty, and a Hyprland-based desktop environment.

## Post-Installation Setup

### Dependency Check

Verify required commands are available before running macOS setup scripts:

```sh
bash scripts/check_dependencies.sh
```

If any commands are missing, re-run darwin-rebuild to install packages:

```sh
darwin-rebuild switch --flake .#darwin
```

### Git Configuration

After installation, create a local git configuration file to set your user details:

```sh
cp ~/.config/git/config.local.example ~/.config/git/config.local
# Edit the file with your name and email
hx ~/.config/git/config.local
```

### Agenix Recipients (Required for Secrets)

> **Note**: Secrets are defined in the home-manager layer and are available on
> both macOS and Linux. Without valid SSH public keys in `secrets/secrets.nix`,
> encrypted secrets (git config, npmrc, gh hosts) will not be decrypted during
> activation. The configurations build normally, but these features will be
> unavailable.

Use `secrets/secrets.example.nix` as the template for recipient configuration.

If you use `agenix`, set your SSH public keys in `secrets/secrets.nix` before rekeying:

```nix
let
  darwin = "ssh-ed25519 AAAA...your-key...";
  linux = "ssh-ed25519 AAAA...your-key...";
in
...
```

An empty key list keeps fresh clones and CI checks portable; `just rekey` requires at least one real recipient key.

Existing `.age` payloads were encrypted for the previous recipient set; after setting real recipient keys locally, run `just rekey` to re-encrypt them. Rekeying requires the corresponding private key and must be done by the key holder.

### OpenCode Provider Override (Optional)

The base OpenCode config is managed from `dot_config/opencode/opencode.json`.
For machine-specific provider settings, edit `~/.config/opencode/opencode.local.json`.

- Read-only assets are symlinked from the Nix store: `AGENTS.md`, `opencode-notifier.json`, `requirements.txt`, `command/`, `skills/tools/`, and managed skill directories. Edit them in `dot_config/opencode/`, then rebuild or switch to apply changes.
- Writable files remain real files synced during activation: `opencode.json`, `opencode.local.json`, `opencode.local.json.example`, `package.json`, and `tools/`.
- `tools/` is synced as real files because a Nix-store realpath cannot walk up to `~/.config/opencode/node_modules` for Bun module resolution.
- During activation, if `~/.config/opencode/opencode.local.json` is non-empty, it is copied to `~/.config/opencode/opencode.json`; otherwise the managed template is copied instead.
- `skills/local/` stays user-owned and is seeded non-destructively for local skills.
- The managed OpenCode plugin list pins exact npm versions: `@mohak34/opencode-notifier@0.2.8` and `opencode-supermemory@2.0.6`.
- To bump a plugin, check the current version in `registry.npmjs.org`, update every plugin spec to the exact `@x.y.z` version, then rebuild the home-manager activation package.
- If `~/.config/opencode/opencode.local.json` is non-empty, make sure its `plugin` array still includes the managed plugins you want enabled.
- Rollback procedure: if OpenCode fails to write inside a symlinked directory, move that path back to the activation sync list in `home/modules/activation/opencode.nix`.

### Pre-commit Hooks (Optional)

pre-commit is optional. CI runs the same security scan and config validation.

If you want local hooks:

```sh
nix shell nixpkgs#pre-commit -c pre-commit install
```

To (re)generate the secrets baseline:

```sh
uv tool run detect-secrets scan --baseline .secrets.baseline
```

## Management

### Managing Nix Packages

Package definitions live in `home/packages.nix`.

#### Adding/Removing Packages

1. Edit `home/packages.nix`
2. Apply changes:

```sh
darwin-rebuild switch --flake .#darwin
```

#### Updating Inputs

```sh
nix flake update
darwin-rebuild switch --flake .#darwin
```

## Structure

*   `flake.nix`: Nix entrypoint (nix-darwin + home-manager).
*   `hosts/`: nix-darwin system configuration.
*   `home/`: Home-manager modules and package definitions.
*   `secrets/`: agenix encrypted secrets (optional).
*   `scripts/`: Platform helper scripts managed by Nix.
*   `.pre-commit-config.yaml`: Optional local hooks (detect-secrets, YAML/TOML checks, local validators).
*   `.secrets.baseline`: detect-secrets baseline for allowlisted findings.
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
    *   `zellij`: Configured through `home/modules/zellij.nix`
    *   `yazi/`: Blazing fast terminal file manager with custom theme
    *   `nushell/`: Modern shell configuration (see architecture/nushell.md)
        *   `autoload/`: Modular configuration files

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
*   **Auto Input Switching**: Automatically switches to English input for Alacritty and Sol (including Sol launch via Cmd+Space)
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
*   **PATH Helper**: Uses a small `path-add` helper to prepend existing paths in order
*   **Key Commands**:
    *   `t` - Taskwarrior
    *   `g` - Ripgrep search
    *   `f` - fd search
    *   `cat` - bat (fallback to cat)
    *   `la`, `ld`, `lf`, `lsize` - List variants
    *   `y` - Yazi file manager with cwd tracking
    *   `update` / `upgrade-all` - Unified system upgrade
*   **Auto-initialized Tools**: Starship, Zoxide, Direnv, Carapace, Atuin
*   **Local Overrides**: Support for unmanaged `~/.config/nushell/local.nu` for machine-specific settings (auto-created as an empty file during activation)
*   **Documentation**: See [docs/architecture/nushell.md](docs/architecture/nushell.md) for full details

### Helix language-server (LSP) support

This configuration enables additional language-server integrations for the Helix editor and documents the matching Nix packages. The repository includes recommended LSPs such as `pyright`, `ruff`, `marksman`, `taplo`, `lua-language-server`, `yaml-language-server`, and `texlab` via Nix packages. For Rust, `rust-analyzer` is expected via `rustup` (`rustup component add rust-analyzer`). See `dot_config/helix/` for editor settings and `home/packages.nix` for package declarations.

## License

MIT License
