## macOS (darwin)
**Package Manager**: Nix (nix-darwin + home-manager)

**System Integration**:
- `system.defaults` and activation scripts via nix-darwin
- LaunchAgents via `launchd.user.agents`
- Hammerspoon and Stats configuration via Home Manager
- Home Manager activation disables legacy app-managed LaunchAgents (Stats/Hammerspoon) to avoid duplicate launches

**Apps**:
- GUI apps managed through nix-darwin `homebrew` (casks/MAS) where nixpkgs is insufficient

## Linux (x86_64-linux)
**Package Manager**: Nix (standalone home-manager)

**Usage**:
```bash
home-manager switch --flake ~/.config/nix-config#<user>@<linuxHostname>
```

Set `user` and `linuxHostname` in `flake.nix` before applying on your machine.

**Supported components**: All CLI tools, Nushell, Helix, Git, Taskwarrior, Yazi, Zellij, OpenCode, Starship, Zoxide, Atuin, Carapace, Direnv, Alacritty (without macOS window features).

**Not available on Linux**: Hammerspoon, Stats, Sol, Maccy, macOS system defaults, LaunchAgents, Homebrew casks. See Phase 2 roadmap for Linux desktop environment alternatives.
