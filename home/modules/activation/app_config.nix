{ config, lib, ... }:

let
  opencode_template = ../../../dot_config/opencode/opencode.json;
  opencode_local_example = ../../../dot_config/opencode/opencode.local.json.example;
  opencode_target = "${config.xdg.configHome}/opencode/opencode.json";
  opencode_local_override = "${config.xdg.configHome}/opencode/opencode.local.json";
  opencode_local_example_target = "${config.xdg.configHome}/opencode/opencode.local.json.example";
  taskwarrior_local_rc = "${config.xdg.configHome}/taskwarrior.local.rc";
  nushell_local_nu = "${config.xdg.configHome}/nushell/local.nu";
in
{
  home.activation.ensureOpencodeLocalConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    opencode_local_override="${opencode_local_override}"
    opencode_local_example_target="${opencode_local_example_target}"
    opencode_dir="$(dirname "$opencode_local_override")"
    mkdir -p "$opencode_dir"
    if [ ! -f "$opencode_local_override" ]; then
      touch "$opencode_local_override"
    fi
    if [ ! -f "$opencode_local_example_target" ]; then
      /bin/cp -f "${opencode_local_example}" "$opencode_local_example_target"
    fi
  '';

  home.activation.syncOpencodeConfig = lib.hm.dag.entryAfter [ "ensureOpencodeLocalConfig" ] ''
    opencode_target="${opencode_target}"
    opencode_local_override="${opencode_local_override}"
    opencode_dir="$(dirname "$opencode_target")"
    mkdir -p "$opencode_dir"
    if [ -s "$opencode_local_override" ]; then
      /bin/cp -f "$opencode_local_override" "$opencode_target"
    else
      /bin/cp -f "${opencode_template}" "$opencode_target"
    fi
  '';

  home.activation.ensureTaskwarriorLocalRc = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    taskwarrior_local_rc="${taskwarrior_local_rc}"
    if [ ! -f "$taskwarrior_local_rc" ]; then
      mkdir -p "$(dirname "$taskwarrior_local_rc")"
      touch "$taskwarrior_local_rc"
    fi
  '';

  home.activation.ensureNushellLocalNu = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    nushell_local_nu="${nushell_local_nu}"
    if [ ! -f "$nushell_local_nu" ]; then
      mkdir -p "$(dirname "$nushell_local_nu")"
      touch "$nushell_local_nu"
    fi
  '';

  # Only carapace needs a runtime cache stub (Plan A).
  # starship/zoxide/atuin are Nix-built (Plan B) via nushell-integrations.nix.
  home.activation.ensureNushellInitCache = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.cache/nushell-init"
    touch "$HOME/.cache/nushell-init/carapace.nu"
  '';
}
