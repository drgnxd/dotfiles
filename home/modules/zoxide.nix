_:

{
  programs.zoxide = {
    enable = true;
    # Init script built via nushell-integrations.nix (Nix-built init script)
    enableNushellIntegration = false;
  };
}
