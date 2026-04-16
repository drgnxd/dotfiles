# Single source of truth: programs.bat.config.
# Keep bat settings in Nix to avoid drift with static files.
_:

{
  programs.bat = {
    enable = true;
    config = {
      theme = "Solarized (dark)";
      italic-text = "always";
      style = "numbers,changes,header";
      paging = "auto";
      tabs = "4";
    };
  };
}
