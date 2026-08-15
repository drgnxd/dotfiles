# Local Configuration

This directory is the only place a new user needs to personalize after cloning.

```sh
cp local/identity.nix.example local/identity.nix
cp local/preferences.nix.example local/preferences.nix
cp local/packages.nix.example local/packages.nix
cp local/claude-auto-mode-environment.nix.example local/claude-auto-mode-environment.nix
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

`claude-auto-mode-environment.nix` is optional: a plain list of prose
strings appended to Claude Code's `autoMode.environment` (deployed to
`~/.local/share/claude/settings.json`), for personal environment context —
organization, source control, sensitive data locations — you don't want
disclosed by being named in this public repo. Omit it to run auto mode with
only the classifier's built-in defaults.

Do not commit any local `.nix` file. They are ignored so each clone can keep its own identity, preferences, private package list, and auto-mode environment context.

Apply the configuration from the repository root:

```sh
# macOS
nix run path:.#bootstrap-darwin

# Linux
nix run path:.#bootstrap-linux
```
