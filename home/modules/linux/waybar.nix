{ lib, ... }:

let
  render_with_theme = import ../../lib/render-theme.nix { inherit lib; };
in

{
  xdg.configFile = {
    "waybar/config.jsonc".source = ../../../xdg/config/waybar/config.jsonc;
    "waybar/style.css".text = render_with_theme {
      templatePath = ../../../xdg/config/waybar/style.css;
    };
  };

  programs.waybar.enable = true;
}
