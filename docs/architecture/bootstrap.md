## Fresh Install / Bootstrap Guide

This guide covers a fresh machine setup from zero to a fully configured environment.

### Prerequisites

* Git (for cloning the repository)
* Internet connection

### Step 1: Install Nix (Determinate Systems installer)

```bash
curl --proto '=https' --tlsv1.2 -fsSL https://install.determinate.systems/nix | sh -s -- install
```

Follow the prompts. The installer enables flakes by default and sets up the Nix daemon.

**Restart your shell** (or open a new terminal) after installation.

### Step 2: Clone the Repository

```bash
git clone https://github.com/<your-username>/dotfiles ~/.config/nix-config
cd ~/.config/nix-config
```

### Step 3: Configure Machine Identity

Copy the templates and edit the required identity for your machine. Preferences are optional and use portable defaults when absent:

```bash
cp local/identity.nix.example local/identity.nix
cp local/preferences.nix.example local/preferences.nix
# Edit local/identity.nix with your user, hostname, and linux_hostname.
```

Example `local/identity.nix`:

```nix
{
  user = "youruser";
  hostname = "your-macos-hostname";        # macOS: scutil --get LocalHostName
  linux_hostname = "your-linux-hostname";  # Linux: hostname
}
```

**Note**: `local/identity.nix` and `local/preferences.nix` are gitignored — they never leave your machine. See [`local/README.md`](../../local/README.md) for the concise local configuration reference.

### Step 4: Bootstrap

**macOS (nix-darwin):**

```bash
nix run path:.#bootstrap-darwin
```

**Linux (standalone home-manager):**

```bash
nix run path:.#bootstrap-linux
```

The bootstrap apps use `path:.` so the untracked `local/identity.nix` is visible to Nix.

### Step 5: Post-Activation

After the first activation completes:

1. **Default shell is Nushell** — your shell prompt changes immediately. Run `exec nu` if needed.
2. **Fonts** — run `fc-cache -f` to refresh the font cache, then verify:
   ```bash
   fc-list | grep -i HackGen
   ```
3. **Japanese input (Linux)** — if you set `japaneseInputMethod = "hazkey"` in `local/preferences.nix`, the hazkey systemd user service is enabled. Start it:
   ```bash
   systemctl --user start hazkey-server
   ```
   For fcitx5 + mozc (default), fcitx5 starts automatically on graphical login. IM variables are delivered through `~/.config/environment.d/fcitx5.conf`, not `home.sessionVariables`.
   On Ubuntu GNOME / X11 hosts that use Debian `im-config`, set `imConfigXinputrc = true;` in `local/preferences.nix` before activation, then perform a full logout/login after activation. `XMODIFIERS` is fixed at X session start, so restarting fcitx5 or reopening the app is not enough. The default fcitx5 toggle is `Ctrl+Space` for US layouts without a Zenkaku/Hankaku key.
4. **Floorp** — available on Linux via `floorp-bin` (nixpkgs) and on macOS via Homebrew cask.
5. **nixd in Helix** — the generated `~/.config/helix/languages.toml` now points at your actual host config names (see Phase 7 note). Option completion works without manual edits.

### Known Notes

* **Per-host nixd override** — the `languages.toml` delivered to Helix substitutes placeholder config names (`darwinConfigurations.<hostname>`, `homeConfigurations."<user>@<linuxHostname>"`) with your actual `hostname` and `user@linuxHostname` from `local/identity.nix`. This is handled automatically; no manual action required.
* **Vulkan on Linux** — disabled by default for hazkey to avoid GPU driver lookup crashes in standalone home-manager. Only re-enable on NixOS with proper graphics modules.
* **Secrets** — if you use agenix, add your SSH public key to `secrets/secrets.nix` and run `nix run .#rekey-secrets`.
