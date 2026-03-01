{
  lib,
  osConfig ? { },
  ...
}:

let
  clean_source =
    {
      src,
      exclude_names ? [ ],
    }:
    let
      excluded_names = [
        ".DS_Store"
        ".pytest_cache"
        ".ruff_cache"
        ".venv"
        "__pycache__"
        "CACHEDIR.TAG"
      ]
      ++ exclude_names;
    in
    lib.cleanSourceWith {
      inherit src;
      filter =
        path: type:
        lib.cleanSourceFilter path type && !(lib.elem (builtins.baseNameOf path) excluded_names);
    };

  taskwarrior_source = clean_source { src = ../../dot_config/taskwarrior; };

  use_npmrc_secret = lib.hasAttrByPath [ "age" "secrets" "npmrc" ] osConfig;
  has_npmrc_file = builtins.pathExists ../../dot_config/npm/npmrc;
in
{
  xdg.configFile = lib.mkMerge [
    { "taskwarrior".source = taskwarrior_source; }

    (lib.optionalAttrs (!use_npmrc_secret && has_npmrc_file) {
      "npm/npmrc".source = ../../dot_config/npm/npmrc;
    })
  ];
}
