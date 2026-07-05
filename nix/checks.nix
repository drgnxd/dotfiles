{
  nixpkgs,
  self,
  forAllSystems,
  treefmtEval,
}:

forAllSystems (
  sys:
  let
    inherit (nixpkgs) lib;
    p = nixpkgs.legacyPackages.${sys};
  in
  {
    formatting = (treefmtEval sys).config.build.check self;
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
