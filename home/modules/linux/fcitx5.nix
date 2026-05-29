{
  inputs,
  lib,
  pkgs,
  preferences ? { },
  ...
}:

let
  use_hazkey = (preferences.japaneseInputMethod or "mozc") == "hazkey";
in

{
  config = {
    i18n.inputMethod = {
      enable = true;
      type = "fcitx5";
      fcitx5.addons = lib.mkMerge [
        [ pkgs.fcitx5-gtk ]
        (lib.mkIf (!use_hazkey) [ pkgs.fcitx5-mozc ])
        (lib.mkIf use_hazkey [ inputs.nix-hazkey.packages.${pkgs.system}.fcitx5-hazkey ])
      ];
    };

    # Vulkan is intentionally left at the upstream default (disabled) because
    # standalone home-manager (non-NixOS) setups cannot reliably resolve GPU
    # driver .so files at runtime, causing hazkey-server to crash. Re-enable
    # only on NixOS with a proper hardware.opengl/graphics module.
    home.packages = lib.mkIf use_hazkey [ inputs.nix-hazkey.packages.${pkgs.system}.hazkey-settings ];

    systemd.user.services.hazkey-server = lib.mkIf use_hazkey {
      Unit = {
        Description = "Hazkey IME server";
        PartOf = [ "graphical-session.target" ];
        After = [ "graphical-session.target" ];
      };
      Service = {
        ExecStart = "${inputs.nix-hazkey.packages.${pkgs.system}.hazkey-server}/bin/hazkey-server";
        Restart = "on-failure";
        RestartSec = "3s";
      };
      Install.WantedBy = [ "hyprland-session.target" ];
    };

    home.sessionVariables = {
      GTK_IM_MODULE = "fcitx";
      QT_IM_MODULE = "fcitx";
      XMODIFIERS = "@im=fcitx";
      SDL_IM_MODULE = "fcitx";
      # GLFW does not support fcitx5 natively; "ibus" is the accepted compatibility shim
      GLFW_IM_MODULE = "ibus";
    };
  };
}
