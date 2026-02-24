{ lib, ... }:

{
  # Settings that require -currentHost flag (ByHost preferences, not supported by system.defaults)
  home.activation.applyCurrentHostDefaults = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    /usr/bin/defaults -currentHost write -globalDomain NSStatusItemSpacing -int 10
    /usr/bin/defaults -currentHost write -globalDomain NSStatusItemSelectionPadding -int 6

    /usr/bin/killall SystemUIServer 2>/dev/null || true
    /usr/bin/killall ControlCenter 2>/dev/null || true
  '';
}
