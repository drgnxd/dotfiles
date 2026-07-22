{
  lib,
  pkgs,
  ...
}:

{
  # Home Manager generates ~/.ssh/config. Keep agenix secrets to identity keys,
  # not a full config, so this managed config remains the source of truth.
  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    settings = {
      "*" = {
        AddKeysToAgent = "yes";
        Compression = false;
        ControlMaster = "auto";
        ControlPath = "~/.ssh/cm-%r@%h:%p";
        ControlPersist = "10m";
        HashKnownHosts = true;
        ServerAliveInterval = 60;
        UseKeychain = lib.mkIf pkgs.stdenv.isDarwin "yes";
      };
      "github.com" = {
        HostName = "github.com";
        IdentityFile = "none";
        User = "git";
      };
    };
  };
}
