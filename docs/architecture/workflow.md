# Development Workflow

## 1. Local Changes
```bash
# Edit configuration
cd ~/.config/nix-config
$EDITOR dot_config/nushell/autoload/03-aliases.nu

# Apply changes
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# Build only (for verification)
/run/current-system/sw/bin/darwin-rebuild build --flake path:.
```

## 2. Git Management
```bash
# Stage changes
cd ~/.config/nix-config
git add .

# Commit
git commit -m "feat(nushell): add new alias"

# Push
git push origin main
```

## 3. Deploy to a New Machine
```bash
# Clone repository
git clone https://github.com/example/dotfiles.git ~/.config/nix-config
cd ~/.config/nix-config

# Apply configuration
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# Add user-specific configuration (optional)
cp ~/.config/git/config.local.example ~/.config/git/config.local
$EDITOR ~/.config/git/config.local
```

## Automated Garbage Collection
Determinate Nix owns the Nix daemon in this flake, and `hosts/darwin/default.nix` keeps `nix.enable = false`. That makes nix-darwin `nix.gc` options inert, so garbage collection is scheduled as a user-level Home Manager service instead.

The `nix-gc` user unit cleans the current user's profiles every Sunday at 05:00 local time with this retention policy:

```bash
nh clean user --keep 5 --keep-since 7d
```

On macOS, launchd writes logs to `~/.local/state/launchagents/nix-gc/stdout.log` and `~/.local/state/launchagents/nix-gc/stderr.log`. On Linux, systemd user service logs are available with `journalctl --user -u nix-gc.service`.
