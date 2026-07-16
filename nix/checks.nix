{
  nixpkgs,
  self,
  forAllSystems,
  treefmtEval,
  git-hooks,
}:

forAllSystems (
  sys:
  let
    inherit (nixpkgs) lib;
    p = nixpkgs.legacyPackages.${sys};
    src = lib.cleanSource self.outPath;
    treefmt = (treefmtEval sys).config.build.wrapper;
  in
  {
    formatting = (treefmtEval sys).config.build.check src;
    pre-commit-check = git-hooks.lib.${sys}.run {
      inherit src;
      hooks = {
        treefmt = {
          enable = true;
          package = treefmt;
        };
        statix.enable = true;
        deadnix.enable = true;
        shellcheck.enable = true;
        actionlint.enable = true;
        typos.enable = true;
      };
    };
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
    agent-memory =
      p.runCommand "check-agent-memory"
        {
          nativeBuildInputs = [
            p.git
            p.python3
          ];
        }
        ''
          cd ${self}
          python3 -m unittest discover -s tests -p 'test_agent_memory.py'
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
