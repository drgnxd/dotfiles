{ config, ... }:

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
      # Atuin defaults to the legacy ~/.atuin/logs path.
      logs.dir = "${config.xdg.stateHome}/atuin/logs";
    };
  };
}
