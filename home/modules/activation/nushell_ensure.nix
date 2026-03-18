{ config, lib, ... }:

let
  nushell_local_nu = "${config.xdg.configHome}/nushell/local.nu";
in
{
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
