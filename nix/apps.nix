{
  nixpkgs,
  forAllSystems,
}:

forAllSystems (
  sys:
  let
    p = nixpkgs.legacyPackages.${sys};
    mkApp = name: script: {
      type = "app";
      program = "${
        p.writeShellApplication {
          inherit name;
          runtimeInputs = [
            p.git
            p.nix
          ];
          text = script;
        }
      }/bin/${name}";
    };
  in
  {
    bootstrap-darwin = mkApp "bootstrap-darwin" ''
      set -euo pipefail
      [ -f local/identity.nix ] || {
        echo "ERROR: create local/identity.nix first (see local/identity.nix.example)" >&2
        exit 1
      }
      sudo nix run nix-darwin -- switch --flake path:.
    '';
    bootstrap-linux = mkApp "bootstrap-linux" ''
      set -euo pipefail
      [ -f local/identity.nix ] || {
        echo "ERROR: create local/identity.nix first (see local/identity.nix.example)" >&2
        exit 1
      }
      USER_HOST="$(whoami)@$(hostname)"
      nix run home-manager/master -- switch --flake "path:.#$USER_HOST"
    '';
    rekey-secrets = mkApp "rekey-secrets" ''
      set -euo pipefail
      cd secrets
      nix run github:ryantm/agenix -- -r
    '';
  }
)
