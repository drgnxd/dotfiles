{ lib, ... }:

let
  render_with_theme = import ../lib/render-theme.nix { inherit lib; };
in

{
  xdg.configFile = {
    "yazi/yazi.toml".source = ../../xdg/config/yazi/yazi.toml;
    "yazi/theme.toml".source = ../../xdg/config/yazi/theme.toml;
    "yazi/keymap.toml".source = ../../xdg/config/yazi/keymap.toml;
    "yazi/flavors/solarized-dark.yazi/flavor.toml".text = render_with_theme {
      templatePath = ../../xdg/config/yazi/flavors/solarized-dark.yazi/flavor.toml;
    };
  };
}
