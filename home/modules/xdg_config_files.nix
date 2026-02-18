{ lib, osConfig ? {}, ... }:

let
  clean_source = { src, exclude_names ? [] }:
    let
      excluded_names = [
        ".DS_Store"
        ".pytest_cache"
        ".ruff_cache"
        ".venv"
        "__pycache__"
        "CACHEDIR.TAG"
      ] ++ exclude_names;
    in
      lib.cleanSourceWith {
        inherit src;
        filter = path: type:
          lib.cleanSourceFilter path type
          && !(lib.elem (builtins.baseNameOf path) excluded_names);
      };

  terminal_configs = import ./xdg_terminal_files.nix;

  editor_configs = import ./xdg_editor_files.nix;

  nushell_configs = import ./xdg_nushell_files.nix;

  yazi_configs = import ./xdg_yazi_files.nix;

  desktop_configs = import ./xdg_desktop_files.nix;

  simple_config_files =
    terminal_configs
    ++ editor_configs
    ++ nushell_configs
    ++ yazi_configs
    ++ desktop_configs;

  simple_config_attrs = builtins.listToAttrs (map (entry: {
    name = entry.target;
    value = { source = entry.source; };
  }) simple_config_files);

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
