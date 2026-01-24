# Platform Support

## macOS (darwin)
**Package Manager**: Homebrew (`Brewfile.tmpl`)

**System Integration**:
- `system_defaults.sh`: NSUserDefaults modifications
- `Hammerspoon`: Window management and input switching
- `Stats`: System monitor (plist-based config)

**Automation**:
- Login items via AppleScript
- Menu bar configuration via `defaults`

## Linux
**Package Manager**: Native (apt/dnf/pacman)

**Shared Tools**:
- Alacritty, Zsh, Tmux, Helix
- Taskwarrior, Yazi, Starship
- CLI utilities (bat, eza, fd, ripgrep)

**Exclusions**:
- Hammerspoon (macOS-only)
- Homebrew (macOS-centric)
- `.internal_scripts/darwin/`
