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

## Zsh
`ZDOTDIR` is set to `~/.config/zsh` through `/etc/zshenv` before macOS's
`/etc/zshrc` runs `compinit`; its completion dump therefore stays under the
XDG config directory. The managed `xdg/config/zsh/.zshrc` overrides the
system's `~/.zsh_history` default with `$XDG_STATE_HOME/zsh/history`:

```nix
environment.variables.ZDOTDIR = "$HOME/.config/zsh";
```

`ensureDirectories` pre-creates `~/.config/zsh` because `compinit` does not
create its target, and keeps the Zsh history directory and file at modes `0700` and `0600`.
Zsh does not automatically read `~/.profile`; it uses its own files under `ZDOTDIR`.

## macOS Applications
Homebrew trust operations receive `XDG_CONFIG_HOME` explicitly, so their state
stays under `~/.config/homebrew`. Alacritty declares XDG paths and the Home
Manager profile PATH directly because macOS
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
firefox-devtools-mcp restricts saved output (screenshots, snapshots) to
`~/.firefox-devtools-mcp` by design; lifting that requires
`--unrestrictedSavePaths`, which trades away a path-restriction safety
feature purely for tidiness, so the default location is kept.
SwiftPM only exposes `~/.swiftpm`'s three subpaths as per-invocation CLI
flags (`--cache-path`, `--config-path`, `--security-path`), not environment
variables, so there is nothing to redirect globally without wrapping the
`swift` binary itself.

## Decision Rationale
- Standard: aligns with widely adopted Linux/Unix conventions
- Clean: avoids legacy paths where upstream applications provide a supported alternative
- Portable: consistent behavior across machines
