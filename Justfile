set shell := ["bash", "-cu"]

default:
  @just --list

# Format all Nix files
fmt:
  nix fmt

# Run all CI checks locally
check:
  nix flake check

# Build Darwin configuration (no activation)
build-darwin:
  nix build .#darwinConfigurations.$(nix eval --raw --apply '(x: builtins.head (builtins.attrNames x))' .#darwinConfigurations).system --no-link

# Apply Darwin configuration
switch-darwin:
  darwin-rebuild switch --flake .

# Build Linux home-manager configuration
build-linux:
  nix build .#homeConfigurations.$(nix eval --raw --apply '(x: builtins.head (builtins.attrNames x))' .#homeConfigurations).activationPackage --no-link

# Apply Linux home-manager configuration
switch-linux:
  home-manager switch --flake .

# Update all flake inputs
update:
  nix flake update

# Update a single input
update-one input:
  nix flake update {{input}}

# Run shfmt on all shell scripts
fmt-shell:
  git ls-files -z '*.sh' | xargs -0 shfmt -w

# Run statix lints
lint:
  nix run nixpkgs#statix -- check .

# Show dead Nix code
dead:
  nix run nixpkgs#deadnix -- .

# Rekey agenix secrets
rekey:
  cd secrets && nix run github:ryantm/agenix -- -r
