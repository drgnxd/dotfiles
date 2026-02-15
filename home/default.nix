{ config, lib, pkgs, ... }:

let
  packages = import ./packages.nix { inherit pkgs lib; };
in
{
  home.username = "drgnxd";
  home.homeDirectory = "/Users/drgnxd";
  home.stateVersion = "24.11";

  programs.home-manager.enable = true;

  imports = [
    ./modules/activation.nix
    ./modules/xdg_config_files.nix
  ];

  xdg.enable = true;

  targets.darwin.linkApps.enable = true;

  home.sessionVariables = {
    DOTFILES_DIR = "${config.home.homeDirectory}/.config/nix-config";
    DOTFILES_FLAKE_TARGET = "macbook";
  };

  home.packages = packages.packages;

  warnings = lib.optional (packages.missing != [])
    ("Missing nix packages: " + (lib.concatStringsSep ", " packages.missing));

  home.file = {
    ".ollama".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/ollama";
    ".Scilab".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/scilab";
    ".hammerspoon".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/hammerspoon";

    ".local/bin/cloud-symlinks" = {
      source = ../scripts/darwin/setup_cloud_symlinks.sh;
      executable = true;
    };
  };

}
