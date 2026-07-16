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
        "^# [0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\n"
        "^nu_abbr_insert_space$"
        "^nu_abbr_submit$"
      ];
      # Atuin defaults to the legacy ~/.atuin/logs path.
      logs.dir = "${config.xdg.stateHome}/atuin/logs";
    };
  };
}
