{ lib }:

let
  solarized_dark = import ../themes/solarized-dark.nix;

  color_names = [
    "base03"
    "base02"
    "base01"
    "base00"
    "base0"
    "base1"
    "base2"
    "base3"
    "yellow"
    "orange"
    "red"
    "magenta"
    "violet"
    "blue"
    "cyan"
    "green"
  ];

  solarized_dark_placeholders = {
    base03 = "#002b36";
    base02 = "#073642";
    base01 = "#586e75";
    base00 = "#657b83";
    base0 = "#839496";
    base1 = "#93a1a1";
    base2 = "#eee8d5";
    base3 = "#fdf6e3";
    yellow = "#b58900";
    orange = "#cb4b16";
    red = "#dc322f";
    magenta = "#d33682";
    violet = "#6c71c4";
    blue = "#268bd2";
    cyan = "#2aa198";
    green = "#859900";
  };

  without_hash = color: lib.removePrefix "#" color;

  from_hashed = map (name: solarized_dark_placeholders.${name}) color_names;
  to_hashed = map (name: solarized_dark.${name}) color_names;

  from_bare = map without_hash from_hashed;
  to_bare = map without_hash to_hashed;
in
{
  templatePath,
  includeBareHex ? false,
}:
let
  template = builtins.readFile templatePath;
  from = from_hashed ++ lib.optionals includeBareHex from_bare;
  to = to_hashed ++ lib.optionals includeBareHex to_bare;
in
lib.replaceStrings from to template
