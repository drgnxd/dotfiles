{ lib, ... }:

let
  clean_source = { src, exclude_names ? [] }:
    let
      default_excludes = [
        ".DS_Store"
        ".pytest_cache"
        ".ruff_cache"
        ".venv"
        "__pycache__"
        "CACHEDIR.TAG"
      ];
    in
      lib.cleanSourceWith {
        inherit src;
        filter = path: _type:
          let
            path_str = toString path;
            name = builtins.baseNameOf path;
          in
            !(lib.elem name (default_excludes ++ exclude_names))
            && !lib.hasInfix "/.pytest_cache/" path_str
            && !lib.hasInfix "/.ruff_cache/" path_str
            && !lib.hasInfix "/.venv/" path_str
            && !lib.hasInfix "/__pycache__/" path_str;
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

  use_npmrc_secret = builtins.pathExists ../../secrets/npmrc.age;
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
