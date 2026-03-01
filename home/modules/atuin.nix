{ ... }:

{
  programs.atuin = {
    enable = true;
    # Init script built via nushell-integrations.nix (Plan B derivation)
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
