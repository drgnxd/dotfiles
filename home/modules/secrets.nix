{
  config,
  lib,
  agenixIdentityFile ? null,
  ...
}:

let
  default_identity_file = "${config.home.homeDirectory}/.ssh/id_ed25519";
  configured_identity_file =
    if agenixIdentityFile == null then default_identity_file else agenixIdentityFile;
  identity_file =
    if lib.hasPrefix "~/" configured_identity_file then
      "${config.home.homeDirectory}/${lib.removePrefix "~/" configured_identity_file}"
    else
      configured_identity_file;
in
{
  age.identityPaths = [ identity_file ];

  age.secrets = lib.mkMerge [
    (lib.optionalAttrs (builtins.pathExists ../../secrets/gh-hosts.age) {
      gh-hosts = {
        file = ../../secrets/gh-hosts.age;
        path = "${config.xdg.configHome}/gh/hosts.yml";
        mode = "0400";
      };
    })
    (lib.optionalAttrs (builtins.pathExists ../../secrets/npmrc.age) {
      npmrc = {
        file = ../../secrets/npmrc.age;
        path = "${config.xdg.configHome}/npm/npmrc";
        mode = "0400";
      };
    })
    (lib.optionalAttrs (builtins.pathExists ../../secrets/git-config-local.age) {
      git-config-local = {
        file = ../../secrets/git-config-local.age;
        path = "${config.xdg.configHome}/git/config.local";
        mode = "0400";
      };
    })
  ];
}
