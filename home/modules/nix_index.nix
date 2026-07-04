_: {
  programs.nix-index.enable = true;
  # Shell hooks target bash/zsh/fish; the login shell here is Nushell, so hooks stay off.
  programs.nix-index.enableBashIntegration = false;
  programs.nix-index.enableZshIntegration = false;
  programs.nix-index.enableFishIntegration = false;
  programs.nix-index-database.comma.enable = true;
}
