{
  nixpkgs,
  forAllSystems,
  treefmtEval,
}:

forAllSystems (
  sys:
  let
    p = nixpkgs.legacyPackages.${sys};
    treefmt = (treefmtEval sys).config.build.wrapper;
  in
  {
    default = p.mkShell {
      packages = [
        treefmt
      ]
      ++ (with p; [
        statix
        deadnix
        actionlint
        typos
      ]);
    };
  }
)
