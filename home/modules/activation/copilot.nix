# Copilot CLI keeps user settings in a CLI-writable settings.json, so the keys
# that must match OpenCode's no-prompt permission stance are merged into it at
# activation instead of being owned as a read-only store symlink. Other keys
# the CLI wrote are preserved. Instructions and skills are symlinked to the
# OpenCode sources in ../../default.nix.
{
  config,
  lib,
  pkgs,
  ...
}:

let
  settings_target = "${config.xdg.dataHome}/copilot/settings.json";
  managed_settings = pkgs.writeText "copilot-managed-settings.json" (
    builtins.toJSON {
      defaultPermissionMode = "allow-all";
      trustedFolders = [
        "${config.home.homeDirectory}/repos"
        "${config.xdg.stateHome}"
        "${config.xdg.configHome}/dotfiles"
        "${config.xdg.configHome}/opencode"
      ];
    }
  );
  jaq = "${pkgs.jaq}/bin/jaq";
in
{
  home.activation.copilotSettings = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    target="${settings_target}"
    if [ -L "$target" ] || { [ -e "$target" ] && [ ! -f "$target" ]; }; then
      echo "warning: $target is not a regular file; leaving Copilot settings untouched" >&2
    elif [ -s "$target" ] && ! ${jaq} -s -e 'length == 1 and (.[0] | type) == "object"' "$target" >/dev/null 2>&1; then
      echo "warning: $target is not a single JSON object; leaving it untouched" >&2
    else
      tmp="$(mktemp)"
      src="$target"
      [ -s "$target" ] || { src="$tmp.empty"; printf '{}' > "$src"; }
      if ${jaq} --slurpfile m ${managed_settings} \
          '. as $c | $c + $m[0] | .trustedFolders = ((($c.trustedFolders // []) + $m[0].trustedFolders) | unique)' \
          "$src" > "$tmp" 2>/dev/null; then
        if ! cmp -s "$tmp" "$target"; then
          run mkdir -p "$(dirname "$target")"
          run install -m 644 "$tmp" "$target"
        fi
      else
        echo "warning: could not merge Copilot managed settings; keeping $target" >&2
      fi
      rm -f "$tmp" "$tmp.empty"
    fi
  '';
}
