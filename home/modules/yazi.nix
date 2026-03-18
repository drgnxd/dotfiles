{ ... }:

{
  xdg.configFile = {
    "yazi/yazi.toml".source = ../../dot_config/yazi/yazi.toml;
    "yazi/theme.toml".source = ../../dot_config/yazi/theme.toml;
    "yazi/keymap.toml".source = ../../dot_config/yazi/keymap.toml;
    "yazi/flavors/solarized-dark.yazi/flavor.toml".source =
      ../../dot_config/yazi/flavors/solarized-dark.yazi/flavor.toml;
  };
}
