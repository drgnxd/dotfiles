# Single source of truth: dot_config/starship/starship.toml via xdg.configFile.
# Plan B Nushell init uses STARSHIP_CONFIG=~/.config/starship/starship.toml.
{ lib, ... }:

let
  render_with_theme = import ../lib/render-theme.nix { inherit lib; };
in

{
  xdg.configFile."starship/starship.toml".text = render_with_theme {
    templatePath = ../../dot_config/starship/starship.toml;
  };

  programs.starship = {
    enable = true;
    # Init script built via nushell-integrations.nix (Plan B derivation)
    enableNushellIntegration = false;
  };
}
