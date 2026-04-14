# macOS Scripts

This directory documents the remaining macOS helper scripts. Most system configuration is now declarative through nix-darwin and home-manager.

## Current Script

- `scripts/darwin/setup_cloud_symlinks.sh`
  - Interactive helper to create symlinks from `~/Library/CloudStorage` into `$HOME`
  - Guarded by `FORCE=1`

## Where macOS settings live

- `hosts/macbook/default.nix`
  - System defaults and security hardening
  - Homebrew casks/MAS for GUI apps

- `hosts/macbook/launchd.nix`
  - nix-darwin LaunchAgent definitions and login app startup
  - Separately defines home-manager activation hooks that disable app-created legacy `LaunchAtLogin` agents (Stats/Hammerspoon)

- `home/default.nix`
  - Home Manager user entrypoint (imports user modules)

- `home/modules/activation/`
  - `directories.nix` (local directories bootstrap)
  - `macos_defaults.nix` (user-level defaults requiring `defaults -currentHost`)
  - `nushell_ensure.nix` (ensure `local.nu` and Nushell cache directories)
  - `opencode.nix` (OpenCode config and rules sync)
  - `taskwarrior_ensure.nix` (ensure local Taskwarrior overlay files)

## Usage
```bash
FORCE=1 scripts/darwin/setup_cloud_symlinks.sh
```

## Related Documentation
- [Repository Architecture](../ARCHITECTURE.md)
- [Security Model](../architecture/security-model.md)
