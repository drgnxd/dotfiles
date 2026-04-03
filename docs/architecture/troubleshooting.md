## Nix Issues

**`darwin-rebuild` fails**:
```bash
darwin-rebuild build --flake ~/.config/nix-config#macbook
```
First, run a build to inspect the error details, then fix the relevant Nix file.

**Flake dependencies cannot be resolved**:
```bash
nix flake update --flake ~/.config/nix-config
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
darwin-rebuild switch --flake ~/.config/nix-config#macbook
```
Adjust the relevant cask based on the reported error.
