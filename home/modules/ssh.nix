{
  config,
  lib,
  pkgs,
  ...
}:

{
  programs.ssh = {
    enable = true;
    compression = false;
    controlMaster = "auto";
    controlPath = "~/.ssh/cm-%r@%h:%p";
    controlPersist = "10m";
    serverAliveInterval = 60;
    hashKnownHosts = true;
    matchBlocks = {
      "github.com" = {
        hostname = "github.com";
        user = "git";
        identitiesOnly = true;
      };
      "*" = {
        extraOptions = {
          AddKeysToAgent = "yes";
          UseKeychain = lib.mkIf pkgs.stdenv.isDarwin "yes";
        };
      };
    };
  };
}
