{ lib, ... }:

let
  caps_lock_hid_usage = 30064771129; # 0x700000039
  control_hid_usage = 30064771300; # 0x7000000E4, matching macOS GUI "Control"
in

{
  # Settings that require -currentHost flag (ByHost preferences, not supported by system.defaults)
  home.activation.applyCurrentHostDefaults = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    /usr/bin/defaults -currentHost write -globalDomain NSStatusItemSpacing -int 10
    /usr/bin/defaults -currentHost write -globalDomain NSStatusItemSelectionPadding -int 6
    /usr/bin/defaults -currentHost write -globalDomain "com.apple.keyboard.modifiermapping.0-0-0" -array \
      '{ HIDKeyboardModifierMappingSrc = ${toString caps_lock_hid_usage}; HIDKeyboardModifierMappingDst = ${toString control_hid_usage}; }'

    /usr/bin/hidutil property --set \
      '{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x7000000E4}]}' >/dev/null

    /usr/bin/killall cfprefsd 2>/dev/null || true
    /usr/bin/killall SystemUIServer 2>/dev/null || true
    /usr/bin/killall ControlCenter 2>/dev/null || true
  '';
}
