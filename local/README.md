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

`private-tools.nix` is optional (copy `private-tools.nix.example` only if you
need it): a function `{ pkgs, lib, ... }: [ <derivation> ... ]` for tools whose
sources live in private repositories and whose names you don't want disclosed
in this public repo. Pin each source to a commit with
`builtins.fetchGit { url = ...; rev = ...; }` (a pinned `rev` is allowed under
the pure `path:.` evaluation; bump it by hand to update the tool) and build it
with `pkgs.callPackage`. Notes:

- It must be a regular file, not a symlink, and fails closed: a malformed
  file or an unreachable remote aborts every rebuild until you fix or move it.
  Nix errors may quote its lines, so keep such logs out of public issues.
- On macOS `darwin-rebuild` runs under `sudo`, so the fetch runs as root: the
  remote must be reachable for root (an agent via `SSH_AUTH_SOCK` plus root's
  `known_hosts`, or an HTTPS remote root can authenticate to), and a local
  repository must pass git's ownership check for root.
- Do not add private repositories as flake inputs: `flake.lock` is committed.
  Private sources and the tool names end up world-readable in `/nix/store`
  on this machine; do not push such closures to a binary cache.
- If the pinned commit is not on the default branch, add `ref` (or
  `allRefs = true`) next to `rev`.

`claude-auto-mode-environment.nix` is optional: a plain list of prose
strings appended to Claude Code's `autoMode.environment` (deployed to
`~/.local/share/claude/settings.json`), for personal environment context —
organization, source control, sensitive data locations — you don't want
disclosed by being named in this public repo. Omit it to run auto mode with
only the classifier's built-in defaults.

Do not commit any local `.nix` file. They are ignored so each clone can keep its own identity, preferences, private package list, private tool sources, and auto-mode environment context.

Apply the configuration from the repository root:

```sh
# macOS
nix run path:.#bootstrap-darwin

# Linux
nix run path:.#bootstrap-linux
```
