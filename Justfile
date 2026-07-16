set shell := ["bash", "-cu"]

default:
  @just --list

# Format the whole tree with treefmt
fmt:
  nix fmt

# Check whole-tree formatting
fmt-check:
  nix fmt -- --fail-on-change

# Run all CI checks locally
check:
  nix flake check

# Build Darwin configuration (no activation)
build-darwin:
  nix build path:.#packages.aarch64-darwin.default --no-link

# Apply Darwin configuration
switch-darwin:
  sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# Build Linux home-manager configuration
build-linux:
  nix build path:.#packages.x86_64-linux.default --no-link

# Apply Linux home-manager configuration
switch-linux:
  home-manager switch --flake path:.

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
  nix run nixpkgs#deadnix -- --fail .

# Rekey agenix secrets
rekey:
  cd secrets && nix run github:ryantm/agenix -- -r

# Show OpenCode subscription usage (pinned npm CLI)
usage:
  bunx opencode-usage@0.5.15

# Report the read-only macOS security posture
security-audit *args:
  scripts/security/audit_darwin.sh {{args}}
