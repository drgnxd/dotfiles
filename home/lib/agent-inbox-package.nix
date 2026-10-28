{
  lib,
  pkgs,
  source,
}:

let
  sourcePath = builtins.path {
    name = "agent-inbox-source";
    path = source;
    filter =
      path: type:
      let
        relative = lib.removePrefix "${source}/" path;
        parts = lib.splitString "/" relative;
      in
      !(lib.any (
        part:
        builtins.elem part [
          ".git"
          "target"
          ".direnv"
          ".idea"
          ".vscode"
          "node_modules"
          ".cargo"
          ".cache"
        ]
      ) parts)
      && (
        relative == ""
        || relative == "Cargo.toml"
        || relative == "Cargo.lock"
        || relative == "build.rs"
        || (lib.hasPrefix "src/" relative && (type == "directory" || lib.hasSuffix ".rs" relative))
        || relative == "src"
      )
      && type != "symlink";
  };
  sourceAvailable =
    builtins.pathExists "${source}/Cargo.toml" && builtins.pathExists "${source}/Cargo.lock";
in
if sourceAvailable then
  let
    manifest = builtins.fromTOML (builtins.readFile "${source}/Cargo.toml");
  in
  pkgs.rustPlatform.buildRustPackage {
    pname = "agent-inbox";
    version =
      if manifest ? package && manifest.package ? version then manifest.package.version else "0.1.0";
    src = sourcePath;
    cargoLock.lockFile = "${sourcePath}/Cargo.lock";
    doCheck = false;
  }
else
  pkgs.writeShellScriptBin "agent-inbox" ''
    printf '%s\n' 'agent-inbox is unavailable; clone the optional helper repository under ~/repos/agent-inbox' >&2
    exit 127
  ''
