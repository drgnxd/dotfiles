{
  user,
  hostname,
  linuxHostname,
  ...
}:

let
  languages_toml = builtins.readFile ../../dot_config/helix/languages.toml;
  languages_toml_substituted =
    builtins.replaceStrings
      [ "darwinConfigurations.darwin" ''homeConfigurations."user@linux"'' ]
      [ "darwinConfigurations.${hostname}" ''homeConfigurations."${user}@${linuxHostname}"'' ]
      languages_toml;
in
{
  xdg.configFile = {
    "helix/config.toml".source = ../../dot_config/helix/config.toml;
    "helix/languages.toml".text = languages_toml_substituted;
    "helix/themes/solarized_dark_transparent.toml".source =
      ../../dot_config/helix/themes/solarized_dark_transparent.toml;
  };
}
