# dotfiles

My personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

## Overview

This repository contains configurations for my macOS and Linux environments, including:

*   **Shell:** Zsh (with Starship prompt, zoxide, fzf)
*   **Terminal:** Alacritty with Tokyo Night theme
*   **Browser:** Floorp (Privacy-focused Firefox-based browser)
*   **Terminal Multiplexer:** Tmux with Vim-style keybindings
*   **Editor:** Helix with Emacs hybrid bindings
*   **File Manager:** Yazi with custom Tokyo Night flavor
*   **Window Manager:** Hammerspoon (macOS only)
*   **Package Manager:** Homebrew (macOS), Native Package Manager (Linux)
*   **Note Taking:** zk (Zettelkasten)
*   **Task Management:** Taskwarrior
*   **Development Tools:** Git (with delta, git-lfs), lazygit, gh, opencode (`oc`, `ocd` aliases), Guile (GNU Guile)
*   **Utilities:** bat, eza, fd, ripgrep, ncdu, smartmontools, direnv, pearcleaner
*   **Version Managers:** pyenv, node, rust
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


### Git Configuration


After installation, create a local git configuration file to set your user details:


```sh
cp ~/.config/git/config.local.example ~/.config/git/config.local
# Edit the file with your name and email
hx ~/.config/git/config.local
```



## Management

### Managing Homebrew Packages

This repository manages the `dot_Brewfile` directly within the `chezmoi` source directory, bypassing the home directory `.Brewfile`.

#### Adding/Removing Packages

**Recommended Workflow (Declarative):**

1. Edit the source file to add or remove packages:
    ```sh
    chezmoi edit dot_Brewfile
    ```
2. Apply changes to the system:
    ```sh
    chezmoi apply
    ```

**Alternative Workflow (Import Current State):**

To reflect manually installed packages into the configuration file:

```sh
# Overwrite dot_Brewfile with current system state (with descriptions)
brew bundle dump --file="$(chezmoi source-path)/dot_Brewfile" --force --describe
```

#### Checking Consistency

Verify discrepancies between the definition file (`dot_Brewfile`) and the current system state.

  * **Check for missing packages** (listed in Brewfile but not installed):

    ```sh
    brew bundle check --file="$(chezmoi source-path)/dot_Brewfile" --verbose
    ```

  * **Check for unmanaged packages** (installed but not listed in Brewfile):

    ```sh
    # List unmanaged packages without uninstalling (Dry Run)
    brew bundle cleanup --file="$(chezmoi source-path)/dot_Brewfile"
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
*   `dot_Brewfile`: List of Homebrew packages to install (macOS only).
*   `dot_config/`: Configuration files for various tools (XDG Base Directory compliant).
    *   `alacritty/`: GPU-accelerated terminal emulator configuration
    *   `fsh/`: Custom themes for Zsh Fast Syntax Highlighting
    *   `gh/`: GitHub CLI configuration
    *   `git/`: Git configuration with delta integration
    *   `hammerspoon/`: macOS automation (window management, input switching, caffeine mode)
    *   `helix/`: Post-modern modal text editor configuration
    *   `npm/`: Node.js package manager configuration
    *   `opencode/`: Configuration for OpenCode (AI coding agent)
    *   `starship/`: Cross-shell prompt configuration
    *   `stats/`: Configuration for Stats (system monitor)
    *   `taskwarrior/`: Task management configuration
    *   `tmux/`: Terminal multiplexer with Tokyo Night theme
    *   `yazi/`: Blazing fast terminal file manager with custom theme
    *   `zsh/`: Zsh configuration with plugins and completions
*   `run_onchange_darwin_install_packages.sh.tmpl`: Script that runs `brew bundle` after `chezmoi apply` (macOS only).

## Features

### Taskwarrior 

Enhanced Zsh integration for better task management: 

*   **Dynamic Syntax Highlighting**: Validates task IDs against the cache; valid IDs are highlighted, invalid ones are shown as subtle errors. 
*   **Live Preview**: Displays task descriptions in the command-line mini-buffer as you type task IDs. 
*   **Fast Completion**: Provides instantaneous completion candidates with task descriptions using a local cache. 
*   **Automatic Cache**: Python hooks automatically refresh the task cache on every add or modify operation. 


### Hammerspoon

Window management and automation features:

*   **Window Management** (Ctrl+Alt): Rectangle-style window resizing
    *   `←/→`: Left/right half screen
    *   `↑/↓`: Top/bottom half screen
    *   `Enter`: Maximize
    *   `U/I/J/K`: Quarter screen positions (top-left, top-right, bottom-left, bottom-right)
    *   `C`: Center (80% size)
*   **Auto Input Switching**: Automatically switches to English input for Alacritty and Sol
*   **Caffeine Mode**: Prevent display sleep via menubar icon (☕️/💤)
*   **Cheat Sheet** (Ctrl+Alt+/): Display all keybindings
*   **Auto Reload**: Configuration reloads automatically on file changes
*   **Manual Reload**: Ctrl+Shift+R to reload configuration

## License

MIT License
