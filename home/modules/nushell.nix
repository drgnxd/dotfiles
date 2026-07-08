{ lib, ... }:

let
  autoloadDir = ../../dot_config/nushell/autoload;
  modulesDir = ../../dot_config/nushell/modules;
  mkConfigFiles =
    subdir: srcDir:
    lib.mapAttrs' (
      name: _type: lib.nameValuePair "nushell/${subdir}/${name}" { source = srcDir + "/${name}"; }
    ) (lib.filterAttrs (_name: type: type == "regular") (builtins.readDir srcDir));
in
{
  xdg.configFile = {
    "nushell/config.nu".source = ../../dot_config/nushell/config.nu;
    "nushell/env.nu".source = ../../dot_config/nushell/env.nu;
  }
  // mkConfigFiles "autoload" autoloadDir
  // mkConfigFiles "modules" modulesDir;
}
