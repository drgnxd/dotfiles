{
  config,
  lib,
  pkgs,
  ...
}:

{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
    # Spotlight does not reliably index the symlinked app bundles from Home Manager.
    home.activation.generateSpotlightAppLaunchers = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
      ${pkgs.bash}/bin/bash ${./spotlight_app_launchers.sh} \
        ${lib.escapeShellArg "${config.home.homeDirectory}/Applications/Home Manager Apps"} \
        ${lib.escapeShellArg "${config.home.homeDirectory}/Applications"}
    '';
  };
}
