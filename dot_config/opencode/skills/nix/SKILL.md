---
name: nix
description: Use when editing Nix flakes or deployment workflows.
---

# Nix Preferences

- `path:.` copies untracked and ignored files, possibly secrets, into the
  world-readable Nix store. Use it only when local evaluation must include them;
  otherwise follow the repository's documented evaluation and deployment
  workflow.
- Resolve configuration attributes dynamically when the repository supports
  multiple users or hosts; do not invent target names.
