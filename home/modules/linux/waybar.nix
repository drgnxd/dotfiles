{ lib, ... }:

let
  render_with_theme = import ../../lib/render-theme.nix { inherit lib; };
in

{
  xdg.configFile = {
    "waybar/config.jsonc".source = ../../../dot_config/waybar/config.jsonc;
    "waybar/style.css".text = render_with_theme {
      templatePath = ../../../dot_config/waybar/style.css;
    };
  };

  programs.waybar.enable = true;
}
