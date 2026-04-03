# Development Workflow

## 1. Local Changes
```bash
# Edit configuration
cd ~/.config/nix-config
$EDITOR dot_config/nushell/autoload/03-aliases.nu

# Apply changes
darwin-rebuild switch --flake ~/.config/nix-config#macbook

# Build only (for verification)
darwin-rebuild build --flake ~/.config/nix-config#macbook
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
git clone https://github.com/drgnxd/dotfiles.git ~/.config/nix-config

# Apply configuration
darwin-rebuild switch --flake ~/.config/nix-config#macbook

# Add user-specific configuration (optional)
cp ~/.config/git/config.local.example ~/.config/git/config.local
$EDITOR ~/.config/git/config.local
```
