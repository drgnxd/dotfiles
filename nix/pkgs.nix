{
  # Single source of nixpkgs config (allowUnfree); pkgs is injected via specialArgs.
  mkPkgs =
    nixpkgs: system:
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

          proton-drive-cli =
            let
              version = "0.7.0";
              source =
                {
                  aarch64-darwin = {
                    url = "https://proton.me/download/drive/cli/0.7.0/darwin-arm64/proton-drive";
                    sha512 = "7b5ff4ff59e7d164a6298a6239b8d2f7b1ffb1eba94e53de93a637ebb10c62d100632c28eac144e722755c28454fe9337b9cc3f5d09c996e17eed9a07992d2ed";
                  };
                  x86_64-linux = {
                    url = "https://proton.me/download/drive/cli/0.7.0/linux-x64/proton-drive";
                    sha512 = "5a5affcbec04ea926a32d10e236c1342227f1b6d416cb797f88f943b2c4f1dcf53b5897a115f1c1aa9ce8ce92fd637e1c50bd223b04866577681f0584eccdbc6";
                  };
                }
                .${prev.stdenv.hostPlatform.system}
                  or (throw "Unsupported platform for proton-drive-cli: ${prev.stdenv.hostPlatform.system}");
            in
            prev.stdenvNoCC.mkDerivation {
              pname = "proton-drive-cli";
              inherit version;
              src = prev.fetchurl source;
              dontUnpack = true;

              installPhase = ''
                install -Dm755 "$src" "$out/bin/proton-drive"
              '';
            };
        })
      ];
    };
}
