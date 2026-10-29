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
      # nixpkgs' pre-commit test suite needs a relaxed Darwin sandbox, which
      # an untrusted Nix user cannot grant, so an uncached build breaks the
      # devshell and every git hook. The tests add nothing to a hook runner.
      package =
        if p.stdenv.hostPlatform.isDarwin then
          p.pre-commit.overridePythonAttrs (_: {
            doCheck = false;
            doInstallCheck = false;
            dontUsePytestCheck = true;
            nativeCheckInputs = [ ];
          })
        else
          p.pre-commit;
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
        commit-message = {
          enable = true;
          name = "commit message";
          entry = "${p.bash}/bin/bash ${../scripts/validate_commit_message.sh}";
          pass_filenames = true;
          stages = [ "commit-msg" ];
        };
        block-local-nix = {
          enable = true;
          name = "block local Nix files";
          entry = "${p.bash}/bin/bash ${../scripts/block_flake_local_nix.sh}";
          pass_filenames = false;
        };
        public-boundary = {
          enable = true;
          name = "check public repository boundary";
          entry = "${p.bash}/bin/bash ${../scripts/check-public-boundary.sh}";
          pass_filenames = false;
        };
        private-terms-files = {
          enable = true;
          name = "check tracked files for private terms";
          entry = "${p.bash}/bin/bash ${../scripts/check-private-terms.sh} files";
          pass_filenames = false;
        };
        private-terms-message = {
          enable = true;
          name = "check commit message for private terms";
          entry = "${p.bash}/bin/bash ${../scripts/check-private-terms.sh} message";
          pass_filenames = true;
          stages = [ "commit-msg" ];
        };
        private-terms-push = {
          enable = true;
          name = "check pushed commits for private terms";
          entry = "${p.bash}/bin/bash ${../scripts/check-private-terms.sh} push";
          pass_filenames = false;
          always_run = true;
          stages = [ "pre-push" ];
        };
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
    agent-inbox-wrapper-tests = import ../home/tests/agent-inbox-wrapper.nix { pkgs = p; };
    opencode-tool-sync-tests =
      p.runCommand "check-opencode-tool-sync" { nativeBuildInputs = [ p.bash ]; }
        ''
          cp ${../home/modules/activation/sync_opencode_tools.sh} sync_opencode_tools.sh
          cp ${../home/tests/opencode-tool-sync.sh} test-opencode-tool-sync.sh
          chmod u+w sync_opencode_tools.sh test-opencode-tool-sync.sh
          mkdir -p home/modules/activation home/tests
          cp sync_opencode_tools.sh home/modules/activation/sync_opencode_tools.sh
          cp test-opencode-tool-sync.sh home/tests/opencode-tool-sync.sh
          bash home/tests/opencode-tool-sync.sh
          touch $out
        '';
    worktree-guard-tests =
      p.runCommand "check-worktree-guard"
        {
          nativeBuildInputs = [
            (p.python3.withPackages (ps: [ ps.pytest ]))
            p.git
          ];
        }
        ''
          cp -r ${../xdg/config/opencode/skills/git-workflow/scripts} scripts
          chmod -R u+w scripts
          export HOME="$TMPDIR/home"
          mkdir -p "$HOME"
          cd scripts
          # The suite pins PATH to system directories for its git fixtures;
          # point them at the sandbox git instead of editing the tests.
          cat > conftest.py <<'PY'
          import os
          import shutil
          import subprocess

          import pytest

          import test_worktree_guard as suite


          @pytest.fixture(autouse=True)
          def sandbox_git(monkeypatch):
              git = shutil.which("git")

              def sh(cwd, *args):
                  env = {**suite.GIT_ENV, "PATH": os.environ["PATH"]}
                  subprocess.run([git, *args], cwd=cwd, check=True, capture_output=True, env=env)

              monkeypatch.setattr(suite, "sh", sh)
          PY
          python -m pytest -q -p no:cacheprovider test_worktree_guard.py
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
