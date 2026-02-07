## macOS (darwin)
**Package Manager**: Nix (nix-darwin + home-manager)

**System Integration**:
- `system.defaults` and activation scripts via nix-darwin
- LaunchAgents via `launchd.user.agents`
- Hammerspoon and Stats configuration via Home Manager

**Apps**:
- GUI apps managed through nix-darwin `homebrew` (casks/MAS) where nixpkgs is insufficient

## Linux
Linux is not currently targeted in this configuration.
