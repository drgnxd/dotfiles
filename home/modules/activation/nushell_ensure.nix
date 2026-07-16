{ config, lib, ... }:

let
  activationLib = import ../../lib/activation.nix { inherit lib; };
  nushell_local_nu = "${config.xdg.configHome}/nushell/local.nu";
in
{
  home.activation.ensureNushellLocalNu = activationLib.mkEnsureLocalFile nushell_local_nu;
}
