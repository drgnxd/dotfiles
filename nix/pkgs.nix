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
        })
      ];
    };
}
