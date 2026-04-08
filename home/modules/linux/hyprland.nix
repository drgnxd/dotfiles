{
  config,
  lib,
  pkgs,
  ...
}:

let
  hypr_local_conf = "${config.xdg.configHome}/hypr/local.conf";
in

{
  wayland.windowManager.hyprland = {
    enable = true;
    extraConfig = builtins.readFile ../../../dot_config/hypr/hyprland.conf;
  };

  xdg.configFile = {
    "hypr/hyprlock.conf".source = ../../../dot_config/hypr/hyprlock.conf;
    "hypr/hypridle.conf".source = ../../../dot_config/hypr/hypridle.conf;
    "hypr/local.conf.example".source = ../../../dot_config/hypr/local.conf.example;
  };

  home.packages = with pkgs; [
    hyprlock
    hypridle
  ];

  home.activation.ensureHyprLocalConf = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    hypr_local_conf="${hypr_local_conf}"
    if [ ! -f "$hypr_local_conf" ]; then
      mkdir -p "$(dirname "$hypr_local_conf")"
      touch "$hypr_local_conf"
    fi
  '';
}
