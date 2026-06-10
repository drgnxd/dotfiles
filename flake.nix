{
  description = "nix-darwin + home-manager configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    nix-darwin.url = "github:nix-darwin/nix-darwin/master";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";

    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

    nixgl.url = "github:nix-community/nixGL";
    nixgl.inputs.nixpkgs.follows = "nixpkgs";

    agenix.url = "github:ryantm/agenix";
    agenix.inputs.darwin.follows = "nix-darwin";
    agenix.inputs.home-manager.follows = "home-manager";
    agenix.inputs.nixpkgs.follows = "nixpkgs";

    nix-hazkey.url = "github:aster-void/nix-hazkey";
    nix-hazkey.inputs.nixpkgs.follows = "nixpkgs";
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
      identity_path = ./local/identity.nix;
      identity =
        if builtins.pathExists identity_path then
          import identity_path
        else
          {
            user = "user";
            hostname = "darwin";
            linux_hostname = "linux";
          };
      preferences_path = ./local/preferences.nix;
      preferences =
        if builtins.pathExists preferences_path then
          import preferences_path
        else
          {
            browserClass = "floorp";
          };
      inherit (identity) user hostname;
      linuxHostname = identity.linux_hostname;
      pkgs_lib = import ./nix/pkgs.nix;
      darwin_pkgs = pkgs_lib.mkPkgs nixpkgs "aarch64-darwin";
      linux_pkgs = pkgs_lib.mkPkgs nixpkgs "x86_64-linux";
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
          ./hosts/darwin
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
                preferences
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
          {
            targets.genericLinux.nixGL.packages = inputs.nixgl.packages;
            targets.genericLinux.nixGL.defaultWrapper = "mesa";
          }
        ];
        extraSpecialArgs = {
          inherit
            inputs
            user
            hostname
            linuxHostname
            preferences
            ;
          pkgs = linux_pkgs;
        };
      };

      formatter = forAllSystems (sys: nixpkgs.legacyPackages.${sys}.nixfmt);

      devShells = import ./nix/devshells.nix { inherit nixpkgs forAllSystems; };

      apps = import ./nix/apps.nix { inherit nixpkgs forAllSystems; };

      checks = import ./nix/checks.nix { inherit nixpkgs self forAllSystems; };
    };
}
