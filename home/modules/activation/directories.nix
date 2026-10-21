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
      bash_history_dir="${config.xdg.stateHome}/bash"
      bash_history_file="$bash_history_dir/history"
      if [ -L "$bash_history_dir" ] || \
         { [ -e "$bash_history_dir" ] && [ ! -d "$bash_history_dir" ]; }; then
        echo "error: refusing unexpected Bash history directory: $bash_history_dir" >&2
        exit 1
      fi
      mkdir -p -m 0700 "$bash_history_dir"
      chmod 0700 "$bash_history_dir"
      if [ -L "$bash_history_file" ] || \
         { [ -e "$bash_history_file" ] && [ ! -f "$bash_history_file" ]; }; then
        echo "error: refusing unexpected Bash history file: $bash_history_file" >&2
        exit 1
      fi
      if [ ! -e "$bash_history_file" ]; then
        (umask 077 && : > "$bash_history_file")
      fi
      chmod 0600 "$bash_history_file"
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
    ''
  );
}
