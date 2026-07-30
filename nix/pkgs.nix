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
                nativeBuildInputs = [
                  prev.unzip
                  prev.rcodesign
                ];
                unpackPhase = "unzip $src";
                installPhase = "install -Dm755 opencode $out/bin/opencode";
                # The upstream release zip already ships an invalid ad-hoc signature
                # (verified: `codesign --verify` fails straight out of the archive,
                # before any Nix processing). This Bun binary needs JIT memory to
                # start its JavaScriptCore-based TUI, so re-sign with JIT
                # entitlements via rcodesign (pure Nix, no sandbox escape needed)
                # or it hangs silently on launch.
                postFixup = ''
                  cat > entitlements.plist <<'PLIST'
                  <?xml version="1.0" encoding="UTF-8"?>
                  <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                  <plist version="1.0">
                  <dict>
                    <key>com.apple.security.cs.allow-jit</key>
                    <true/>
                    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
                    <true/>
                    <key>com.apple.security.cs.disable-library-validation</key>
                    <true/>
                  </dict>
                  </plist>
                  PLIST
                  rcodesign sign --entitlements-xml-file entitlements.plist "$out/bin/opencode"
                '';
                meta = prev.opencode.meta;
              }
            else
              opencode.packages.${system}.opencode;
        })
      ];
    };
}
