# Local Configuration

This directory is the only place a new user needs to personalize after cloning.

```sh
cp local/identity.nix.example local/identity.nix
cp local/preferences.nix.example local/preferences.nix
cp local/packages.nix.example local/packages.nix
```

Edit `identity.nix` before the first activation:

- `user`: output of `whoami`.
- `hostname`: macOS local host name from `scutil --get LocalHostName`.
- `linux_hostname`: Linux host name from `hostname`.

`preferences.nix` is optional. Omit it to use the portable defaults.

`packages.nix` is optional: a plain list of extra nixpkgs attribute names
to install alongside `home/packages.nix`'s public lists, for anything you
don't want disclosed by being named in this public repo (e.g.
personal-finance tooling). Omit it to install nothing extra.

Do not commit any local `.nix` file. They are ignored so each clone can keep its own identity, preferences, and private package list.

Apply the configuration from the repository root:

```sh
# macOS
nix run path:.#bootstrap-darwin

# Linux
nix run path:.#bootstrap-linux
```
