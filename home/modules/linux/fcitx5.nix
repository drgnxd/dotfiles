{
  inputs,
  lib,
  pkgs,
  preferences ? { },
  ...
}:

let
  use_hazkey = (preferences.japaneseInputMethod or "mozc") == "hazkey";
  hazkey_addon = inputs.nix-hazkey.packages.${pkgs.system}.fcitx5-hazkey;
  hazkey_settings = inputs.nix-hazkey.packages.${pkgs.system}.hazkey-settings;
in

{
  i18n.inputMethod = {
    enable = true;
    type = "fcitx5";
    fcitx5.addons = lib.mkMerge [
      [ pkgs.fcitx5-gtk ]
      (lib.mkIf (!use_hazkey) [ pkgs.fcitx5-mozc ])
      (lib.mkIf use_hazkey [ hazkey_addon ])
    ];
  };

  # Vulkan is intentionally left at the upstream default (disabled) because
  # standalone home-manager (non-NixOS) setups cannot reliably resolve GPU
  # driver .so files at runtime, causing hazkey-server to crash. Re-enable
  # only on NixOS with a proper hardware.opengl/graphics module.
  home.packages = lib.mkIf use_hazkey [ hazkey_settings ];

  home.sessionVariables = {
    GTK_IM_MODULE = "fcitx";
    QT_IM_MODULE = "fcitx";
    XMODIFIERS = "@im=fcitx";
    SDL_IM_MODULE = "fcitx";
    # GLFW does not support fcitx5 natively; "ibus" is the accepted compatibility shim
    GLFW_IM_MODULE = "ibus";
  };
}
