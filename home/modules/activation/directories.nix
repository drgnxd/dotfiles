{ lib, ... }:

{
  home.activation.ensureDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.local/bin"
    mkdir -p "$HOME/Desktop/Screenshots"
    mkdir -p "$HOME/.local/state/launchagents/hammerspoon"
    mkdir -p "$HOME/.local/state/launchagents/maccy"
    mkdir -p "$HOME/.local/state/launchagents/stats"
  '';
}
