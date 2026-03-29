# Troubleshooting

## Nix Issues

**`darwin-rebuild` fails**:
```bash
darwin-rebuild build --flake ~/.config/nix-config#macbook
```
First run `build` to inspect the error details, then fix the relevant Nix file.

**flake dependencies cannot be resolved**:
```bash
nix flake update --flake ~/.config/nix-config
```
Check network connectivity and input update issues.

## Secrets Issues

**`agenix` cannot find files**:
```bash
ls secrets
```
Confirm that `secrets/*.age` exists and keys in `secrets/secrets.nix` are correct.

## Homebrew (nix-darwin) Issues

**cask installation fails**:
```bash
darwin-rebuild switch --flake ~/.config/nix-config#macbook
```
Adjust the relevant cask according to the error message.
