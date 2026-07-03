{
  # Single source of nixpkgs config (allowUnfree); pkgs is injected via specialArgs.
  mkPkgs =
    nixpkgs: system:
    import nixpkgs {
      inherit system;
      config.allowUnfree = true;
    };
}
