{
  nixpkgs,
  forAllSystems,
}:

forAllSystems (
  sys:
  let
    p = nixpkgs.legacyPackages.${sys};
  in
  {
    default = p.mkShell {
      packages = with p; [
        nixfmt
        statix
        deadnix
      ];
    };
  }
)
