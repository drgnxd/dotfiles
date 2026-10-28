{
  pkgs,
  lib,
}:

let
  package = import ../lib/agent-inbox-package.nix;
  absent = package {
    inherit pkgs lib;
    source = "${toString ./.}/absent-agent-inbox-source";
  };
  present = package {
    inherit pkgs lib;
    source = toString ./agent-inbox-fixture;
  };
in
assert absent.name == "agent-inbox";
assert
  builtins.attrNames (builtins.readDir (toString present.src)) == [
    "Cargo.lock"
    "Cargo.toml"
    "src"
  ];
assert builtins.attrNames (builtins.readDir "${present.src}/src") == [ "main.rs" ];
{
  inherit absent present;
}
