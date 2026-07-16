# XDG Base Directory Compliance

## Overview
All configuration follows the XDG Base Directory Specification to keep the home
directory clean and make data locations predictable across machines.

```
$XDG_CONFIG_HOME (~/.config)   -> Application configuration
$XDG_CACHE_HOME (~/.cache)     -> Non-essential cached data
$XDG_DATA_HOME (~/.local/share) -> User-specific data files
$XDG_STATE_HOME (~/.local/state) -> Persistent application state
```

## Benefits
- Clean home directory with fewer dotfiles
- Predictable paths for backups and sync
- Portable configs across macOS and Linux

## Atuin
Atuin follows XDG paths for configuration and history data, but defaults file
logs to the legacy `~/.atuin/logs` directory. Home Manager overrides the log
directory to keep persistent logs under XDG state:

```toml
[logs]
dir = "~/.local/state/atuin/logs"
```

## macOS Applications
Homebrew trust operations receive `XDG_CONFIG_HOME` explicitly, so their state
stays under `~/.config/homebrew`. Hammerspoon uses its native `MJConfigFile`
preference to load `~/.config/hammerspoon/init.lua`; reload watchers derive the
directory from `hs.configdir` instead of relying on `~/.hammerspoon`. Alacritty
declares XDG paths and the Home Manager profile PATH directly because macOS
LaunchServices does not reliably preserve the per-user launchd environment.

## Docker and Lima
Docker and Lima rely on environment variables instead of symlinks to keep the
layout consistent with XDG paths.

```bash
export DOCKER_CONFIG="$XDG_CONFIG_HOME/docker"
export LIMA_HOME="$XDG_DATA_HOME/lima"
```

## Compatibility Exceptions
Ollama and Scilab retain home-directory compatibility links because their GUI
or non-model state is not fully redirectable. CodexBar currently hard-codes a
Claude OAuth lock under `~/.codexbar`. Determinate Nix retains its legacy user
profile shims because its XDG switch is a restricted system setting.

## Decision Rationale
- Standard: aligns with widely adopted Linux/Unix conventions
- Clean: avoids legacy paths where upstream applications provide a supported alternative
- Portable: consistent behavior across machines
