---
name: nix
description: Use when working on Nix flakes, nix-darwin, or home-manager configurations — drvPath checks, path:. evaluation, Determinate Nix caveats, platform asymmetry, and packaging placement.
---

# Nix Flake Workflows

Use these notes for Nix flakes, nix-darwin, and home-manager work. Treat each item as point-in-time platform behavior and re-check before relying on it in a new repo.

# drvPath Refactor Checks

- For pure refactors, compare the target `.drvPath` before and after the change. Byte-equal drvPaths are a strong isolation assertion that evaluation output did not change. (verified 2025–2026; re-verify before relying)
- Do not expect drvPath equality when the managed closure legitimately changes, such as adding or removing Home Manager modules, packages, or skills. (verified 2025–2026; re-verify before relying)

# Flake Path Evaluation

- Use the `path:.` flake prefix when evaluation must see gitignored or untracked files, such as `local/identity.nix`. (verified 2025–2026; re-verify before relying)
- The `.#` form evaluates the git source and does not include ignored or untracked local files. (verified 2025–2026; re-verify before relying)

# Determinate Nix

- When Determinate Nix owns the daemon and nix-darwin sets `nix.enable = false`, nix-darwin `nix.gc` and `nix.settings` options are inert. Use the Determinate daemon's mechanisms or a user-level scheduled service instead. (verified 2025–2026; re-verify before relying)

# Platform Boundaries

- nix-darwin can declaratively control OS-layer macOS settings and services. Standalone home-manager is a user-layer manager only; proposals must respect that asymmetry. (verified 2025–2026; re-verify before relying)
- `system.keyboard.remapCapsLockToControl` has had reboot-persistence issues; prefer a `launchd.user.agents` `hidutil` agent when persistence matters. (verified 2025–2026; re-verify before relying)

# Package Placement

- GUI `.app` bundles belong in `homebrew.casks`; Launch Services can conflict with store-symlink placement. CLI tools belong in Nix packages. (verified 2025–2026; re-verify before relying)

# Desktop Environment Variables

- `home.sessionVariables` is not sourced by `gnome-session`. Use `xdg.configFile."environment.d/..."` for input-method environment variables on GNOME. (verified 2025–2026; re-verify before relying)

# Identity and Attribute Names

- Resolve host and user flake attribute names dynamically with `builtins.attrNames`; never hardcode a username or hostname. (verified 2025–2026; re-verify before relying)
