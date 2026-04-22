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
      linuxHostname = "linux-dev";
      darwin_pkgs = import nixpkgs {
        system = "aarch64-darwin";
        config.allowUnfree = true;
      };
      linux_pkgs = import nixpkgs {
        system = "x86_64-linux";
        config.allowUnfree = true;
      };
      supportedSystems = [
        "aarch64-darwin"
        "x86_64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      darwinConfigurations.${hostname} = nix-darwin.lib.darwinSystem {
        inherit system;
        specialArgs = {
          inherit inputs user hostname;
          pkgs = darwin_pkgs;
        };
        modules = [
          ./hosts/macbook
          home-manager.darwinModules.home-manager
          agenix.darwinModules.default
          {
            nixpkgs.hostPlatform = system;
            nixpkgs.config.allowUnfree = true;
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.users.${user} = import ./home;
            home-manager.extraSpecialArgs = {
              inherit
                inputs
                user
                hostname
                linuxHostname
                ;
              pkgs = darwin_pkgs;
            };
          }
        ];
      };

      homeConfigurations."${user}@${linuxHostname}" = home-manager.lib.homeManagerConfiguration {
        pkgs = linux_pkgs;
        modules = [
          ./home
        ];
        extraSpecialArgs = {
          inherit
            inputs
            user
            hostname
            linuxHostname
            ;
          pkgs = linux_pkgs;
        };
      };

      formatter = forAllSystems (sys: nixpkgs.legacyPackages.${sys}.nixfmt-rfc-style);

      devShells = forAllSystems (
        sys:
        let
          p = nixpkgs.legacyPackages.${sys};
        in
        {
          default = p.mkShell {
            packages = with p; [
              nixfmt-rfc-style
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
          formatting = p.runCommand "check-formatting" { nativeBuildInputs = [ p.nixfmt-rfc-style ]; } ''
            cd ${self}
            find . -name '*.nix' -exec nixfmt-rfc-style --check {} +
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
