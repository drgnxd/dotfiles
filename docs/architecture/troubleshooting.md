## Nix Issues

**`darwin-rebuild` fails**:
```bash
cd ~/.config/nix-config
/run/current-system/sw/bin/darwin-rebuild build --flake path:.
```
First, run a build to inspect the error details, then fix the relevant Nix file.

**Flake dependencies cannot be resolved**:
```bash
cd ~/.config/nix-config && nix flake update
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
cd ~/.config/nix-config
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.
```
Adjust the relevant cask based on the reported error.
