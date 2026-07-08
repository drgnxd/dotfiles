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
**Desktop Environment**: Hyprland (Wayland compositor)

**Usage**:
```bash
cd ~/.config/nix-config
home-manager switch --flake path:.#<user>@<linuxHostname>
```

Set `local/identity.nix` before applying on your machine.

**Desktop stack**:
- Hyprland — tiling window manager (Hammerspoon equivalent)
- Waybar — status bar (Stats.app equivalent)
- Wofi — application launcher (Sol equivalent)
- fcitx5 + mozc (or hazkey) — Japanese input
- cliphist + wl-clipboard — clipboard manager (Maccy equivalent)
- hypridle + hyprlock — idle management and screen lock
- mako — notification daemon
- grim + slurp — screenshots

**Supported components**: All CLI tools, Nushell, Helix, Git, Taskwarrior, Yazi, Zellij, OpenCode, Starship, Zoxide, Atuin, Carapace, Direnv, Alacritty, and the Linux desktop stack above.

**Keybinding parity**: Window management keybindings (`Ctrl+Alt` + arrows/`U``I``J``K`/`C`/`Enter`) are mirrored from the macOS Hammerspoon configuration for consistent muscle memory.

**Hazkey input**: set `japaneseInputMethod = "hazkey"` in `local/preferences.nix` to enable live conversion on Linux. Vulkan remains disabled by default to avoid GPU driver lookup crashes in standalone home-manager; only re-enable on NixOS with proper graphics modules.

**Fcitx5 input environment**: fcitx5 IM variables are delivered through `~/.config/environment.d/fcitx5.conf`, not `home.sessionVariables`, so GNOME sessions and systemd-managed Hyprland sessions receive the same values. On Ubuntu GNOME / X11 hosts that use Debian `im-config`, set `imConfigXinputrc = true;` in `local/preferences.nix` to write `~/.xinputrc` with `run_im fcitx5`; then perform a full logout/login because `XMODIFIERS` is fixed at X session start. Restarting fcitx5 or reopening an app is not enough. The default fcitx5 toggle is `Ctrl+Space` for US layouts without a Zenkaku/Hankaku key.

**Hammerspoon -> Hyprland mapping**:

| macOS (Hammerspoon) | Linux (Hyprland) |
|---------------------|------------------|
| Window management (Ctrl+Alt) | Hyprland keybinds (Ctrl+Alt) |
| Sol launcher (Cmd+Space) | Wofi (Super+Space) |
| Auto input switching | socket2 event watcher (`hypr-input-watcher`, systemd user service) |
| Browser control (background app) | `dispatch sendshortcut` targeting `class:^(floorp)$` |

### Additional desktop utilities
- SwayOSD (volume / brightness / caps-lock OSD)
- hyprpicker (color picker — Digital Color Meter equivalent)
- Blur toggle binding (Super+B)
- Touchpad workspace swipe (Mission Control horizontal swipe equivalent)
- Background browser control via `dispatch sendshortcut`

**Not available on Linux**: macOS system defaults, LaunchAgents, Homebrew casks, and direct Hammerspoon APIs.
