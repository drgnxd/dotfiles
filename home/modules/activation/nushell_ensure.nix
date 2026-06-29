{ config, lib, ... }:

let
  activationLib = import ../../lib/activation.nix { inherit lib; };
  nushell_local_nu = "${config.xdg.configHome}/nushell/local.nu";
in
{
  home.activation.ensureNushellLocalNu = activationLib.mkEnsureLocalFile nushell_local_nu;

  # Only carapace needs a runtime cache stub (Plan A).
  # starship/zoxide/atuin are Nix-built (Plan B) via nushell-integrations.nix.
  home.activation.ensureNushellInitCache = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.cache/nushell-init"
    touch "$HOME/.cache/nushell-init/carapace.nu"
  '';
}
