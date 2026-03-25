{ pkgs, ... }:

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
}
