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
    repo_language_tools = [
      p.bash-language-server
      p.lua-language-server
      p.marksman
      p.nodejs
      p.nushell
      p.pyright
      p.ruff
      p.shfmt
      p.taplo
    ];
  in
  {
    default = p.mkShell {
      packages = [
        treefmt
      ]
      ++ repo_language_tools
      ++ pre-commit-check.enabledPackages;
      inherit (pre-commit-check) shellHook;
    };
  }
)
