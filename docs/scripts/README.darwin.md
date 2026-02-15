# macOS Scripts

This directory documents the remaining macOS helper scripts. Most system configuration is now declarative through nix-darwin and home-manager.

## Current Script

- `scripts/darwin/setup_cloud_symlinks.sh`
  - Interactive helper to create symlinks from `~/Library/CloudStorage` into `$HOME`
  - Guarded by `FORCE=1`

## Where macOS settings live

- `hosts/macbook/default.nix`
  - System defaults and security hardening
  - LaunchAgents and login item behavior
  - Homebrew casks/MAS for GUI apps

- `home/default.nix`
  - Home Manager user entrypoint (imports user modules)

- `home/modules/activation.nix`
  - User-level defaults (Finder/Dock/menu bar)
  - Stats.app configuration import
  - Legacy LaunchAtLogin agents for Stats/Hammerspoon are disabled and archived to prevent duplicate app launches

## Usage
```bash
FORCE=1 scripts/darwin/setup_cloud_symlinks.sh
```

## Related Documentation
- [Repository Architecture](../../ARCHITECTURE.md)
- [Security Model](../architecture/security-model.md)
