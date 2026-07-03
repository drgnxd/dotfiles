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
