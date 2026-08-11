{ lib, pkgs, ... }:

{
  home.activation.ensureDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] (
    ''
      mkdir -p "$HOME/.local/bin"
    ''
    + lib.optionalString pkgs.stdenv.isDarwin ''
      mkdir -p "$HOME/Desktop/Screenshots"
      mkdir -p "$HOME/.local/state/launchagents/maccy"
      mkdir -p "$HOME/.local/state/launchagents/nix-gc"
      mkdir -p "$HOME/.local/state/launchagents/stats"
      # compinit (ZDOTDIR, see hosts/darwin/default.nix) doesn't create its target dir
      mkdir -p "$HOME/.config/zsh"
    ''
  );
}
