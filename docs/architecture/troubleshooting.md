## Nix Issues

**`darwin-rebuild` fails**:
```bash
cd ~/.config/dotfiles
/run/current-system/sw/bin/darwin-rebuild build --flake path:.
```
First, run a build to inspect the error details, then fix the relevant Nix file.

**Flake dependencies cannot be resolved**:
```bash
cd ~/.config/dotfiles && nix flake update
```
Check network status and input update issues.

## Secrets Issues

**agenix cannot find files**:
```bash
ls secrets
```
Verify that `secrets/*.age` exists and that keys in `secrets/secrets.nix` are correct.

## Homebrew (nix-darwin) Issues

**Cask installation fails**:
```bash
cd ~/.config/dotfiles
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.
```
Adjust the relevant cask based on the reported error.

## launchd Environment Issues

**Scheduled LaunchAgents or GUI apps cannot find `nix` / `git-annex` after a reboot**:
```bash
launchctl getenv PATH
```
`launchd.user.envVariables` (`hosts/darwin/default.nix`) is applied only during
activation, via a one-shot `launchctl setenv` per key. Those values are not
persisted, so a reboot — most often a macOS update reboot — drops `PATH`,
`XDG_*`, `CLAUDE_CONFIG_DIR`, and `NPM_CONFIG_*` from the user launchd session.
The `setenv-user-env` login agent (`hosts/darwin/launchd.nix`) replays the whole
set at login, so a normal login recovers it; the failure window is between boot
and that agent running, or if the agent itself did not run.

Recover by re-seeding the session (either re-applies the agent and the values):
```bash
cd ~/.config/dotfiles
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.
```
Or set `PATH` directly as an immediate stopgap (does not survive the next
reboot):
```bash
launchctl setenv PATH "$HOME/.nix-profile/bin:/etc/profiles/per-user/$USER/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
```

## What a plain `darwin-rebuild switch` reverts every run

A switch is not purely additive. On **every** run it also:

- **Disables Remote Login (SSH) and Screen Sharing / ARD.**
  `system.activationScripts.securityHardening` (`hosts/darwin/default.nix`)
  runs `systemsetup -setremotelogin off` and the ARD `kickstart -deactivate
  -off` unconditionally, and deletes `com.apple.loginwindow LoginwindowText`.
  If you need remote access to this Mac, re-enable it after each switch or add
  the exception to that script.
- **Reverts manual System Settings changes** to the `system.defaults` values:
  fixed Dark mode, key-repeat rate, Dock (`autohide`, `static-only`, tilesize
  48), Finder (show-all-files, column view), locale `en_JP` + Celsius/cm,
  mouse & trackpad tracking speed 7, menu-bar clock (seconds/date/day),
  Control Center visibility (Wi-Fi / battery / now-playing hidden), screenshot
  folder `~/Desktop/Screenshots`, all text substitutions off.
- **Removes app-created "Launch at Login" agents** every switch:
  `eu.exelban.Stats(.LaunchAtLogin)`, `org.p0deje.Maccy`, legacy
  `setenv.SCIHOME` are `rm`-ed from `~/Library/LaunchAgents` (nix-darwin owns
  those login agents). Re-enabling "launch at login" from inside Stats or
  Maccy will not stick.
- **Homebrew `onActivation.cleanup = "zap"`**: any formula / cask / tap / MAS
  app not listed under `homebrew.*` in `hosts/darwin/default.nix` is
  uninstalled, and casks are **zapped** (their Application Support / config
  data deleted too). A manual `brew install` you forget to add to the config
  is gone, with its data, on the next switch. (Latent: the config declares
  `cask "tailscale"` but it is installed as the renamed `tailscale-app` —
  Homebrew resolves the rename, but align the config when convenient.)

### What a switch does NOT touch

- **Foreign LaunchAgents.** The `com.drgnxd.*` automation agents (from
  `accretion` and `~/repos/scripts`) are safe. The activation script's
  user-agent cleanup loop only iterates
  `/run/current-system/user/Library/LaunchAgents/*` (nix-declared agents); it
  never globs `~/Library/LaunchAgents` and has no knowledge of non-nix
  plists. Verified by reading `/run/current-system/activate`.
- `~/.local/state/**` (job state, logs, restic repo, `failure.json`),
  `~/repos/**`, the Proton Drive CLI session, `~/.ssh`.
- Home-manager dotfiles are read-only Nix-store symlinks, so they cannot be
  edited in place. The `*.before-nix` files under `~/.config` are one-time
  backups from the original pre-Nix migration, not produced by ongoing
  switches.

### Gitignored inputs a switch depends on but the git-bundle backup misses

`local/identity.nix` (sets `hostname`; without it the flake exposes no
`darwinConfigurations.<hostname>` and the switch fails), `local/packages.nix`, and
`local/claude-auto-mode-environment.nix` are gitignored, so they are **not in
the `com.drgnxd.dotfiles-backup` git bundle** — only in the whole-home restic
backup. `~/.ssh/id_ed25519` is the agenix identity that decrypts every
`secrets/*.age`; losing it both breaks activation and makes the secrets
unrecoverable. Keep an independent copy of that key.
