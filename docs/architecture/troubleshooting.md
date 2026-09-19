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

There is a third window: an app registered as its own macOS Login Item (not a
LaunchAgent plist this repo manages) races `setenv-user-env` with no ordering
guarantee. If the app's Login Item wins and launches before `setenv-user-env`
finishes, it keeps the stale environment it inherited at launch for its whole
session — `launchctl setenv` never updates an already-running process. CodexBar
is the confirmed case: its Codex/Claude usage-monitoring CLI subprocesses need
`CODEX_HOME`/`CLAUDE_CONFIG_DIR`, so a lost race shows up as both providers
looking unauthenticated after a reboot, recoverable by quitting and manually
relaunching CodexBar. `setenv-user-env` now quits and reopens CodexBar itself,
after `setenv`, in the same script (`postSetenvRelaunchApps` in
`hosts/darwin/launchd.nix`), so its relative order is guaranteed regardless of
which one the OS launches first. This is a deliberate, narrow fix: the same
sibling-ordering race exists for every `mkLoginApp` entry (Alacritty, Floorp,
Sol, the Proton apps), but only CodexBar has shown an observable failure so
far.

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

## Re-registering scheduled agents after Nushell changes

After a Nix rebuild changes the Nushell store path, preview the scheduled-agent
re-registration from the interactive Aqua session:

```bash
cd ~/.config/dotfiles
just relaunch-agents --dry-run
```

The dry run validates the locally configured allow-list, plist labels, running
jobs, and any configured lock without creating the state directory, booting out or
bootstrapping any agent, or updating the sentinel. If the preview is clean,
perform the re-registration:

```bash
just relaunch-agents
```

Use `--force` only when the Nushell-path sentinel must be ignored. Jobs that are
running or hold a configured lock are deferred; rerun the command after they
become idle. A failed validation leaves the sentinel unchanged so the problem
can be fixed before retrying.

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
- **Briefly quits and relaunches CodexBar**: `setenv-user-env`
  (`hosts/darwin/launchd.nix`) reruns whenever its own script content or
  `userLaunchdEnv` changes, and each run quits then reopens every app in
  `postSetenvRelaunchApps` (currently just CodexBar) after replaying the env
  — see the "launchd Environment Issues" section above.
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

- **Foreign LaunchAgents.** User LaunchAgents managed outside this flake are
  safe. The activation script's user-agent cleanup loop only iterates
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
the repository git bundle** — only in the whole-home restic backup.
`~/.ssh/id_ed25519` is the agenix identity that decrypts every
`secrets/*.age`; losing it both breaks activation and makes the secrets
unrecoverable. Keep an independent copy of that key.
