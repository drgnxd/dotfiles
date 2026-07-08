# treefmt-nix module: single formatting entry point (nix fmt) and check derivation.
_: {
  projectRootFile = "flake.nix";
  programs.nixfmt.enable = true; # same nixfmt as before (RFC style from unstable)
  programs.shfmt.enable = true; # no indent flag => upstream defaults, matches old CI
  programs.taplo.enable = true;
  settings.formatter.shfmt.includes = [ "scripts/linux/hypr-*" ];
  settings.global.excludes = [
    "*.age"
    "*.lock"
    "*.plist"
    "dot_config/opencode/node_modules/**"
    "result/**"
  ];
}
