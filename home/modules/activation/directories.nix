{
  config,
  lib,
  pkgs,
  ...
}:

{
  home.activation.ensureDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] (
    ''
      mkdir -p "$HOME/.local/bin"
      ensure_private_history() {
        local history_dir="$1"
        local history_file="$history_dir/history"

        if [ -L "$history_dir" ] || \
           { [ -e "$history_dir" ] && [ ! -d "$history_dir" ]; }; then
          printf 'error: refusing unexpected history directory: %s\n' "$history_dir" >&2
          exit 1
        fi
        mkdir -p -m 0700 "$history_dir"
        chmod 0700 "$history_dir"
        if [ -L "$history_file" ] || \
           { [ -e "$history_file" ] && [ ! -f "$history_file" ]; }; then
          printf 'error: refusing unexpected history file: %s\n' "$history_file" >&2
          exit 1
        fi
        if [ ! -e "$history_file" ]; then
          (umask 077 && : > "$history_file")
        fi
        chmod 0600 "$history_file"
      }

      ensure_private_history "${config.xdg.stateHome}/bash"
    ''
    + lib.optionalString pkgs.stdenv.hostPlatform.isDarwin ''
      mkdir -p "$HOME/Desktop/Screenshots"
      # Log dirs for every mkManagedAgent / launchd.agents agent (their
      # StandardOutPath/StandardErrorPath is ~/.local/state/launchagents/<name>/;
      # launchd silently drops output when the parent dir is missing).
      for agent in maccy stats nix-gc setenv-scihome setenv-user-env remap-capslock; do
        mkdir -p "$HOME/.local/state/launchagents/$agent"
      done
      mkdir -p "$HOME/.local/state/automation-failures"
      # compinit (ZDOTDIR, see hosts/darwin/default.nix) doesn't create its target dir
      mkdir -p "$HOME/.config/zsh"
      ensure_private_history "${config.xdg.stateHome}/zsh"
    ''
  );
}
