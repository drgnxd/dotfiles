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
    # marksman is a .NET package that propagates a Darwin sandbox profile to
    # every shell derivation it is an input of, and an untrusted Nix user
    # cannot build such a derivation. Joining it drops the propagation.
    marksman = p.symlinkJoin {
      name = "marksman-${p.marksman.version}";
      paths = [ p.marksman ];
    };
    repo_language_tools = [
      p.bash-language-server
      p.lua-language-server
      marksman
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
      # git-hooks.nix installs .pre-commit-config.yaml into the cwd repository,
      # so only run it when entered from a checkout of this flake.
      shellHook = ''
        if [ -f "$(git rev-parse --show-toplevel 2>/dev/null)/nix/devshells.nix" ]; then
          ${pre-commit-check.shellHook}
        fi
      '';
    };
  }
)
