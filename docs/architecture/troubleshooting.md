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
