{ ... }:

{
  programs.zoxide = {
    enable = true;
    # Nushell integration is managed via custom caching in nushell config
    enableNushellIntegration = false;
  };
}
