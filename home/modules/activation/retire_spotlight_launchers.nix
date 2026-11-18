{ lib, pkgs, ... }:

{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
    # copyApps installs real bundles that Spotlight indexes, so the AppleScript
    # launchers generated for the old symlinked apps are obsolete and would
    # shadow the copies for `open -a`. Only bundles carrying our marker go.
    # Delete this module once no host still has those launchers.
    home.activation.retireSpotlightLaunchers = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      for launcher in "$HOME/Applications"/*.app; do
        if [ ! -L "$launcher" ] && [ -f "$launcher/Contents/Resources/home-manager-spotlight-target" ]; then
          run rm -rf "$launcher" || warnEcho "could not remove obsolete launcher $launcher"
        fi
      done
    '';
  };
}
