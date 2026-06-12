{
  nixpkgs,
  self,
  forAllSystems,
}:

forAllSystems (
  sys:
  let
    lib = nixpkgs.lib;
    p = nixpkgs.legacyPackages.${sys};
  in
  {
    formatting = p.runCommand "check-formatting" { nativeBuildInputs = [ p.nixfmt ]; } ''
      cd ${self}
      find . -name '*.nix' -exec nixfmt --check {} +
      touch $out
    '';
    lint-statix = p.runCommand "check-statix" { nativeBuildInputs = [ p.statix ]; } ''
      cd ${self}
      statix check .
      touch $out
    '';
    lint-deadnix = p.runCommand "check-deadnix" { nativeBuildInputs = [ p.deadnix ]; } ''
      cd ${self}
      deadnix --fail .
      touch $out
    '';
  }
  // lib.optionalAttrs (sys == "aarch64-darwin") {
    darwin-system = self.packages.aarch64-darwin.default;
  }
  // lib.optionalAttrs (sys == "x86_64-linux") {
    home-activation = self.packages.x86_64-linux.default;
  }
)
