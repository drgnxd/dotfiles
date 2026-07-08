{
  nixpkgs,
  forAllSystems,
  treefmtEval,
  checks,
}:

forAllSystems (
  sys:
  let
    p = nixpkgs.legacyPackages.${sys};
    pre-commit-check = checks.${sys}.pre-commit-check;
    treefmt = (treefmtEval sys).config.build.wrapper;
  in
  {
    default = p.mkShell {
      packages = [
        treefmt
      ]
      ++ pre-commit-check.enabledPackages;
      inherit (pre-commit-check) shellHook;
    };
  }
)
