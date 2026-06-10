{
  nixpkgs,
  self,
  forAllSystems,
}:

forAllSystems (
  sys:
  let
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
)
