{ lib, pkgs, ... }:

{
  home.activation.ensureDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] (
    ''
      mkdir -p "$HOME/.local/bin"
    ''
    + lib.optionalString pkgs.stdenv.isDarwin ''
      mkdir -p "$HOME/Desktop/Screenshots"
      # Log dirs for every mkManagedAgent / launchd.agents agent (their
      # StandardOutPath/StandardErrorPath is ~/.local/state/launchagents/<name>/;
      # launchd silently drops output when the parent dir is missing).
      for agent in schemespoon maccy stats nix-gc setenv-scihome setenv-user-env remap-capslock; do
        mkdir -p "$HOME/.local/state/launchagents/$agent"
      done
      # compinit (ZDOTDIR, see hosts/darwin/default.nix) doesn't create its target dir
      mkdir -p "$HOME/.config/zsh"
    ''
  );
}
