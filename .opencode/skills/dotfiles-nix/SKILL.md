---
name: dotfiles-nix
description: Use when changing this repository's Nix flakes, nix-darwin, home-manager modules, deployment behavior, or platform-specific configuration.
---

# Dotfiles Nix Maintenance

This repository is a cross-platform Nix flake: nix-darwin on macOS and
standalone Home Manager on Linux.

- Use `path:.` for local evaluation because `local/identity.nix` may be ignored.
- Resolve flake attribute names dynamically with `builtins.attrNames`; never
  hardcode user or host names.
- For pure refactors, compare affected `.drvPath` values before and after. Do
  not expect equality when the managed closure changes.
- Determinate Nix owns the daemon, so nix-darwin `nix.enable = false` makes its
  `nix.gc` and `nix.settings` options inert. Use Determinate's supported
  configuration or user-level services instead.
- Keep macOS system settings in nix-darwin and user settings in Home Manager.
- Put GUI app bundles in Homebrew casks and CLI tools in Nix packages.

Run the Nix validation gates declared in the repository `AGENTS.md` for changed
Nix files. Apply macOS changes with the documented `darwin-rebuild` command.
