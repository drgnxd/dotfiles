{
  # Single source of nixpkgs config (allowUnfree); pkgs is injected via specialArgs.
  mkPkgs =
    nixpkgs: opencode: system:
    import nixpkgs {
      inherit system;
      config.allowUnfree = true;
      overlays = [
        (_: prev: {
          # Determinate Nix requires sandboxing; the package's version hook
          # misdetects the valid `claude --version` output under that sandbox.
          claude-code = prev.claude-code.overrideAttrs (_: {
            __noChroot = false;
            doInstallCheck = false;
          });
          opencode =
            if system == "aarch64-darwin" then
              prev.stdenvNoCC.mkDerivation {
                pname = "opencode";
                version = "1.18.9";
                src = prev.fetchurl {
                  url = "https://github.com/anomalyco/opencode/releases/download/v1.18.9/opencode-darwin-arm64.zip";
                  hash = "sha256-b5mLfau5QluzSP0NiK/rkqFEIncSMc7JsPQ3S5Rzl+Y=";
                };
                nativeBuildInputs = [ prev.unzip ];
                unpackPhase = "unzip $src";
                installPhase = "install -Dm755 opencode $out/bin/opencode";
                meta = prev.opencode.meta;
              }
            else
              opencode.packages.${system}.opencode;
        })
      ];
    };
}
