# XDG Base Directory Compliance

## Overview
All configuration follows the XDG Base Directory Specification to keep the home
directory clean and make data locations predictable across machines.

```
$XDG_CONFIG_HOME (~/.config)   -> Application configuration
$XDG_CACHE_HOME (~/.cache)     -> Non-essential cached data
$XDG_DATA_HOME (~/.local/share) -> User-specific data files
```

## Benefits
- Clean home directory with fewer dotfiles
- Predictable paths for backups and sync
- Portable configs across macOS and Linux

## Docker and Lima
Docker and Lima rely on environment variables instead of symlinks to keep the
layout consistent with XDG paths.

```bash
export DOCKER_CONFIG="$XDG_CONFIG_HOME/docker"
export LIMA_HOME="$XDG_DATA_HOME/lima"
```

## Decision Rationale
- Standard: aligns with widely adopted Linux/Unix conventions
- Clean: avoids legacy `~/.docker` and `~/.lima` directories
- Portable: consistent behavior across machines
