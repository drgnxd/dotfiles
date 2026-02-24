{ ... }:

{
  # Keep legacy config path for custom Nushell STARSHIP_CONFIG
  xdg.configFile."starship/starship.toml".source = ../../dot_config/starship/starship.toml;

  programs.starship = {
    enable = true;
    # Nushell integration is managed via custom caching in nushell config
    enableNushellIntegration = false;
  };
}
