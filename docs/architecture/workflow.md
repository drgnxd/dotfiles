# Development Workflow

## 1. Local Changes
```bash
# Edit configuration
cd ~/.config/dotfiles
$EDITOR xdg/config/nushell/autoload/03-aliases.nu

# Apply changes
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# Build only (for verification)
/run/current-system/sw/bin/darwin-rebuild build --flake path:.
```

## 2. Git Management
```bash
# Stage changes
cd ~/.config/dotfiles
git add .

# Commit
git commit -m "feat(nushell): add new alias"

# Push
git push origin main
```

## 3. Deploy to a New Machine
```bash
# Clone repository
git clone https://github.com/drgnxd/dotfiles.git ~/.config/dotfiles
cd ~/.config/dotfiles

# Apply configuration
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# Add user-specific configuration (optional)
cp ~/.config/git/config.local.example ~/.config/git/config.local
$EDITOR ~/.config/git/config.local
```

## Updating nixpkgs

nixpkgs is advanced locally, not by the weekly flake.lock pull request, so that only revisions that have settled in nixpkgs-unstable reach `flake.lock`.

```bash
# Pin nixpkgs to the newest nixpkgs-unstable channel head that is at least 7 days old
just update-settled

# Update every input; nixpkgs goes through update-settled
just update
```

- Settling is measured on the channel branch's own push history (`nixos-channel-bot` fast-forwards `nixpkgs-unstable` only after Hydra passes), not on master commit dates. The default is 7 days. The recipe refuses to move nixpkgs backwards unless `allow_downgrade=true` is passed.
- Do not run a bare `nix flake update`: it moves nixpkgs to the branch tip. Use `just update` or `just update-one <input>`.
- Review the closure diff and build before applying; roll back with `darwin-rebuild switch --rollback` and revert `flake.lock`.
- A security fix that is actively exploited, or that affects an installed package reachable from untrusted input, bypasses the settling time.
- `check-flake-lock-age` in CI warns when nixpkgs or home-manager is older than 30 days (nix-darwin and agenix: 90, because those upstreams commit rarely), which is the upper bound for leaving the lock unreviewed. A pinned nixpkgs is already at least 7 days old, so about 23 days remain before the warning.
- The weekly pull request still moves home-manager and nix-darwin to their branch tips; an evaluation error there can mean they expect a newer nixpkgs than the pinned one.

## Automated Garbage Collection
Determinate Nix owns the Nix daemon in this flake, and `hosts/darwin/default.nix` keeps `nix.enable = false`. That makes nix-darwin `nix.gc` options inert, so garbage collection is scheduled as a user-level Home Manager service instead.

The `nix-gc` user unit cleans the current user's profiles every Sunday at 05:00 local time with this retention policy:

```bash
nh clean user --keep 5 --keep-since 7d
```

On macOS, launchd writes logs to `~/.local/state/launchagents/nix-gc/stdout.log` and `~/.local/state/launchagents/nix-gc/stderr.log`. On Linux, systemd user service logs are available with `journalctl --user -u nix-gc.service`.
