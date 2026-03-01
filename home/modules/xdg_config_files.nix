{
  lib,
  osConfig ? { },
  ...
}:

let
  # Helper: map a relative path string to an xdg.configFile entry
  mkConfigFile = path: {
    name = path;
    value = {
      source = ../../dot_config/${path};
    };
  };

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

  desktop_configs = import ./xdg_desktop_files.nix;

  all_config_paths = desktop_configs;

  simple_config_attrs = builtins.listToAttrs (map mkConfigFile all_config_paths);

  taskwarrior_source = clean_source { src = ../../dot_config/taskwarrior; };

  use_npmrc_secret = lib.hasAttrByPath [ "age" "secrets" "npmrc" ] osConfig;
  has_npmrc_file = builtins.pathExists ../../dot_config/npm/npmrc;
in
{
  xdg.configFile = lib.mkMerge [
    simple_config_attrs

    {
      "alacritty/toggle_blur.sh" = {
        source = ../../dot_config/alacritty/executable_toggle_blur.sh;
        executable = true;
      };

      "taskwarrior".source = taskwarrior_source;
    }

    (lib.optionalAttrs (!use_npmrc_secret && has_npmrc_file) {
      "npm/npmrc".source = ../../dot_config/npm/npmrc;
    })
  ];
}
