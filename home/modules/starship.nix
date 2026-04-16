# Single source of truth: dot_config/starship/starship.toml via xdg.configFile.
# Plan B Nushell init uses STARSHIP_CONFIG=~/.config/starship/starship.toml.
_:

{
  xdg.configFile."starship/starship.toml".source = ../../dot_config/starship/starship.toml;

  programs.starship = {
    enable = true;
    # Init script built via nushell-integrations.nix (Plan B derivation)
    enableNushellIntegration = false;
  };
}
