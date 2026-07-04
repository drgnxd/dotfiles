{
  config,
  lib,
  pkgs,
  user,
  hostname,
  linuxHostname,
  ...
}:

let
  packages = import ./packages.nix { inherit pkgs lib; };
  memory_tools = [
    (pkgs.writeShellScriptBin "memory-read" (builtins.readFile ../scripts/agent_memory/memory_read.sh))
    (pkgs.writeShellScriptBin "memory-append" (
      builtins.readFile ../scripts/agent_memory/memory_append.sh
    ))
  ];
in
{
  home.username = user;
  home.homeDirectory = if pkgs.stdenv.isDarwin then "/Users/${user}" else "/home/${user}";
  home.stateVersion = "24.11";

  programs.home-manager.enable = true;

  imports = [
    # === Cross-platform (always loaded) ===
    ./modules/activation/directories.nix
    ./modules/activation/nushell_ensure.nix
    ./modules/activation/opencode.nix
    ./modules/activation/taskwarrior_ensure.nix
    ./modules/alacritty.nix
    ./modules/atuin.nix
    ./modules/bat.nix
    ./modules/direnv.nix
    ./modules/floorp.nix
    ./modules/fzf.nix
    ./modules/gh.nix
    ./modules/git.nix
    ./modules/helix.nix
    ./modules/jujutsu.nix
    ./modules/nix_gc.nix
    ./modules/nushell.nix
    ./modules/nushell-integrations.nix
    ./modules/secrets.nix
    ./modules/shellcheck.nix
    ./modules/ssh.nix
    ./modules/starship.nix
    ./modules/taskwarrior.nix
    ./modules/yazi.nix
    ./modules/zellij.nix
    ./modules/zoxide.nix
  ]
  ++ lib.optionals pkgs.stdenv.isDarwin [
    # === macOS only ===
    ./modules/activation/macos_defaults.nix
    ./modules/hammerspoon.nix
    ./modules/xdg_config_files.nix
    ./modules/xdg_desktop_files.nix
  ]
  ++ lib.optionals pkgs.stdenv.isLinux [
    # === Linux only ===
    ./modules/linux/desktop.nix
  ];

  xdg.enable = true;

  targets.darwin.linkApps.enable = lib.mkIf pkgs.stdenv.isDarwin true;

  home.sessionVariables = {
    DOTFILES_DIR = "${config.home.homeDirectory}/.config/nix-config";
    DOTFILES_FLAKE_TARGET = if pkgs.stdenv.isDarwin then hostname else linuxHostname;
    NH_FLAKE = "${config.home.homeDirectory}/.config/nix-config";
  };

  home.packages = packages.packages ++ memory_tools;

  warnings = lib.optional (packages.missing != [ ]) (
    "Missing nix packages: " + (lib.concatStringsSep ", " packages.missing)
  );

  home.file = {
    ".ollama".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/ollama";
    ".Scilab".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/scilab";
  }
  // lib.optionalAttrs pkgs.stdenv.isDarwin {
    ".hammerspoon".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/hammerspoon";
    ".local/bin/cloud-symlinks" = {
      source = ../scripts/darwin/setup_cloud_symlinks.sh;
      executable = true;
    };
  };

}
