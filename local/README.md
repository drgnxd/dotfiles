# Local Configuration

This directory is the only place a new user needs to personalize after cloning.

```sh
cp local/identity.nix.example local/identity.nix
cp local/preferences.nix.example local/preferences.nix
```

Edit `identity.nix` before the first activation:

- `user`: output of `whoami`.
- `hostname`: macOS local host name from `scutil --get LocalHostName`.
- `linux_hostname`: Linux host name from `hostname`.

`preferences.nix` is optional. Omit it to use the portable defaults.

Do not commit either local `.nix` file. They are ignored so each clone can keep its own identity and preferences.

Apply the configuration from the repository root:

```sh
# macOS
nix run path:.#bootstrap-darwin

# Linux
nix run path:.#bootstrap-linux
```
