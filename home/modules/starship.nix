_:

{
  # Keep legacy config path for custom Nushell STARSHIP_CONFIG
  xdg.configFile."starship/starship.toml".source = ../../dot_config/starship/starship.toml;

  programs.starship = {
    enable = true;
    # Init script built via nushell-integrations.nix (Plan B derivation)
    enableNushellIntegration = false;
  };
}
