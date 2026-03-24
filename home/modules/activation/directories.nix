{ lib, pkgs, ... }:

{
  home.activation.ensureDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] (
    ''
      mkdir -p "$HOME/.local/bin"
    ''
    + lib.optionalString pkgs.stdenv.isDarwin ''
      mkdir -p "$HOME/Desktop/Screenshots"
      mkdir -p "$HOME/.local/state/launchagents/hammerspoon"
      mkdir -p "$HOME/.local/state/launchagents/maccy"
      mkdir -p "$HOME/.local/state/launchagents/stats"
    ''
  );
}
