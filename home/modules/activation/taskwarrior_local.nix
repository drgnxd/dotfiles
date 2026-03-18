{ config, lib, ... }:

let
  taskwarrior_local_rc = "${config.xdg.configHome}/taskwarrior.local.rc";
in
{
  home.activation.ensureTaskwarriorLocalRc = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    taskwarrior_local_rc="${taskwarrior_local_rc}"
    if [ ! -f "$taskwarrior_local_rc" ]; then
      mkdir -p "$(dirname "$taskwarrior_local_rc")"
      touch "$taskwarrior_local_rc"
    fi
  '';
}
