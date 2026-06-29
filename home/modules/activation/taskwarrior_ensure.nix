{ config, lib, ... }:

let
  activationLib = import ../../lib/activation.nix { inherit lib; };
  taskwarrior_local_rc = "${config.xdg.configHome}/taskwarrior.local.rc";
in
{
  home.activation.ensureTaskwarriorLocalRc = activationLib.mkEnsureLocalFile taskwarrior_local_rc;
}
