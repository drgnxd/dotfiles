{
  description = "nix-darwin + home-manager configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    nix-darwin.url = "github:nix-darwin/nix-darwin/master";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";

    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

    agenix.url = "github:ryantm/agenix";
    agenix.inputs.darwin.follows = "nix-darwin";
    agenix.inputs.home-manager.follows = "home-manager";
    agenix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      nix-darwin,
      home-manager,
      agenix,
      ...
    }:
    let
      system = "aarch64-darwin";
      user = "drgnxd";
      hostname = "macbook";
      supportedSystems = [
        "aarch64-darwin"
        "x86_64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      darwinConfigurations.${hostname} = nix-darwin.lib.darwinSystem {
        inherit system;
        specialArgs = { inherit inputs user hostname; };
        modules = [
          ./hosts/macbook
          home-manager.darwinModules.home-manager
          agenix.darwinModules.default
          {
            nixpkgs.hostPlatform = system;
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.users.${user} = import ./home;
            home-manager.extraSpecialArgs = { inherit inputs user; };
          }
        ];
      };

      formatter = forAllSystems (sys: nixpkgs.legacyPackages.${sys}.nixfmt);

      devShells = forAllSystems (
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
      );

      checks = forAllSystems (
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
      );
    };
}
