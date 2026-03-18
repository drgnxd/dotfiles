_:

{
  programs.zoxide = {
    enable = true;
    # Init script built via nushell-integrations.nix (Plan B derivation)
    enableNushellIntegration = false;
  };
}
