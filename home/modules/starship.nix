{ ... }:

{
  programs.starship = {
    enable = true;
    # Nushell integration is managed via custom caching in nushell config
    enableNushellIntegration = false;
    settings = builtins.fromTOML (builtins.readFile ../../dot_config/starship/starship.toml);
  };
}
