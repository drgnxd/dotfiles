# Plaintext npmrc fallback for both platforms when no agenix npmrc secret exists.
{
  config,
  lib,
  ...
}:

let
  use_npmrc_secret = lib.hasAttrByPath [ "age" "secrets" "npmrc" ] config;
  has_npmrc_file = builtins.pathExists ../../xdg/config/npm/npmrc;
in
{
  xdg.configFile = lib.mkMerge [
    (lib.optionalAttrs (!use_npmrc_secret && has_npmrc_file) {
      "npm/npmrc".source = ../../xdg/config/npm/npmrc;
    })
  ];
}
