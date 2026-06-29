{
  inputs,
  lib,
  pkgs,
  preferences ? { },
  ...
}:

let
  systemdUser = import ../../lib/systemd-user.nix;
  use_hazkey = (preferences.japaneseInputMethod or "mozc") == "hazkey";
  write_xinputrc = preferences.imConfigXinputrc or false;
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

    systemd.user.services.hazkey-server = lib.mkIf use_hazkey (
      systemdUser.mkGraphicalUserService {
        description = "Hazkey IME server";
        execStart = "${inputs.nix-hazkey.packages.${pkgs.system}.hazkey-server}/bin/hazkey-server";
      }
    );

    # gnome-session does not source hm-session-vars.sh; environment.d reaches
    # GNOME/systemd-user and the systemd-managed Hyprland session target.
    xdg.configFile."environment.d/fcitx5.conf".text = ''
      GTK_IM_MODULE=fcitx
      QT_IM_MODULE=fcitx
      XMODIFIERS=@im=fcitx
      SDL_IM_MODULE=fcitx
      GLFW_IM_MODULE=ibus
    '';

    # Debian/Ubuntu im-config reads ~/.xinputrc on X11 and selects fcitx5 so
    # XMODIFIERS becomes @im=fcitx. It is inert noise on Wayland Hyprland, so gate it.
    home.file.".xinputrc" = lib.mkIf write_xinputrc { text = "run_im fcitx5\n"; };
  };
}
