{
  config,
  lib,
  pkgs,
  preferences ? { },
  ...
}:

let
  activationLib = import ../../lib/activation.nix { inherit lib; };
  hypr_local_conf = "${config.xdg.configHome}/hypr/local.conf";
  render_with_theme = import ../../lib/render-theme.nix { inherit lib; };
  browser_class = preferences.browserClass or "floorp";
in

{
  wayland.windowManager.hyprland = {
    enable = true;
    configType = "hyprlang";
    extraConfig = render_with_theme {
      templatePath = ../../../dot_config/hypr/hyprland.conf;
      includeBareHex = true;
    };
  };

  xdg.configFile = {
    "hypr/browser.conf".text = ''
      # Managed by Nix: browser sendshortcut bindings
      bind = CTRL SUPER, j, sendshortcut, , Page_Down, class:^(${browser_class})$
      bind = CTRL SUPER, k, sendshortcut, , Prior, class:^(${browser_class})$
      bind = CTRL SUPER, h, sendshortcut, ALT, Left, class:^(${browser_class})$
      bind = CTRL SUPER, l, sendshortcut, ALT, Right, class:^(${browser_class})$
    '';
    "hypr/hyprlock.conf".text = render_with_theme {
      templatePath = ../../../dot_config/hypr/hyprlock.conf;
      includeBareHex = true;
    };
    "hypr/hypridle.conf".source = ../../../dot_config/hypr/hypridle.conf;
    "hypr/local.conf.example".source = ../../../dot_config/hypr/local.conf.example;
  };

  home.packages = with pkgs; [
    hyprlock
    hypridle
  ];

  home.activation.ensureHyprLocalConf = activationLib.mkEnsureLocalFile hypr_local_conf;
}
