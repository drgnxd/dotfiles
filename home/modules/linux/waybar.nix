_:

{
  xdg.configFile = {
    "waybar/config.jsonc".source = ../../../dot_config/waybar/config.jsonc;
    "waybar/style.css".source = ../../../dot_config/waybar/style.css;
  };

  programs.waybar.enable = true;
}
