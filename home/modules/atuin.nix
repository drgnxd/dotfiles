{ ... }:

{
  programs.atuin = {
    enable = true;
    # Nushell integration is managed via custom caching in nushell config
    enableNushellIntegration = false;
    settings = {
      secrets_filter = true;
      history_filter = [
        "^SecretCommand"
        "^base64"
      ];
    };
  };
}
